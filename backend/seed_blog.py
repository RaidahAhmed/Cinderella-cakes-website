# Adds the starter blog articles from data/blog_posts.json.
# Safe to run more than once: an article is skipped if its slug already exists,
# and nothing else in the database (accounts, orders, gallery) is changed.
#
# Run from the backend folder, after "flask db upgrade":
#     python seed_blog.py
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from app import create_app
from app.extensions import db
from app.models.blog import BlogPost, slugify

app = create_app(os.environ.get('FLASK_ENV', 'development'))

DATA_FILE = Path(__file__).resolve().parent / 'data' / 'blog_posts.json'


def seed_blog():
    with open(DATA_FILE, encoding='utf-8') as handle:
        articles = json.load(handle)

    added = 0
    with app.app_context():
        now = datetime.now()
        for index, article in enumerate(articles):
            slug = slugify(article['title'])
            if BlogPost.query.filter_by(slug=slug).first():
                continue
            # Stagger the dates so the list has a natural newest-first order.
            created = now - timedelta(days=index * 5)
            db.session.add(BlogPost(
                title=article['title'],
                slug=slug,
                category=article.get('category') or 'Cake notes',
                excerpt=article.get('excerpt'),
                content=article['content'],
                published=True,
                created_at=created,
                updated_at=created,
            ))
            added += 1
        db.session.commit()
    print(f'Blog seed finished: {added} new article(s) added, {len(articles) - added} already present.')


if __name__ == '__main__':
    seed_blog()
