"""Continuation regressions: isolated SQLite, ephemeral credentials, no external services."""
import importlib.util
import io
import json
import os
from contextlib import ExitStack, redirect_stdout
from datetime import date, datetime, timedelta
from pathlib import Path
import secrets
import string
import tempfile
import unittest
from unittest.mock import patch

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from flask import Flask
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError

# Importing the application must not read a developer's private .env file.
with patch('dotenv.load_dotenv', return_value=False):
    import app as application_package
    from app.controllers.orders import orders_controller
    from app.controllers.public_controller import public_bp
    from app.controllers.review_controller import review_bp
    from app.controllers.settings_controller import settings_bp
    from app.controllers.tracking_controller import tracking_bp
    from app.extensions import bcrypt, db, jwt
    from app.models.gallery import GalleryItem
    from app.models.order_tracking import OrderStatusHistory
    from app.models.orders import Order, VALID_STATUSES, generate_order_reference
    from app.models.page import Page
    from app.models.rbac import Permission, Role, User
    from app.models.review import Review
    from app.models.settings import SiteSettings


BACKEND = Path(__file__).resolve().parents[1]
TARGET_EMAIL = 'cinderellacakes2@gmail.com'
LEGACY_EMAIL = 'admin@cinderellacakes.com'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SQLiteAppCase(unittest.TestCase):
    def setUp(self):
        self.uploads = tempfile.TemporaryDirectory()
        self.app = Flask('regression_' + secrets.token_hex(6), static_folder=None)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SECRET_KEY=secrets.token_urlsafe(48),
            JWT_SECRET_KEY=secrets.token_urlsafe(48),
            BCRYPT_LOG_ROUNDS=4,
            UPLOAD_FOLDER=self.uploads.name,
            MAIL_ENABLED=False,
        )
        db.init_app(self.app)
        bcrypt.init_app(self.app)
        jwt.init_app(self.app)
        for blueprint in (orders_controller.orders, tracking_bp, review_bp, public_bp, settings_bp):
            self.app.register_blueprint(blueprint)
        self.context = self.app.app_context()
        self.context.push()
        self.assertEqual(db.engine.url.render_as_string(), 'sqlite:///:memory:')
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()
        self.uploads.cleanup()

    def token_headers(self, permissions=(), roles=()):
        token = create_access_token(
            identity=secrets.token_hex(8),
            additional_claims={'permissions': list(permissions), 'roles': list(roles)},
        )
        return {'Authorization': f'Bearer {token}'}

    def make_order(self, phone=None, status='new'):
        phone = phone or '078' + ''.join(secrets.choice(string.digits) for _ in range(7))
        order = Order(
            full_name='Regression Customer', phone_number=phone,
            event_type='birthday', event_date=date.today() + timedelta(days=30),
            flavor='vanilla', cake_size='2kg', delivery_type='delivery',
            delivery_address='Private delivery address',
            special_instructions='Private order instructions', inspiration_image='private-photo.jpg',
        )
        order.status = status
        db.session.add(order)
        db.session.flush()
        db.session.add(OrderStatusHistory(order_id=order.id, status=status, note='Public status note.'))
        db.session.commit()
        return order

    def database_snapshot(self):
        return {
            table.name: [dict(row) for row in db.session.execute(
                sa.select(table).order_by(*table.primary_key.columns)
            ).mappings()]
            for table in db.metadata.sorted_tables
        }


