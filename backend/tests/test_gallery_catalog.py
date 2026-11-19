"""Gallery preservation regressions; isolated SQLite and temporary media, no live services."""
import importlib.util
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from flask_jwt_extended import create_access_token

with patch('dotenv.load_dotenv', return_value=False):
    import app as application
    from app.controllers.orders import orders_controller
    from app.extensions import db
    from app.models.gallery import GalleryItem, gallery_media_url
    from app.models.orders import Order
    from app.models.rbac import User
    from app.models.settings import SiteSettings

BACKEND = Path(__file__).resolve().parents[1]
ORIGINALS = BACKEND.parent / 'frontend' / 'src' / 'assets' / 'gallery'
CATALOG = BACKEND / 'data' / 'gallery_catalog.json'
MATCHED_COUNTS = {'birthday': 33, 'kids': 29, 'sculpted': 16, 'wedding': 12, 'baby': 9,
                  'cupcakes': 7, 'holiday': 3, 'corporate': 2, 'graduation': 1}
TOTAL_COUNTS = {**MATCHED_COUNTS, 'kids': 30, 'other': 7}

# Independent compact transcription of Maya's post-level evidence. Repeated carousel
# frames intentionally share a shortcode/title; inventory equality checks every filename.
REFERENCE_POSTS = '''BYqYplCAo91|wedding|White Drape Wedding Tiers with Sparkler
BYsv0Aug1SJ|sculpted|Blue Label Whisky Bottle Cake
BaHvQ2SHUCm|kids|Moana Name Sign Cake Collage
BcK8DX4g0gI|kids|Winnie the Pooh Number 5 Cake
Bcf9cxOAZ2D|holiday|Christmas Reindeer "Thank You Team" Cake
B-_i0N8Hv9E|sculpted|Jackfruit Sculpted Cake
B_AmTzinDyA|sculpted|Cooking Pot and Banana Leaf Cake
B_Amk6LHFYl|sculpted|Storybook and Coffee Mug Cake
B_AmvCkHZiN|kids|Spider-Man Two-Tier Web City Cake
B_AnFevnlgc|birthday|Coral Rosette Drip Cake
B_AnmIXHYrO|birthday|Red Drip Cake with Sugar Roses
B_K0f_2HpuG|kids|Seaside Number 6 Cake
B_K22j3nYWL|kids|Panda with Pink Bow Cake
B_K2GHynPtH|baby|Baby in a Cradle Ruffle Cake
B_K2pECHchl|sculpted|Rolex Box and Watch Cake
B_K3NtenE1S|baby|Pink and Blue Bow Gender Reveal Cake
B_K4a2JH5OX|wedding|Orange and Pink Sugar Rose Cascade
B_K5O46nkWq|baby|"Push!" Baby Arrival Cake
B_K5tiknej5|kids|Moana and Maui Flower Cake
B_K6691HJmh|sculpted|Pouring Guinness Barrel Cake
B_K6MM-nRyk|kids|Topsy-Turvy Racing Cars Cake
B_K6TDknQ99|sculpted|DJ Deck Birthday Cake
B_K6xCHnJhj|kids|Doll Ballgown Birthday Cake
B_Kz_wlHwCU|wedding|Tuxedo Groom's Cake
B_hDbYzFj95|cupcakes|Rose Swirl Cupcake Box
B_hp_zmHOFy|birthday|Chocolate Drip Cake with Strawberries
B_zxXWtHx_I|birthday|Pink Ombre Rosette Cake
CAxZNg5HP8Y|cupcakes|Sesame Street Cupcakes
CBLvhalHE-W|holiday|Football Goal Net Cake for Dad
CBVya3WH-Up|birthday|Laptop 16th Birthday Cake
CBihkW8HtuQ|kids|Baby Shark Under-the-Sea Cake
CBiiKfVH8yj|birthday|Vintage Suitcase Cake for Mum
CBv_0O7nKUb|baby|"He or She?" Baby Booties Cake
CB6RrL_nf2R|birthday|Gold Stiletto on Pink Lace Cake
CB815I7nb4B|kids|Paw Patrol Lookout Cake
CB-jFgIHAlr|baby|Moon and Teddy Baby Cake
CCMOk9NHXGh|sculpted|Cognac Bottle Cake
CCO-I6sHi_Z|kids|Rainbow Unicorn Two-Tier Cake
CCO-cwhHyoF|kids|Mermaid Tail Number 10 Cake
CCk80_5F5yM|kids|Frozen Elsa and Olaf Cake
CCk8e-DF8xx|kids|Bluey and Bingo Sprinkle Cake
CDRRBzGnHy5|sculpted|Leopard Print Suitcase Cake
CD-kwB5HZEV|cupcakes|"Thank You" Coach Cupcakes
CEhtXSznUhG|kids|Minions Balloon Cake
CE7TEbhF8-s|baby|Baby Teddy Balloon Cake
CE7TxpTFCx5|wedding|White Ruffle Wedding Cake with Sugar Roses
CE7UoQHlm1g|corporate|Sculpted Water Pump Cake
CFMhrlilE50|kids|Rainbow Twin Doll Cakes
CFSvv_Dns7G|birthday|Hand-Painted Pop Girl Portrait Cake
CF0AKhTnG85|sculpted|Quilted Handbag and Make-Up Cake
CGT_EHClvZa|cupcakes|Cupcakes with Sweet Messages
CGUE6dbFhEx|sculpted|Wine Barrel Cake
CGs1QFPryGG|kids|Baby Moana Number 4 Cake
CG0LikGLpij|kids|Moana Two-Tier Flower Cake
CHBSjgGrfrE|sculpted|Vegetable Basket Cake
CHUwpMyrJUf|corporate|Yellow Gas Cylinder Cake
CHUxCEmrK1k|kids|Frozen Elsa and Anna Drip Cake
CHUxJ57rs2A|birthday|Gift Box Cake with Sugar Orchids
CHaNpM3Lkga|birthday|Black Top Hat Cake with Purple Ruffles
CHvgnCCrh2O|sculpted|Green Sack and Woven Basket Cake
CIOJ8Ogr4ai|kids|Cars Checkered Cake
CK677sZLxmV|kids|Superman and Friends Cake
CK68NT9rf1y|holiday|Super Dad Basketball Cake
COC-Hv6LS4s|wedding|African Print Wedding Tiers at a Garden Reception
COqrC9-LgzC|kids|Frozen Tall Tier Cake
COqrI9LLIag|baby|Expecting Mum Silhouette Cake
COqrTkPrxw9|wedding|Red Rose Wedding Tiers
COqrZNNLA33|baby|Baby Blocks and Teddy Shower Cake
CPu67itrTwY|kids|Hulk Avengers Cake
CPu6nUTrHHS|sculpted|Teal Ruffle Clutch and Heel Cake
CQA-aIwLiqc|birthday|Rainbow Three-Tier Cake with Cupcakes
CQxW-GIrxdG|sculpted|Chanel Handbag and Pearls Cake
CQxXlKArDFc|cupcakes|Sprinkle Donut Box
CTpPm6UoIiM|birthday|Clock and Gears Cake
CU4FpTpoEoG|kids|Spider-Man City Skyline Cake
CU4NnoEobhD|cupcakes|Pastel Cupcake Box
CZGtFzJLhSG|wedding|Five-Tier Peach and White Wedding Cake
CZNOW9fr_IU|birthday|Money Tower Cake
CdHEErqr_nt|kids|Cocomelon Rainbow Cake
CdHEZpVrmJ3|wedding|African Pattern Drum Tier Cake
CfpLd3Xrezp|wedding|Green and Gold Wedding Tiers
C8JQR4fIzFh|birthday|Arsenal Football Cake
C8JQgyxIBVW|kids|Spider-Man Drip Cake
C8JQnodIaxJ|birthday|Football Birthday Cake with Gold Stars
DCWvPASo7RZ|birthday|Piano and Music Notes Cake
DMwkk5wMwe2|kids|Paw Patrol Three-Tier Cake
DMzGiorCXGK|birthday|Black Heart Cake with Red Roses
DNEl1cTNRFI|kids|Cars Lightning McQueen Cake
DP9esp8DGwv|birthday|Einstein E=mc² Maths Cake
BiPuGfqll_a|birthday|Be sure that I will get t right. Whatsapp 0781470984
CE63h5BFGbt|birthday|BritamBakeOffChallenge
Bgo1d_XgEtJ|wedding|Cake by
Bgo1k0Egdrs|wedding|Cake by
CmPXt3VLAXd|birthday|Carry me on those wings so firm. To the heights in light as…
BYqVPt_A3qU|wedding|Cattle theme. Kuhingira
BiPtQXAFnRe|birthday|Dream team comes to reality
CBihdb4HJQk|birthday|Happy birthday SKY
CFZEQHongWL|birthday|Happy birthday dea
CE7T5-MFPhF|birthday|Installment trials
BcK8f3zgq7N|graduation|It is more than GRADUATION... Its an experience... We…
Btcm6_4FCfu|birthday|Margla. May u live happily ever after
B_t2bacFwED|birthday|Red velvet and vanilla buttercream
DQt1ocziPaf|sculpted|Sugar sculpture, Eaten today but kept in my memory
B4xhcbmF-Tt|birthday|Thanx Martin
Boes5EciE6K|birthday|Thanx Reagan for choosing
CoC4fCaIV2D|birthday|Tis the season to ask and get… it’s a request from you and…
Biwtsx9F0Io|birthday|Wow'''


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CatalogEvidenceTests(unittest.TestCase):
    def test_all_120_original_filenames_and_112_exact_metadata_matches(self):
        document = json.loads(CATALOG.read_text(encoding='utf-8'))
        entries = document['items']
        self.assertEqual(document['expected_count'], 120)
        self.assertEqual(len(entries), 120)
        self.assertEqual(len({row['filename'] for row in entries}), 120)
        self.assertEqual({row['filename'] for row in entries}, {p.name for p in ORIGINALS.iterdir() if p.is_file()})
        self.assertEqual(Counter(row['media_type'] for row in entries), {'image': 119, 'video': 1})
        self.assertEqual(Counter(row['category'] for row in entries), TOTAL_COUNTS)
        matched = [row for row in entries if row['source'].startswith('reference_')]
        self.assertEqual(len(matched), 112)
        self.assertEqual(Counter(row['category'] for row in matched), MATCHED_COUNTS)
        expected = {code: (category, title) for code, category, title in
                    (line.split('|', 2) for line in REFERENCE_POSTS.splitlines())}
        observed = Counter()
        for row in matched:
            if row['filename'] == 'spiderman.jpg':
                self.assertEqual((row['category'], row['title'], row['source']),
                                 ('kids', 'Spider-Man, Age 6', 'reference_filename'))
            else:
                code = re.search(r'\d{4}-\d{2}-\d{2}_([A-Za-z0-9_-]{11})_\d+', row['filename']).group(1)
                self.assertEqual((row['category'], row['title']), expected[code], row['filename'])
                self.assertEqual(row['source'], 'reference_shortcode')
                observed[code] += 1
            self.assertEqual(document['sources'][row['source']]['url'], 'https://cinderellacakes.ug/api/cakes?source=own')
        self.assertEqual(set(observed), set(expected))
        self.assertEqual(sum(observed.values()), 111)
        self.assertEqual({key: count for key, count in observed.items() if count > 1},
                         {'CB-jFgIHAlr': 2, 'CQxXlKArDFc': 2, 'Biwtsx9F0Io': 3})
        unmatched = {row['filename']: row['category'] for row in entries if row['source'] == 'local_filename'}
        self.assertEqual(unmatched, {
            'cinderella.cakes.ug_2020-12-20_CJCCAGYr6H_2468544348702089727.jpg': 'other',
            'cinderella.cakes.ug_2020-12-20_CJCCFjFr0Z_2468544723119195775.jpg': 'other',
            'SpongeBob.jpg': 'kids', 'ThankYou!.jpg': 'other', 'bag.jpg': 'other',
            'cinderella.jpg': 'other', 'heart.jpg': 'other', 'king.jpg': 'other',
        })

    def test_cli_help_does_not_load_flask_dotenv_or_database(self):
        # -S makes third-party imports unavailable; --help must still work.
        with tempfile.TemporaryDirectory() as cwd:
            result = subprocess.run([sys.executable, '-B', '-S', str(BACKEND / 'seed.py'), '--help'],
                                    cwd=cwd, capture_output=True, text=True, timeout=15, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--gallery-only', result.stdout)
        self.assertIn('--source-dir', result.stdout)


class GalleryImportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        values = {
            'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False, 'SECRET_KEY': secrets.token_urlsafe(48),
            'JWT_SECRET_KEY': secrets.token_urlsafe(48), 'BCRYPT_LOG_ROUNDS': 4,
            'UPLOAD_FOLDER': str(self.root / 'persistent-media'), 'GALLERY_SOURCE_DIR': str(ORIGINALS),
            'MAIL_ENABLED': False, 'CORS_ORIGINS': [], 'MAX_CONTENT_LENGTH': 5 * 1024 * 1024,
        }
        config = type('IsolatedGalleryConfig', (), values)
        with patch.dict(application.config_by_name, {'gallery-regression': config}):
            self.app = application.create_app('gallery-regression')
        self.context = self.app.app_context()
        self.context.push()
        self.assertEqual(db.engine.url.render_as_string(), 'sqlite:///:memory:')
        db.create_all()
        self.client = self.app.test_client()
        with patch.object(application, 'create_app', return_value=self.app):
            self.seed = load_module('isolated_gallery_seed', BACKEND / 'seed.py')
        self.entries = self.seed.load_gallery_catalog()
        self.uploads = Path(self.app.config['UPLOAD_FOLDER'])
        self.headers = {'Authorization': 'Bearer ' + create_access_token(identity='gallery-verifier',
                        additional_claims={'permissions': ['content_write', 'orders_read']})}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def import_gallery(self, source=None):
        with redirect_stdout(io.StringIO()):
            result = self.seed.seed_gallery_images(source)
        # The CLI helper owns a separate app context/session from this test client.
        db.session.expire_all()
        return result

    def rows(self):
        return {row.id: {**row.to_dict(), 'catalog_filename': row.catalog_filename}
                for row in GalleryItem.query.order_by(GalleryItem.id).all()}

    def legacy(self, entry, index=1, prefix=''):
        filename = entry['filename']
        stem, suffix = os.path.splitext(filename)
        stored = f'gallery_{index:032x}_{self.seed._safe_stem(stem)}{suffix}'
        row = GalleryItem(self.seed._build_title(filename), prefix + stored,
                          category=self.seed._guess_category(filename))
        db.session.add(row)
        db.session.commit()
        return row

    def make_order(self, item):
        order = Order('Gallery Customer', '0780000000', 'birthday', date.today() + timedelta(days=30),
                      'vanilla', '2kg', inspiration_image='customer-photo.jpg')
        order.gallery_item = item
        db.session.add(order)
        db.session.commit()
        return order

    def test_import_120_including_video_is_idempotent_and_never_touches_originals(self):
        before = {p.name: self.seed._digest(p) for p in ORIGINALS.iterdir() if p.is_file()}
        with patch.dict(os.environ):
            os.environ.pop('ADMIN_INITIAL_PASSWORD', None)
            first = self.import_gallery()
        self.assertEqual(first['created'], 120)
        self.assertEqual(GalleryItem.query.count(), 120)
        self.assertEqual(Counter(row.category for row in GalleryItem.query.all()), TOTAL_COUNTS)
        self.assertEqual(Counter(row.media_type for row in GalleryItem.query.all()), {'image': 119, 'video': 1})
        snapshot = self.rows()
        second = self.import_gallery()
        self.assertEqual(second, {'total': 120, 'created': 0, 'curated': 0, 'preserved': 120})
        self.assertEqual(self.rows(), snapshot)
        self.assertEqual(User.query.count(), 0)
        self.assertEqual(SiteSettings.query.count(), 0)
        self.assertEqual({p.name: self.seed._digest(p) for p in ORIGINALS.iterdir() if p.is_file()}, before)
        self.assertEqual({p.name: self.seed._digest(p) for p in (self.uploads / 'gallery').iterdir()}, before)

    def test_119_legacy_rows_keep_ids_paths_order_links_and_get_curated_once(self):
        originals = {}
        for index, entry in enumerate(self.entries, 1):
            if entry['media_type'] == 'video':
                continue
            prefix = '/static/uploads/inspiration/' if index % 2 else ''
            row = self.legacy(entry, index, prefix)
            originals[entry['filename']] = (row.id, row.image_url)
        row = GalleryItem.query.first()
        order = self.make_order(row)
        original_order_id, original_design_id = order.id, row.id
        self.assertEqual(self.import_gallery()['created'], 1)
        self.assertEqual(GalleryItem.query.count(), 120)
        for entry in self.entries:
            row = GalleryItem.query.filter_by(catalog_filename=entry['filename']).one()
            self.assertEqual((row.title, row.category), (entry['title'], entry['category']))
            if entry['filename'] in originals:
                self.assertEqual((row.id, row.image_url), originals[entry['filename']])
        snapshot = self.rows()
        self.import_gallery()
        self.assertEqual(self.rows(), snapshot)
        db.session.expire_all()
        self.assertEqual(db.session.get(Order, original_order_id).gallery_item_id, original_design_id)

    def test_custom_legacy_metadata_and_later_admin_edits_survive_reseeding(self):
        entry = next(row for row in self.entries if row['category'] == 'wedding')
        legacy = self.legacy(entry)
        legacy.title = 'Owner title'
        legacy.description = 'Keep my notes'
        legacy.category = 'anniversary'
        db.session.commit()
        legacy_id = legacy.id
        self.import_gallery()
        row = db.session.get(GalleryItem, legacy_id)
        self.assertEqual((row.title, row.description, row.category), ('Owner title', 'Keep my notes', 'anniversary'))
        # An administrator can even intentionally restore the exact old generated tuple.
        response = self.client.put(f'/api/v1/gallery/{legacy_id}', headers=self.headers, json={
            'title': self.seed._build_title(entry['filename']), 'description': '',
            'category': self.seed._guess_category(entry['filename']),
        })
        self.assertEqual(response.status_code, 200)
        snapshot = self.rows()
        self.import_gallery()
        self.assertEqual(self.rows(), snapshot)

    def test_missing_empty_and_incomplete_source_fail_before_any_database_mutation(self):
        missing = self.root / 'missing-source'
        empty = self.root / 'empty-source'
        empty.mkdir()
        incomplete = self.root / 'incomplete-source'
        incomplete.mkdir()
        for entry in self.entries[:-1]:
            (incomplete / entry['filename']).write_bytes(b'fixture')
        for source in (missing, empty, incomplete):
            with self.subTest(source=source), patch.object(self.seed, '_seed_admin_settings') as accounts:
                with self.assertRaisesRegex(RuntimeError, 'Gallery source'):
                    self.seed.seed(source)
                accounts.assert_not_called()
                with self.assertRaisesRegex(RuntimeError, 'Gallery source'):
                    self.import_gallery(source)
            self.assertEqual(GalleryItem.query.count(), 0)
            self.assertEqual(User.query.count(), 0)
        (incomplete / self.entries[-1]['filename']).write_bytes(b'')
        with self.assertRaisesRegex(RuntimeError, 'empty'):
            self.import_gallery(incomplete)
        self.assertEqual(GalleryItem.query.count(), 0)

    def test_explicit_source_override_and_relative_backend_resolution(self):
        self.app.config['GALLERY_SOURCE_DIR'] = str(self.root / 'missing')
        with self.assertRaisesRegex(RuntimeError, 'source directory not found'):
            self.seed.preflight_gallery_source()
        root, entries = self.seed.preflight_gallery_source('../frontend/src/assets/gallery')
        self.assertEqual(root, ORIGINALS.resolve())
        self.assertEqual(len(entries), 120)
        self.assertEqual(self.import_gallery(ORIGINALS)['created'], 120)

    def test_staging_copy_failure_leaves_no_partial_rows_or_media(self):
        copy = shutil.copy2
        count = 0
        def fail_second(source, destination):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError('Simulated disk error')
            return copy(source, destination)
        with patch.object(self.seed.shutil, 'copy2', side_effect=fail_second):
            with self.assertRaisesRegex(RuntimeError, 'Simulated disk error'):
                self.import_gallery()
        self.assertEqual(GalleryItem.query.count(), 0)
        self.assertEqual(list(self.uploads.iterdir()), [])

    def test_database_failure_rolls_back_all_rows_and_retry_reuses_verified_copies(self):
        with patch.object(db.session, 'commit', side_effect=RuntimeError('Simulated database error')):
            with self.assertRaisesRegex(RuntimeError, 'Simulated database error'):
                self.import_gallery()
        self.assertEqual(GalleryItem.query.count(), 0)
        self.assertEqual(self.import_gallery()['created'], 120)

    def test_conflicting_destination_and_ambiguous_legacy_rows_never_overwrite(self):
        destination = self.uploads / 'gallery' / self.entries[0]['filename']
        destination.parent.mkdir()
        destination.write_bytes(b'Owner media; never overwrite')
        with self.assertRaisesRegex(RuntimeError, 'destination conflict'):
            self.import_gallery()
        self.assertEqual(destination.read_bytes(), b'Owner media; never overwrite')
        self.assertEqual(GalleryItem.query.count(), 0)
        self.legacy(self.entries[0], 1)
        self.legacy(self.entries[0], 2)
        before = self.rows()
        with self.assertRaisesRegex(RuntimeError, 'Ambiguous'):
            self.import_gallery()
        self.assertEqual(self.rows(), before)

    def test_original_suffix_matching_is_literal_not_sql_like_wildcards(self):
        entry = next(row for row in self.entries if row['source'] == 'reference_shortcode')
        item = self.legacy(entry)
        self.assertTrue(self.seed._legacy_match(item, entry['filename']))
        item.image_url = item.image_url.replace('cinderella.cakes.ug_', 'cinderella.cakes.ugX')
        self.assertFalse(self.seed._legacy_match(item, entry['filename']))
        self.assertFalse(self.seed._legacy_match(item, 'bag.jpg'))

    def test_catalog_traversal_is_rejected_before_source_or_database_access(self):
        document = json.loads(CATALOG.read_text(encoding='utf-8'))
        document['items'][0]['filename'] = '../outside.jpg'
        fake = self.root / 'unsafe.json'
        fake.write_text(json.dumps(document), encoding='utf-8')
        with patch.object(self.seed, 'CATALOG_PATH', fake):
            with self.assertRaisesRegex(RuntimeError, 'Unsafe'):
                self.import_gallery()
        self.assertEqual(GalleryItem.query.count(), 0)

    def test_all_serving_urls_video_ranges_and_order_serialization(self):
        self.import_gallery()
        response = self.client.get('/api/v1/gallery')
        self.assertEqual(response.status_code, 200)
        items = response.get_json()['items']
        self.assertEqual(len(items), 120)
        public = self.client.get('/api/public/gallery').get_json()
        self.assertEqual(public, items)
        for row in items:
            with self.client.get(row['image_url']) as media:
                self.assertEqual(media.status_code, 200, row['image_url'])
                self.assertEqual(media.mimetype, 'video/mp4' if row['media_type'] == 'video' else 'image/jpeg')
        video = next(row for row in items if row['media_type'] == 'video')
        with self.client.get(video['image_url'], headers={'Range': 'bytes=0-31'}) as media:
            self.assertEqual(media.status_code, 206)
            self.assertEqual(len(media.data), 32)
        order = self.make_order(db.session.get(GalleryItem, video['id']))
        self.assertEqual(order.to_dict()['gallery_item'], video)
        detail = self.client.get(f'/api/v1/orders/{order.id}', headers=self.headers).get_json()['order']
        listing = self.client.get('/api/v1/orders', headers=self.headers).get_json()['orders'][0]
        for serialized in (detail, listing):
            self.assertEqual(serialized['gallery_item_id'], video['id'])
            self.assertEqual(serialized['gallery_item'], video)
        self.import_gallery()
        db.session.expire_all()
        self.assertEqual(db.session.get(Order, order.id).gallery_item_id, video['id'])
        counts = self.client.get('/api/v1/gallery/categories').get_json()
        self.assertEqual(counts['total'], 120)
        self.assertEqual({row['key']: row['count'] for row in counts['categories'] if row['count']}, TOTAL_COUNTS)
        self.assertEqual(len(self.client.get('/api/v1/gallery?category=kids').get_json()['items']), 30)

    def test_customer_and_legacy_prefixed_urls_are_preserved(self):
        path = self.uploads / 'legacy photo.jpg'
        path.write_bytes(b'legacy media bytes')
        expected = '/static/uploads/inspiration/legacy%20photo.jpg'
        for value in ('legacy photo.jpg', 'static/uploads/inspiration/legacy photo.jpg', expected):
            item = GalleryItem('Legacy', value)
            self.assertEqual(item.to_dict()['image_url'], expected)
            with self.client.get(expected) as response:
                self.assertEqual(response.data, path.read_bytes())
        for value in ('https://media.example.invalid/clip.MP4?version=1', '//media.example.invalid/photo.jpg'):
            self.assertEqual(gallery_media_url(value), value)
        self.assertEqual(GalleryItem('Clip', 'https://media.example.invalid/clip.MP4?version=1').media_type, 'video')
        unicode_path = 'gallery/it’s a cake.jpg'
        self.assertEqual(unquote(gallery_media_url(unicode_path)), '/static/uploads/' + unicode_path)
        self.assertEqual(self.client.get('/static/uploads/gallery/%2e%2e/%2e%2e/outside.jpg').status_code, 404)

    def test_video_order_selection_round_trips_and_deleted_ids_are_rejected(self):
        self.import_gallery()
        video = next(row for row in GalleryItem.query.all() if row.media_type == 'video')
        data = {'full_name': 'Video Customer', 'phone_number': '0780000000', 'event_type': 'birthday',
                'event_date': (date.today() + timedelta(days=30)).isoformat(), 'flavor': 'vanilla',
                'cake_size': '2kg', 'gallery_item_id': str(video.id)}
        with patch.object(orders_controller, 'send_order_email'), \
                patch.object(orders_controller, 'build_whatsapp_link', return_value='https://example.invalid/'), \
                patch.object(orders_controller, 'build_baker_to_customer_whatsapp_link', return_value='https://example.invalid/'):
            response = self.client.post('/api/v1/orders/create', data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.query.one().gallery_item_id, video.id)
        data['gallery_item_id'] = '2147483647'
        self.assertEqual(self.client.post('/api/v1/orders/create', data=data).status_code, 400)
        self.assertEqual(Order.query.count(), 1)

    def test_new_admin_images_use_gallery_subfolder_and_mp4_upload_is_still_rejected(self):
        image = ORIGINALS / 'spiderman.jpg'
        response = self.client.post('/api/v1/gallery/create', headers=self.headers, data={
            'title': 'Admin upload', 'category': 'kids', 'image': (io.BytesIO(image.read_bytes()), 'photo.jpg'),
        })
        self.assertEqual(response.status_code, 201)
        url = response.get_json()['item']['image_url']
        self.assertTrue(url.startswith('/static/uploads/gallery/'))
        self.assertTrue((self.uploads / 'gallery' / unquote(url.rsplit('/', 1)[-1])).is_file())
        response = self.client.post('/api/v1/gallery/create', headers=self.headers, data={
            'title': 'Not an authorized catalog import', 'image': (io.BytesIO(b'untrusted'), 'clip.mp4'),
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(GalleryItem.query.count(), 1)


class CatalogMigrationTests(unittest.TestCase):
    def test_additive_identity_migration_keeps_rows_media_and_order_foreign_keys(self):
        engine = sa.create_engine('sqlite:///:memory:')
        try:
            with engine.connect() as connection:
                connection.exec_driver_sql('PRAGMA foreign_keys=ON')
                connection.exec_driver_sql('CREATE TABLE gallery_items (id INTEGER PRIMARY KEY, title TEXT, image_url TEXT)')
                connection.exec_driver_sql('CREATE TABLE orders (id INTEGER PRIMARY KEY, gallery_item_id INTEGER REFERENCES gallery_items(id))')
                connection.exec_driver_sql("INSERT INTO gallery_items VALUES (1, 'Owner title', 'legacy.jpg')")
                connection.exec_driver_sql('INSERT INTO orders VALUES (1, 1)')
                connection.commit()
                migration = load_module('catalog_identity_migration', BACKEND / 'migrations' / 'versions' / '7c42e1f9a015_gallery_catalog_identity.py')
                context = MigrationContext.configure(connection)
                with Operations.context(context):
                    migration.upgrade()
                connection.commit()
                self.assertEqual(connection.exec_driver_sql('SELECT id, title, image_url, catalog_filename FROM gallery_items').all(),
                                 [(1, 'Owner title', 'legacy.jpg', None)])
                self.assertEqual(connection.exec_driver_sql('SELECT * FROM orders').all(), [(1, 1)])
                self.assertEqual(connection.exec_driver_sql('PRAGMA foreign_key_check').all(), [])
                self.assertIn('uq_gallery_catalog_filename', {row['name'] for row in sa.inspect(connection).get_indexes('gallery_items')})
                connection.commit()
                with Operations.context(context):
                    migration.downgrade()
                connection.commit()
                self.assertEqual(connection.exec_driver_sql('SELECT * FROM gallery_items').all(), [(1, 'Owner title', 'legacy.jpg')])
                self.assertEqual(connection.exec_driver_sql('SELECT * FROM orders').all(), [(1, 1)])
        finally:
            engine.dispose()


if __name__ == '__main__':
    unittest.main()
