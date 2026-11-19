"""Blog API and gallery detail ("More like this") tests: isolated SQLite, no external services."""
import io
import json
import os
import secrets
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from flask_jwt_extended import create_access_token

# Importing the application must not read a developer's private .env file.
with patch('dotenv.load_dotenv', return_value=False):
    from app.controllers.blog_controller import blog_bp
    from app.controllers.gallery.gallery_controller import gallery
    from app.extensions import bcrypt, db, jwt
    from app.models.blog import BlogPost, slugify
    from app.models.gallery import GalleryItem

BACKEND = Path(__file__).resolve().parents[1]


class BlogAndDetailCase(unittest.TestCase):
    def setUp(self):
        self.uploads = tempfile.TemporaryDirectory()
        self.app = Flask('blog_detail_' + secrets.token_hex(6), static_folder=None)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SECRET_KEY=secrets.token_urlsafe(48),
            JWT_SECRET_KEY=secrets.token_urlsafe(48),
            BCRYPT_LOG_ROUNDS=4,
            UPLOAD_FOLDER=self.uploads.name,
        )
        db.init_app(self.app)
        bcrypt.init_app(self.app)
        jwt.init_app(self.app)
        self.app.register_blueprint(blog_bp)
        self.app.register_blueprint(gallery)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()
        token = create_access_token(
            identity='blog-verifier',
            additional_claims={'permissions': ['content_write'], 'roles': []},
        )
        self.admin = {'Authorization': f'Bearer {token}'}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()
        self.uploads.cleanup()

    def create_post(self, **fields):
        data = {'title': 'How to plan a cake', 'content': 'First paragraph.\n\nSecond one.'}
        data.update(fields)
        return self.client.post(
            '/api/v1/blog/admin', data=data, headers=self.admin,
            content_type='multipart/form-data',
        )

    # ---------- gallery detail ----------

    def test_gallery_detail_returns_story_and_same_category_related(self):
        first = GalleryItem('Rose cake', 'a.jpg', 'A soft rose story', 'birthday')
        second = GalleryItem('Gold cake', 'b.jpg', None, 'birthday')
        other = GalleryItem('Castle cake', 'c.jpg', None, 'kids')
        db.session.add_all([first, second, other])
        db.session.commit()

        response = self.client.get(f'/api/v1/gallery/{first.id}')
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body['item']['title'], 'Rose cake')
        self.assertEqual(body['item']['description'], 'A soft rose story')
        self.assertEqual(body['category_label'], 'Birthday')
        self.assertEqual([entry['title'] for entry in body['related']], ['Gold cake'])

    def test_gallery_detail_unknown_id_is_404(self):
        self.assertEqual(self.client.get('/api/v1/gallery/9999').status_code, 404)

    def test_gallery_categories_route_still_works(self):
        db.session.add(GalleryItem('Rose cake', 'a.jpg', None, 'birthday'))
        db.session.commit()
        response = self.client.get('/api/v1/gallery/categories')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['success'])

    # ---------- blog ----------

    def test_blog_admin_routes_need_a_login(self):
        self.assertEqual(self.client.post('/api/v1/blog/admin', data={'title': 'x'}).status_code, 401)
        self.assertEqual(self.client.get('/api/v1/blog/admin/all').status_code, 401)
        self.assertEqual(self.client.delete('/api/v1/blog/admin/1').status_code, 401)

    def test_blog_admin_routes_need_content_write(self):
        token = create_access_token(identity='reader', additional_claims={'permissions': ['content_read']})
        response = self.client.get('/api/v1/blog/admin/all', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(response.status_code, 403)

    def test_create_requires_title_and_content(self):
        self.assertEqual(self.create_post(title='  ').status_code, 400)
        self.assertEqual(self.create_post(content='   ').status_code, 400)

    def test_create_publish_read_and_slug_uniqueness(self):
        first = self.create_post()
        second = self.create_post()
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        slugs = [first.get_json()['post']['slug'], second.get_json()['post']['slug']]
        self.assertEqual(slugs, ['how-to-plan-a-cake', 'how-to-plan-a-cake-2'])

        listing = self.client.get('/api/v1/blog').get_json()
        self.assertEqual(listing['total'], 2)
        self.assertNotIn('content', listing['posts'][0])  # the list stays light

        detail = self.client.get('/api/v1/blog/how-to-plan-a-cake').get_json()
        self.assertIn('Second one.', detail['post']['content'])
        self.assertEqual(len(detail['more']), 1)

    def test_drafts_are_hidden_from_visitors_but_not_from_admin(self):
        created = self.create_post(published='false').get_json()['post']
        self.assertFalse(created['published'])

        self.assertEqual(self.client.get('/api/v1/blog').get_json()['total'], 0)
        self.assertEqual(self.client.get(f"/api/v1/blog/{created['slug']}").status_code, 404)
        admin_view = self.client.get('/api/v1/blog/admin/all', headers=self.admin).get_json()
        self.assertEqual(admin_view['total'], 1)

        publish = self.client.put(
            f"/api/v1/blog/admin/{created['id']}", data={'published': 'true'},
            headers=self.admin, content_type='multipart/form-data',
        )
        self.assertEqual(publish.status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/blog/{created['slug']}").status_code, 200)

    def test_update_changes_text_but_keeps_the_shared_link(self):
        created = self.create_post().get_json()['post']
        response = self.client.put(
            f"/api/v1/blog/admin/{created['id']}",
            data={'title': 'A brand new title', 'excerpt': 'Short and sweet'},
            headers=self.admin, content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 200)
        post = response.get_json()['post']
        self.assertEqual(post['title'], 'A brand new title')
        self.assertEqual(post['excerpt'], 'Short and sweet')
        self.assertEqual(post['slug'], created['slug'])

        empty = self.client.put(
            f"/api/v1/blog/admin/{created['id']}", data={'title': ' '},
            headers=self.admin, content_type='multipart/form-data',
        )
        self.assertEqual(empty.status_code, 400)

    def test_cover_image_upload_replace_and_delete_clean_up_files(self):
        blog_folder = Path(self.uploads.name) / 'blog'
        created = self.client.post(
            '/api/v1/blog/admin',
            data={'title': 'With a picture', 'content': 'Body text.',
                  'cover': (io.BytesIO(b'fake-image-bytes'), 'cover.png')},
            headers=self.admin, content_type='multipart/form-data',
        )
        self.assertEqual(created.status_code, 201)
        post = created.get_json()['post']
        self.assertTrue(post['cover_image_url'].startswith('/static/uploads/blog/'))
        self.assertEqual(len(list(blog_folder.iterdir())), 1)

        replaced = self.client.put(
            f"/api/v1/blog/admin/{post['id']}",
            data={'cover': (io.BytesIO(b'newer-bytes'), 'newer.jpg')},
            headers=self.admin, content_type='multipart/form-data',
        )
        self.assertEqual(replaced.status_code, 200)
        self.assertEqual(len(list(blog_folder.iterdir())), 1)  # the old file was removed

        deleted = self.client.delete(f"/api/v1/blog/admin/{post['id']}", headers=self.admin)
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(list(blog_folder.iterdir()), [])
        self.assertEqual(self.client.get(f"/api/v1/blog/{post['slug']}").status_code, 404)

    def test_cover_image_rejects_other_file_types(self):
        response = self.client.post(
            '/api/v1/blog/admin',
            data={'title': 'Bad cover', 'content': 'Body.', 'cover': (io.BytesIO(b'<script>'), 'cover.html')},
            headers=self.admin, content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(BlogPost.query.count(), 0)

    def test_starter_articles_file_is_valid_and_slugs_are_unique(self):
        articles = json.loads((BACKEND / 'data' / 'blog_posts.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(articles), 1)
        slugs = [slugify(article['title']) for article in articles]
        self.assertEqual(len(slugs), len(set(slugs)))
        for article in articles:
            self.assertTrue(article['title'].strip())
            self.assertTrue(article['content'].strip())
            self.assertLessEqual(len(article.get('excerpt', '')), 400)


if __name__ == '__main__':
    unittest.main()