class SeedAccountTests(SQLiteAppCase):
    def setUp(self):
        super().setUp()
        # seed.py's module-level app is replaced before import, so no real engine is created.
        with patch.object(application_package, 'create_app', return_value=self.app):
            self.seed_module = load_module('isolated_seed', BACKEND / 'seed.py')

    def add_user(self, email, role_name='super_admin'):
        role = None
        if role_name:
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name, description='Retained role')
                db.session.add(role)
        password = secrets.token_urlsafe(24)
        user = User(email=email, role=role, first_name='Existing', last_name='Owner', is_active=False)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user, password

    def assert_preserved_account(self, email, role_name='super_admin'):
        user, password = self.add_user(email, role_name)
        permission = Permission(name='content_read', description='Retained permission')
        user.role.permissions = [permission]
        settings = SiteSettings(
            contact_email='previous@example.invalid', contact_phone='Retained phone',
            address='Retained address', site_name='Retained bakery name',
            primary_color='#8B3FA0', secondary_color='#2FBFC0', logo_url='retained-logo.png',
        )
        extra_settings = SiteSettings(contact_email='older@example.invalid')
        page = Page(slug='retained-page', title='Keep this content', is_published=True)
        db.session.add_all([settings, extra_settings, page])
        db.session.commit()
        old_user = dict(user.to_dict())
        old_hash = user.password_hash
        old_role_id = user.role_id
        old_settings = dict(settings.to_dict())
        old_page = dict(page.to_dict())
        with patch.dict(os.environ, {'ADMIN_INITIAL_PASSWORD': secrets.token_urlsafe(24)}):
            with patch.object(User, 'set_password', side_effect=AssertionError('Existing hash must not change')):
                self.seed_module._seed_admin_settings()
                self.seed_module._seed_admin_settings()
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(user.to_dict(), {**old_user, 'email': TARGET_EMAIL})
        self.assertEqual(user.password_hash, old_hash)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.role_id, old_role_id)
        self.assertEqual([p.name for p in user.role.permissions], ['content_read'])
        self.assertEqual(page.to_dict(), old_page)
        for key, value in old_settings.items():
            if key not in ('contact_email', 'updated_at'):
                self.assertEqual(settings.to_dict()[key], value)
        self.assertTrue(all(row.contact_email == TARGET_EMAIL for row in SiteSettings.query.all()))
        public = self.client.get('/api/public/settings')
        admin = self.client.get('/api/v1/settings/', headers=self.token_headers(roles=['super_admin']))
        self.assertEqual(public.get_json()['contact_email'], TARGET_EMAIL)
        self.assertEqual(admin.get_json()['contact_email'], TARGET_EMAIL)

    def test_already_target_admin_preserves_hash_id_role_and_content(self):
        self.assert_preserved_account(TARGET_EMAIL)

    def test_known_legacy_admin_is_renamed_without_resetting_password(self):
        self.assert_preserved_account(LEGACY_EMAIL)

    def test_unique_other_admin_is_renamed_without_escalating_role(self):
        self.assert_preserved_account('owner@example.invalid', role_name='admin')

    def assert_seed_refuses_without_changes(self, message):
        before = self.database_snapshot()
        with patch.dict(os.environ, {'ADMIN_INITIAL_PASSWORD': secrets.token_urlsafe(24)}):
            with patch.object(self.seed_module, 'seed_gallery_images') as gallery:
                with self.assertRaisesRegex(RuntimeError, message):
                    self.seed_module.seed()
                gallery.assert_not_called()
        self.assertEqual(self.database_snapshot(), before)

    def test_target_and_legacy_collision_is_not_resolved_by_reset_or_competing_account(self):
        self.add_user(LEGACY_EMAIL)
        self.add_user(TARGET_EMAIL)
        self.assert_seed_refuses_without_changes('Ambiguous')

    def test_multiple_other_admins_are_ambiguous(self):
        self.add_user('one@example.invalid', role_name='admin')
        self.add_user('two@example.invalid')
        self.assert_seed_refuses_without_changes('Ambiguous')

    def test_known_legacy_and_another_admin_are_ambiguous(self):
        self.add_user(LEGACY_EMAIL)
        self.add_user('other@example.invalid')
        self.assert_seed_refuses_without_changes('Ambiguous')

    def test_target_and_another_admin_are_ambiguous(self):
        self.add_user(TARGET_EMAIL)
        self.add_user('other@example.invalid')
        self.assert_seed_refuses_without_changes('Ambiguous')

    def test_target_email_non_admin_is_not_silently_promoted(self):
        self.add_user(TARGET_EMAIL, role_name='editor')
        self.assert_seed_refuses_without_changes('non-admin')

    def test_case_variant_email_collision_is_ambiguous_on_sqlite(self):
        self.add_user(TARGET_EMAIL)
        self.add_user(TARGET_EMAIL.upper(), role_name=None)
        self.assert_seed_refuses_without_changes('Ambiguous')

    def test_unrelated_non_admin_does_not_authorize_bootstrapping(self):
        self.add_user('reader@example.invalid', role_name='editor')
        self.assert_seed_refuses_without_changes('No unambiguous')

    def test_missing_or_blank_bootstrap_stops_before_any_seed_writes(self):
        for value in (None, '', '   '):
            with self.subTest(value=value), patch.dict(os.environ):
                os.environ.pop('ADMIN_INITIAL_PASSWORD', None)
                if value is not None:
                    os.environ['ADMIN_INITIAL_PASSWORD'] = value
                before = self.database_snapshot()
                with patch.object(self.seed_module, 'seed_gallery_images') as gallery:
                    with self.assertRaisesRegex(RuntimeError, 'ADMIN_INITIAL_PASSWORD'):
                        self.seed_module.seed()
                    gallery.assert_not_called()
                self.assertEqual(self.database_snapshot(), before)

    def test_explicit_bootstrap_is_private_and_rerun_preserves_the_new_hash(self):
        password = secrets.token_urlsafe(24)
        output = io.StringIO()
        with patch.dict(os.environ, {'ADMIN_INITIAL_PASSWORD': password}):
            with patch.object(self.seed_module, 'seed_gallery_images'), redirect_stdout(output):
                self.seed_module.seed()
        user = User.query.one()
        self.assertEqual(user.email, TARGET_EMAIL)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.role.name, 'super_admin')
        original_hash = user.password_hash
        self.assertNotIn(password, output.getvalue())
        self.assertNotIn(original_hash, output.getvalue())
        with patch.dict(os.environ):
            os.environ.pop('ADMIN_INITIAL_PASSWORD', None)
            self.seed_module._seed_admin_settings()
        self.assertEqual(User.query.one().password_hash, original_hash)

    def test_commit_failure_rolls_back_email_settings_roles_and_permissions(self):
        self.add_user(LEGACY_EMAIL)
        db.session.add(SiteSettings(contact_email='keep@example.invalid'))
        db.session.commit()
        before = self.database_snapshot()
        with patch.object(db.session, 'commit', side_effect=RuntimeError('Simulated write failure')):
            with self.assertRaisesRegex(RuntimeError, 'Simulated write failure'):
                self.seed_module._seed_admin_settings()
        self.assertEqual(self.database_snapshot(), before)


class LegacyMigrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = sa.create_engine('sqlite:///:memory:')
        self.connection = self.engine.connect()
        self.connection.exec_driver_sql('PRAGMA foreign_keys=ON')
        self.connection.commit()
        self.migration_context = MigrationContext.configure(self.connection)
        versions = BACKEND / 'migrations' / 'versions'
        self.initial = load_module('initial_regression_revision', versions / '201fa049ee30_initial_migration.py')
        self.tracking = load_module(
            'tracking_regression_revision', versions / '2b82845ea46d_add_order_tracking_reviews_gallery_.py',
        )
        self.apply(self.initial.upgrade)
        self.initial_columns = {column['name'] for column in sa.inspect(self.connection).get_columns('orders')}

    def tearDown(self):
        self.connection.close()
        self.engine.dispose()

    def apply(self, operation):
        with Operations.context(self.migration_context):
            operation()
        self.connection.commit()

    def table(self, name):
        return sa.Table(name, sa.MetaData(), autoload_with=self.connection)

    def rows(self, name):
        table = self.table(name)
        return [dict(row) for row in self.connection.execute(sa.select(table).order_by(table.c.id)).mappings()]

    def insert_orders(self, statuses):
        table = self.table('orders')
        for index, status in enumerate(statuses, start=1):
            self.connection.execute(table.insert().values(
                id=index, full_name=f'Legacy Customer {index}', phone_number='0780000000',
                event_type='birthday', event_date=date(2025, 2, 3), flavor='vanilla', cake_size='2kg',
                inspiration_image=f'preserved-{index}.jpg', special_instructions='Preserve instructions',
                delivery_type='delivery', delivery_address='Preserve address', status=status,
                created_at=datetime(2025, 1, 1, 10, 0),
                updated_at=datetime(2025, 1, 2, 11, 0) if index % 2 else None,
            ))
        self.connection.commit()

    def test_backfill_maps_every_legacy_status_preserves_fields_and_adds_public_snapshot(self):
        mapping = {'pending': 'new', 'contacted': 'confirmed', 'in_progress': 'baking', 'completed': 'delivered'}
        self.insert_orders([*mapping, *VALID_STATUSES])
        before = self.rows('orders')
        self.apply(self.tracking.upgrade)
        after = self.rows('orders')
        history = self.rows('order_status_history')
        references = [row['order_reference'] for row in after]
        self.assertEqual(len(set(references)), len(before))
        self.assertEqual(len(history), len(before))
        for original, current, snapshot in zip(before, after, history):
            self.assertRegex(current['order_reference'], r'^CC-[A-Z0-9]{5}$')
            expected_status = mapping.get(original['status'], original['status'])
            self.assertEqual(current['status'], expected_status)
            for key, value in original.items():
                if key != 'status':
                    self.assertEqual(current[key], value)
            self.assertEqual(snapshot['order_id'], original['id'])
            self.assertEqual(snapshot['status'], expected_status)
            self.assertEqual(snapshot['created_at'], original['updated_at'] or original['created_at'])
            self.assertIn('snapshot', snapshot['note'].lower())
        inspector = sa.inspect(self.connection)
        reference_column = next(c for c in inspector.get_columns('orders') if c['name'] == 'order_reference')
        self.assertFalse(reference_column['nullable'])
        self.assertIn('uq_orders_order_reference', {c['name'] for c in inspector.get_unique_constraints('orders')})
        self.assertIn('fk_orders_gallery_item_id_gallery_items', {c['name'] for c in inspector.get_foreign_keys('orders')})
        self.assertEqual(self.connection.exec_driver_sql('PRAGMA foreign_key_check').all(), [])

    def test_reference_collision_retries_before_assigning_distinct_references(self):
        self.insert_orders(['pending', 'contacted'])
        with patch.object(self.tracking.secrets, 'choice', side_effect=list('AAAAAAAAAABBBBB')) as choice:
            self.apply(self.tracking.upgrade)
        self.assertEqual(choice.call_count, 15)
        self.assertEqual([row['order_reference'] for row in self.rows('orders')], ['CC-AAAAA', 'CC-BBBBB'])

    def test_unknown_status_aborts_before_ddl_or_data_mutation(self):
        self.insert_orders(['pending', 'needs_manual_review'])
        before = self.rows('orders')
        with self.assertRaisesRegex(RuntimeError, 'Unrecognized legacy order status'):
            self.apply(self.tracking.upgrade)
        self.assertEqual(self.rows('orders'), before)
        self.assertNotIn('reviews', sa.inspect(self.connection).get_table_names())
        self.assertNotIn('order_status_history', sa.inspect(self.connection).get_table_names())
        self.assertEqual({c['name'] for c in sa.inspect(self.connection).get_columns('orders')}, self.initial_columns)

    def test_exhausted_reference_allocation_aborts_before_any_ddl(self):
        self.insert_orders(['pending', 'new'])
        before = self.rows('orders')
        with patch.object(self.tracking.secrets, 'choice', return_value='A') as choice:
            with self.assertRaisesRegex(RuntimeError, 'Unable to allocate unique'):
                self.apply(self.tracking.upgrade)
        self.assertEqual(choice.call_count, 505)
        self.assertEqual(self.rows('orders'), before)
        self.assertNotIn('reviews', sa.inspect(self.connection).get_table_names())

    def test_missing_legacy_timestamps_get_snapshot_time_without_altering_order(self):
        self.insert_orders(['pending'])
        orders = self.table('orders')
        self.connection.execute(orders.update().values(created_at=None, updated_at=None))
        self.connection.commit()
        self.apply(self.tracking.upgrade)
        self.assertIsNotNone(self.rows('order_status_history')[0]['created_at'])
        self.assertIsNone(self.rows('orders')[0]['created_at'])
        self.assertIsNone(self.rows('orders')[0]['updated_at'])

    def test_unique_and_non_null_reference_constraints_are_enforced(self):
        self.insert_orders(['pending'])
        self.apply(self.tracking.upgrade)
        orders = self.table('orders')
        existing = self.rows('orders')[0]
        for reference in (existing['order_reference'], None):
            with self.subTest(reference=reference):
                with self.assertRaises(IntegrityError):
                    with self.connection.begin_nested():
                        self.connection.execute(orders.insert().values({**existing, 'id': 2, 'order_reference': reference}))
        self.assertEqual(len(self.rows('orders')), 1)

    def test_downgrade_preserves_orders_and_removes_named_constraints_and_new_tables(self):
        self.insert_orders(['pending', 'completed'])
        self.apply(self.tracking.upgrade)
        expected = [{key: value for key, value in row.items() if key in self.initial_columns} for row in self.rows('orders')]
        self.apply(self.tracking.downgrade)
        self.assertEqual(self.rows('orders'), expected)
        self.assertEqual({c['name'] for c in sa.inspect(self.connection).get_columns('orders')}, self.initial_columns)
        self.assertNotIn('reviews', sa.inspect(self.connection).get_table_names())
        self.assertNotIn('order_status_history', sa.inspect(self.connection).get_table_names())
        self.assertEqual(self.connection.exec_driver_sql('PRAGMA foreign_key_check').all(), [])

    def test_empty_legacy_database_can_upgrade_and_downgrade(self):
        self.apply(self.tracking.upgrade)
        self.assertEqual(self.rows('orders'), [])
        self.assertEqual(self.rows('order_status_history'), [])
        self.apply(self.tracking.downgrade)
        self.assertEqual(self.rows('orders'), [])


class TrackingPrivacyTests(SQLiteAppCase):
    def track(self, reference, phone):
        return self.client.post('/api/v1/track', json={'order_reference': reference, 'phone_number': phone})

    def test_ugandan_equivalents_match_in_both_directions(self):
        local = '078' + ''.join(secrets.choice(string.digits) for _ in range(7))
        international = '256' + local[1:]
        variants = [local, international, '+' + international, f'{local[:4]}-{local[4:7]} {local[7:]}',
                    f'+256 {local[1:4]}-{local[4:7]} {local[7:]}']
        order = self.make_order(local)
        for stored in variants:
            order.phone_number = stored
            db.session.commit()
            for submitted in variants:
                with self.subTest(stored=stored, submitted=submitted):
                    response = self.track(' ' + order.order_reference.lower() + ' ', submitted)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.get_json()['order_reference'], order.order_reference)
                    self.assertEqual(order.phone_number, stored)

    def test_wrong_phone_and_unknown_reference_have_identical_private_responses(self):
        order = self.make_order()
        wrong_phone = order.phone_number[:-1] + str((int(order.phone_number[-1]) + 1) % 10)
        unknown_reference = generate_order_reference()
        while unknown_reference == order.order_reference:
            unknown_reference = generate_order_reference()
        responses = [self.track(order.order_reference, wrong_phone), self.track(unknown_reference, order.phone_number),
                     self.track('invalid-reference', order.phone_number), self.track(order.order_reference, 'not-a-phone')]
        for response in responses:
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.get_json(), responses[0].get_json())
            self.assertEqual(set(response.get_json()), {'success', 'message'})
            self.assertNotIn(order.full_name, response.get_data(as_text=True))
            self.assertNotIn(order.phone_number, response.get_data(as_text=True))

    def test_success_exposes_only_contract_fields_and_public_history_fields(self):
        order = self.make_order(status='baking')
        body = self.track(order.order_reference, order.phone_number).get_json()
        self.assertEqual(set(body), {
            'success', 'order_reference', 'status', 'full_name', 'event_date', 'event_type',
            'flavor', 'cake_size', 'delivery_type', 'created_at', 'status_history',
        })
        self.assertEqual(len(body['status_history']), 1)
        self.assertEqual(set(body['status_history'][0]), {'status', 'note', 'created_at'})
        self.assertEqual(body['status_history'][0]['note'], 'Public status note.')
        serialized = json.dumps(body)
        for private_value in (order.phone_number, order.delivery_address, order.special_instructions, order.inspiration_image):
            self.assertNotIn(private_value, serialized)

    def test_malformed_json_objects_and_non_string_fields_are_rejected_safely(self):
        order = self.make_order()
        for payload in (None, [], ['x'], True, 3, 'text', {}):
            with self.subTest(payload=payload):
                response = self.client.post('/api/v1/track', data=json.dumps(payload), content_type='application/json')
                self.assertEqual(response.status_code, 400)
                self.assertEqual(set(response.get_json()), {'success', 'message'})
        for field in ('order_reference', 'phone_number'):
            for invalid in (None, True, 4, 1.2, [], {}, ''):
                with self.subTest(field=field, invalid=invalid):
                    payload = {'order_reference': order.order_reference, 'phone_number': order.phone_number, field: invalid}
                    self.assertEqual(self.client.post('/api/v1/track', json=payload).status_code, 400)
        response = self.client.post('/api/v1/track', data='{', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_database_errors_never_escape_the_public_tracker(self):
        order = self.make_order()
        with patch('app.controllers.tracking_controller.Order') as model, patch.object(self.app.logger, 'exception'):
            model.query.filter_by.return_value.first.side_effect = RuntimeError('internal-database-detail')
            response = self.track(order.order_reference, order.phone_number)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(set(response.get_json()), {'success', 'message'})
        self.assertNotIn('internal-database-detail', response.get_data(as_text=True))


class ReviewModerationTests(SQLiteAppCase):
    def submit_review(self, rating=5, **changes):
        return self.client.post('/api/v1/reviews', json={
            'customer_name': 'Review Customer', 'rating': rating, 'review_text': 'A lovely celebration cake.', **changes,
        })

    def test_approval_controls_visibility_and_average_and_public_cannot_self_approve(self):
        self.assertEqual(self.client.get('/api/v1/reviews').get_json(), {
            'success': True, 'total': 0, 'average_rating': 0, 'reviews': [],
        })
        first = self.submit_review(is_approved=True)
        self.assertEqual(first.status_code, 201)
        self.assertFalse(first.get_json()['review']['is_approved'])
        first_id = first.get_json()['review']['id']
        second_id = self.submit_review(rating=1).get_json()['review']['id']
        self.assertEqual(self.client.get('/api/v1/reviews').get_json()['total'], 0)
        headers = self.token_headers(permissions=['content_read', 'content_write'])
        admin = self.client.get('/api/v1/admin/reviews', headers=headers).get_json()
        self.assertEqual((admin['total'], admin['pending']), (2, 2))
        self.assertEqual(self.client.patch(f'/api/v1/admin/reviews/{first_id}/approve', headers=headers).status_code, 200)
        public = self.client.get('/api/v1/reviews').get_json()
        self.assertEqual((public['total'], public['average_rating']), (1, 5.0))
        self.client.patch(f'/api/v1/admin/reviews/{second_id}/approve', headers=headers)
        self.assertEqual(self.client.get('/api/v1/reviews').get_json()['average_rating'], 3.0)
        self.client.patch(f'/api/v1/admin/reviews/{first_id}/approve', headers=headers)
        self.assertEqual(self.client.get('/api/v1/reviews').get_json()['average_rating'], 1.0)
        self.assertEqual(self.client.delete(f'/api/v1/admin/reviews/{second_id}', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/api/v1/reviews').get_json()['total'], 0)

    def test_admin_review_routes_require_bearer_auth_and_matching_permissions(self):
        review_id = self.submit_review().get_json()['review']['id']
        routes = [('get', '/api/v1/admin/reviews'), ('patch', f'/api/v1/admin/reviews/{review_id}/approve'),
                  ('delete', f'/api/v1/admin/reviews/{review_id}')]
        for method, route in routes:
            with self.subTest(method=method):
                self.assertEqual(getattr(self.client, method)(route).status_code, 401)
                self.assertEqual(getattr(self.client, method)(route, headers={'Authorization': 'Bearer invalid'}).status_code, 422)
                self.assertEqual(getattr(self.client, method)(route, headers=self.token_headers()).status_code, 403)
        read_only = self.token_headers(permissions=['content_read'])
        self.assertEqual(self.client.get('/api/v1/admin/reviews', headers=read_only).status_code, 200)
        self.assertEqual(self.client.patch(routes[1][1], headers=read_only).status_code, 403)
        self.assertEqual(self.client.delete(routes[2][1], headers=read_only).status_code, 403)
        self.assertFalse(db.session.get(Review, review_id).is_approved)

    def test_rating_validation_rejects_booleans_fractions_nonfinite_and_oversized_values(self):
        invalid_ratings = [True, False, 0, 6, -1, 2.5, 5.0, float('nan'), float('inf'), None,
                           [], {}, '4.5', '5.0', '1e0', '9' * 5000]
        for rating in invalid_ratings:
            with self.subTest(rating_type=type(rating).__name__):
                response = self.submit_review(rating=rating)
                self.assertEqual(response.status_code, 400)
                self.assertIn('rating', response.get_json()['errors'])
        self.assertEqual(Review.query.count(), 0)
        for rating in (1, 5, '3', ' 4 '):
            self.assertEqual(self.submit_review(rating=rating).status_code, 201)

    def test_review_body_and_text_types_lengths_are_validated(self):
        for payload in (None, [], True, 3, 'text'):
            response = self.client.post('/api/v1/reviews', data=json.dumps(payload), content_type='application/json')
            self.assertEqual(response.status_code, 400)
        for field, invalid in [('customer_name', {}), ('customer_name', 123), ('customer_name', 'x' * 61),
                               ('review_text', []), ('review_text', False), ('review_text', 'x' * 801)]:
            with self.subTest(field=field):
                response = self.submit_review(**{field: invalid})
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.get_json()['errors'])
        self.assertEqual(Review.query.count(), 0)

    def test_review_database_failures_are_generic_and_rollback(self):
        with patch.object(db.session, 'commit', side_effect=RuntimeError('private-sql-detail')):
            with patch.object(self.app.logger, 'exception'):
                response = self.submit_review()
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('private-sql-detail', response.get_data(as_text=True))
        self.assertEqual(Review.query.count(), 0)
        with patch('app.controllers.review_controller.Review') as model, patch.object(self.app.logger, 'exception'):
            model.query.filter_by.side_effect = RuntimeError('private-sql-detail')
            response = self.client.get('/api/v1/reviews')
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('private-sql-detail', response.get_data(as_text=True))


class OrderReferenceTests(SQLiteAppCase):
    def order_form(self, **changes):
        return {
            'full_name': 'New Customer', 'phone_number': '0780000000', 'event_type': 'birthday',
            'event_date': (date.today() + timedelta(days=30)).isoformat(), 'flavor': 'vanilla',
            'cake_size': '2kg', **changes,
        }

    def notification_mocks(self):
        stack = ExitStack()
        stack.enter_context(patch.object(orders_controller, 'send_order_email'))
        stack.enter_context(patch.object(orders_controller, 'build_whatsapp_link', return_value='https://example.invalid/'))
        stack.enter_context(patch.object(orders_controller, 'build_baker_to_customer_whatsapp_link', return_value='https://example.invalid/'))
        return stack

    def test_orm_reference_default_uses_secrets_and_is_non_nullable(self):
        with patch('app.models.orders.secrets.choice', side_effect=list('A1B2C')) as choice:
            self.assertEqual(generate_order_reference(), 'CC-A1B2C')
        self.assertEqual(choice.call_count, 5)
        self.assertFalse(Order.__table__.c.order_reference.nullable)
        self.assertRegex(self.make_order().order_reference, r'^CC-[A-Z0-9]{5}$')

    def test_unique_constraint_race_retries_and_creates_one_order_and_one_snapshot(self):
        existing = self.make_order()
        reference = generate_order_reference()
        while reference == existing.order_reference:
            reference = generate_order_reference()
        with patch.object(orders_controller, '_generate_unique_reference', side_effect=[existing.order_reference, reference]) as allocate:
            with self.notification_mocks():
                response = self.client.post('/api/v1/orders/create', data=self.order_form())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(allocate.call_count, 2)
        self.assertEqual(response.get_json()['order_reference'], reference)
        created = Order.query.filter_by(order_reference=reference).one()
        self.assertEqual(created.status_history.count(), 1)
        self.assertEqual(Order.query.count(), 2)
        self.assertEqual(OrderStatusHistory.query.count(), 2)

    def test_reference_race_retry_limit_is_bounded_and_does_not_leak_database_details(self):
        existing = self.make_order()
        with patch.object(orders_controller, '_generate_unique_reference', return_value=existing.order_reference) as allocate:
            with self.notification_mocks(), patch.object(self.app.logger, 'exception'):
                response = self.client.post('/api/v1/orders/create', data=self.order_form())
        self.assertEqual(response.status_code, 500)
        self.assertEqual(allocate.call_count, 5)
        self.assertEqual(Order.query.count(), 1)
        self.assertEqual(OrderStatusHistory.query.count(), 1)
        self.assertNotIn('UNIQUE', response.get_data(as_text=True))
        self.assertNotIn(existing.order_reference, response.get_data(as_text=True))

    def test_reference_precheck_never_returns_an_unchecked_fallback(self):
        existing = self.make_order()
        with patch.object(orders_controller, 'generate_order_reference', return_value=existing.order_reference) as generate:
            with self.assertRaisesRegex(RuntimeError, 'Unable to allocate'):
                orders_controller._generate_unique_reference()
        self.assertEqual(generate.call_count, 10)

    def test_mysql_reference_constraint_classification_does_not_retry_unrelated_errors(self):
        duplicate_reference = IntegrityError(None, None, Exception(1062, "Duplicate entry for key 'orders.order_reference'"))
        unrelated = IntegrityError(None, None, Exception(1062, "Duplicate entry for key 'other_field'"))
        foreign_key = IntegrityError(None, None, Exception(1452, 'Foreign key failure order_reference'))
        self.assertTrue(orders_controller._is_reference_collision(duplicate_reference))
        self.assertFalse(orders_controller._is_reference_collision(unrelated))
        self.assertFalse(orders_controller._is_reference_collision(foreign_key))

    def test_gallery_ids_reject_fractional_boolean_and_out_of_range_numbers_before_querying(self):
        for invalid in (True, False, 1.5, [], {}, '-1', '0', '1.5', '1e2', '2147483648', '9' * 5000):
            with self.subTest(value_type=type(invalid).__name__):
                value, error = orders_controller._parse_gallery_item_id(invalid)
                self.assertIsNone(value)
                self.assertIsNotNone(error)
        item = GalleryItem(title='Existing inspiration', image_url='existing.jpg', category='other')
        db.session.add(item)
        db.session.commit()
        self.assertEqual(orders_controller._parse_gallery_item_id(str(item.id)), (item.id, None))
        self.assertEqual(orders_controller._parse_gallery_item_id(None), (None, None))
        for raw in ('0', '1.2', '2147483648', '9' * 5000):
            self.assertEqual(self.client.post('/api/v1/orders/create', data=self.order_form(gallery_item_id=raw)).status_code, 400)
        self.assertEqual(Order.query.count(), 0)

    def test_admin_status_types_are_safe_and_all_canonical_statuses_remain_available(self):
        order = self.make_order()
        endpoint = f'/api/v1/orders/{order.id}/status'
        headers = self.token_headers(permissions=['orders_write'])
        self.assertEqual(self.client.patch(endpoint, json={'status': 'ready'}).status_code, 401)
        for payload in ([], 'ready', {'status': []}, {'status': True}, {'status': 'ready', 'note': {}}, {'status': 'ready', 'note': 'x' * 501}):
            self.assertEqual(self.client.patch(endpoint, json=payload, headers=headers).status_code, 400)
        self.assertEqual(VALID_STATUSES, ['new', 'confirmed', 'baking', 'ready', 'out_for_delivery', 'delivered', 'cancelled'])
        for status in VALID_STATUSES:
            response = self.client.patch(endpoint, json={'status': status}, headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()['order']['status'], status)
        self.assertEqual(order.status_history.count(), len(VALID_STATUSES))


if __name__ == '__main__':
    unittest.main()
