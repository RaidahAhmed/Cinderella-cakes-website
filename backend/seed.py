#Seed script to populate the database with initial data for the Cinderella Cakes website. 
#This includes creating roles, permissions, a super admin user, site settings, navigation items, pages, content sections, footer links and gallery images.
import argparse
import hashlib
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit


def argument_parser():
    parser = argparse.ArgumentParser(description='Seed site data or import the local gallery catalog.')
    parser.add_argument('--gallery-only', action='store_true',
                        help='Import gallery only; never create or modify accounts or site settings.')
    parser.add_argument('--source-dir',
                        help='Original gallery directory; overrides GALLERY_SOURCE_DIR (relative to backend).')
    return parser


# Help exits before importing Flask, reading .env, or creating an application.
if __name__ == '__main__':
    arguments = argument_parser().parse_args()

from app import create_app
from app.extensions import db
from app.models.rbac import User, Role, Permission
from app.models.page import Page
from app.models.navigation import MenuItem
from app.models.hero import HeroSection
from app.models.content import ContentSection, ContentBlock
from app.models.footer import FooterColumn, FooterLink, SocialLink
from app.models.settings import SiteSettings
from app.models.gallery import GalleryItem, CATEGORY_CHOICES, gallery_media_url

app = create_app(os.environ.get('FLASK_ENV', 'development'))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Source folder holding the original cake photos shipped with the frontend.
GALLERY_SOURCE_DIR = os.path.normpath(
    os.path.join(BASE_DIR, '..', 'frontend', 'src', 'assets', 'gallery')
)
CATALOG_PATH = Path(BASE_DIR) / 'data' / 'gallery_catalog.json'

# Only the checked-in catalog can authorize the original trusted MP4.
GALLERY_IMAGE_EXTENSIONS = {'.jpg', '.mp4'}

INSTAGRAM_PREFIX = 'cinderella.cakes.ug_'

# Best-effort keyword mapping used to give imported photos a sensible category.
CATEGORY_KEYWORDS = [
    (('wedding', 'bridal'), 'wedding'),
    (('birthday', 'bday'), 'birthday'),
    (('baby', 'shower', 'gender'), 'baby'),
    (('grad',), 'graduation'),
    (('kid', 'character', 'spongebob'), 'kids'),
    (('cupcake', 'treat'), 'cupcakes'),
]


def _guess_category(filename):
    """Picks a gallery category from keywords in the file name."""
    name = filename.lower()
    for keywords, category in CATEGORY_KEYWORDS:
        if any(keyword in name for keyword in keywords):
            return category
    return 'other'


def _build_title(filename):
    """Turns a file name into a readable title.

    Instagram-style exports become 'Cake Design - <Month Year>'; anything else
    is humanised from the file name.
    """
    stem = os.path.splitext(filename)[0]

    if stem.startswith(INSTAGRAM_PREFIX):
        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', stem)
        if date_match:
            try:
                post_date = datetime.strptime(date_match.group(0), '%Y-%m-%d')
                return f'Cake Design - {post_date.strftime("%B %Y")}'
            except ValueError:
                pass
        return 'Cake Design'

    pretty = re.sub(r'[^A-Za-z0-9]+', ' ', stem).strip()
    if not pretty or pretty.isdigit():
        return 'Cake Design'
    return pretty.title()[:150]


def _safe_stem(stem, limit=180):
    """Keeps the stored file name URL-safe (emoji and spaces are stripped).

    The limit is generous so that Instagram-style names stay unique and the
    idempotency check below never confuses two different photos.
    """
    cleaned = re.sub(r'[^A-Za-z0-9._-]+', '_', stem).strip('_')
    return (cleaned or 'cake')[:limit]


#Copies the bundled cake photos into the uploads folder and registers them in the gallery.
#It is safe to re-run: images that were already imported are skipped.
def load_gallery_catalog():
    """Read local metadata only; no reference-site or external-media requests."""
    try:
        catalog = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
        entries = catalog['items']
        if catalog['version'] != 1 or catalog['expected_count'] != 120 or len(entries) != 120:
            raise ValueError('Expected catalog version 1 and all 120 originals')
        seen = set()
        for entry in entries:
            name = entry['filename']
            if (not isinstance(name, str) or not name or len(name) > 240
                    or any(c in name for c in '/\\:\x00') or name in ('.', '..')
                    or name in seen or Path(name).suffix.lower() not in GALLERY_IMAGE_EXTENSIONS):
                raise ValueError(f'Unsafe or duplicate catalog filename: {name!r}')
            seen.add(name)
            if not isinstance(entry['title'], str) or not 1 <= len(entry['title'].strip()) <= 150:
                raise ValueError(f'Invalid title: {name}')
            if entry['category'] not in CATEGORY_CHOICES or entry['source'] not in catalog['sources']:
                raise ValueError(f'Invalid category or provenance: {name}')
            if entry['media_type'] != ('video' if name.lower().endswith('.mp4') else 'image'):
                raise ValueError(f'Invalid media type: {name}')
        return sorted(entries, key=lambda entry: entry['filename'])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(f'Invalid gallery catalog at {CATALOG_PATH}: {exc}') from exc


def preflight_gallery_source(source_dir=None):
    entries = load_gallery_catalog()
    configured = source_dir or app.config.get('GALLERY_SOURCE_DIR') or GALLERY_SOURCE_DIR
    root = Path(configured).expanduser()
    if not root.is_absolute():
        root = Path(BASE_DIR) / root
    root = root.resolve()
    if not root.is_dir():
        raise RuntimeError(f'Gallery source directory not found: {root}. Set GALLERY_SOURCE_DIR.')
    for entry in entries:
        source = root / entry['filename']
        if source.is_symlink() or not source.is_file() or source.stat().st_size == 0:
            raise RuntimeError(f'Gallery source missing, empty, or unsafe: {source}')
        with source.open('rb') as stream:
            if not stream.read(1):
                raise RuntimeError(f'Gallery source is unreadable: {source}')
    return root, entries


def _legacy_match(item, filename):
    name = Path(unquote(urlsplit((item.image_url or '').replace('\\', '/')).path)).name
    stem, suffix = os.path.splitext(filename)
    old_name = _safe_stem(stem) + suffix.lower()
    return name in (filename, old_name) or any(
        re.fullmatch(r'gallery_[0-9a-fA-F]{32}_' + re.escape(candidate), name)
        for candidate in (filename, old_name)
    )


def _local_destination(stored_url, upload_root):
    url = gallery_media_url(stored_url)
    if not url or urlsplit(url).netloc:
        return None
    path = unquote(urlsplit(url).path)
    for prefix, directory in (
        ('/static/uploads/gallery/', upload_root / 'gallery'),
        ('/static/uploads/inspiration/', upload_root),
    ):
        if path.startswith(prefix):
            destination = directory / path[len(prefix):]
            if destination.is_symlink() or not destination.resolve().is_relative_to(directory.resolve()):
                raise RuntimeError(f'Unsafe gallery destination: {stored_url}')
            return destination
    raise RuntimeError(f'Unrecognized gallery media path: {stored_url}')


def _digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.digest()


def seed_gallery_images(source_dir=None):
    """Stage every copy before one DB transaction; never rewrite administrator metadata."""
    root, entries = preflight_gallery_source(source_dir)
    with app.app_context():
        try:
            upload_root = Path(app.config['UPLOAD_FOLDER']).resolve()
            gallery_root = upload_root / 'gallery'
            if gallery_root.is_symlink():
                raise RuntimeError('Gallery upload directory must not be a symlink.')
            existing_items = GalleryItem.query.order_by(GalleryItem.id).all()
            prepared = []
            claimed = set()
            for entry in entries:
                name = entry['filename']
                matches = [item for item in existing_items if item.catalog_filename == name
                           or (item.catalog_filename is None and _legacy_match(item, name))]
                if len(matches) > 1 or (matches and matches[0].id in claimed):
                    raise RuntimeError(f'Ambiguous previous gallery imports for {name}; review without deleting rows.')
                item = matches[0] if matches else None
                if item:
                    claimed.add(item.id)
                stored = item.image_url if item else 'gallery/' + name
                destination = _local_destination(stored, upload_root)
                prepared.append((entry, item, stored, destination))

            # Copy/read failures cannot leave partially imported rows. Existing files are never overwritten.
            with TemporaryDirectory(prefix='cinderella-gallery-') as staging:
                copies = []
                for index, (entry, item, stored, destination) in enumerate(prepared):
                    if destination is None:
                        continue
                    source = root / entry['filename']
                    if destination.exists():
                        if not destination.is_file() or destination.stat().st_size == 0:
                            raise RuntimeError(f'Existing gallery media is empty or invalid: {destination}')
                        if item is None and _digest(source) != _digest(destination):
                            raise RuntimeError(f'Gallery destination conflict; not overwriting: {destination}')
                        continue
                    staged = Path(staging) / str(index)
                    shutil.copy2(source, staged)
                    if _digest(staged) != _digest(source):
                        raise RuntimeError(f'Gallery copy verification failed: {source}')
                    copies.append((staged, destination))
                for staged, destination in copies:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with destination.open('xb') as target, staged.open('rb') as source:
                        shutil.copyfileobj(source, target)
                    if _digest(staged) != _digest(destination):
                        raise RuntimeError(f'Gallery copy verification failed: {destination}')

            created = curated = 0
            for entry, item, stored, destination in prepared:
                if item is None:
                    item = GalleryItem(title=entry['title'], image_url=stored, category=entry['category'])
                    db.session.add(item)
                    created += 1
                elif item.catalog_filename is None:
                    # Only the complete untouched legacy tuple is eligible for one-time curation.
                    if (item.title == _build_title(entry['filename'])
                            and item.category == _guess_category(entry['filename'])
                            and not item.description):
                        item.title = entry['title']
                        item.category = entry['category']
                        curated += 1
                item.catalog_filename = entry['filename']
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            raise RuntimeError(f'Gallery import failed; database changes rolled back: {exc}') from exc
        result = {'total': len(entries), 'created': created, 'curated': curated,
                  'preserved': len(entries) - created - curated}
        print(f'Gallery import complete: {result}')
        return result


ADMIN_EMAIL = 'cinderellacakes2@gmail.com'
LEGACY_ADMIN_EMAIL = 'admin@cinderellacakes.com'


def _prepare_admin_user():
    """Resolve identity and credentials before making any database changes."""
    users = User.query.all()
    candidates = [
        user for user in users
        if user.email.strip().lower() in (ADMIN_EMAIL, LEGACY_ADMIN_EMAIL)
        or (user.role and user.role.name in ('admin', 'super_admin'))
    ]
    if len(candidates) > 1:
        raise RuntimeError(
            'Ambiguous admin accounts. Resolve the canonical admin and email collision '
            'manually before seeding; no accounts were changed.'
        )
    if candidates:
        user = candidates[0]
        if not user.role or user.role.name not in ('admin', 'super_admin'):
            raise RuntimeError('The admin email belongs to a non-admin account; seeding stopped.')
        if not user.password_hash:
            raise RuntimeError('The existing admin has no password hash; seeding will not reset it.')
        return user
    if users:
        raise RuntimeError('No unambiguous existing admin found; seeding will not create a competing account.')

    password = os.environ.get('ADMIN_INITIAL_PASSWORD')
    if not password or not password.strip():
        raise RuntimeError('ADMIN_INITIAL_PASSWORD must be explicitly set to initialize an empty user database.')
    user = User(email=ADMIN_EMAIL, first_name='Admin', last_name='User')
    user.set_password(password)
    return user


def _seed_admin_settings():
    """Commit account, role, permission, and contact changes atomically."""
    try:
        admin_user = _prepare_admin_user()
        is_new_admin = admin_user.id is None

        # 1. Create permissions
        perms = [
            'content_read', 'content_write',
            'orders_read', 'orders_write',
            'gallery_read', 'gallery_write'
        ]

        #This loop checks if each permission already exists in the database. 
        #If not, it creates a new Permission object and adds it to the session.
        permission_objs = []
        for p_name in perms:
            perm = Permission.query.filter_by(name=p_name).first()
            if not perm:
                perm = Permission(name=p_name, description=f"Can {p_name.replace('_', ' ')}")
                db.session.add(perm)
            permission_objs.append(perm)

        db.session.flush()

        # 2. Create roles
        #This section checks for the existence of 'super_admin' and 'admin' roles.
        #If they don't exist, it creates them and assigns the appropriate permissions.
        super_admin_role = Role.query.filter_by(name='super_admin').first()
        if not super_admin_role:
            super_admin_role = Role(name='super_admin', description='Full access to everything')
            db.session.add(super_admin_role)
            
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin', description='Can manage content, gallery and orders')
            admin_role.permissions = permission_objs
            db.session.add(admin_role)

        db.session.flush()

        # 3. Create super admin user
        #This makes sure the bakery's super admin account exists.
        if is_new_admin:
            admin_user.role = super_admin_role
            db.session.add(admin_user)
        admin_user.email = ADMIN_EMAIL

        # 4. Site Settings
        #This checks if site settings like site name, contact information, etc. exist. 
        #If not, it creates default settings for the website.
        existing_settings = SiteSettings.query.all()
        if not existing_settings:
            settings = SiteSettings(
                site_name="Cinderella Cakes",
                contact_email=ADMIN_EMAIL,
                contact_phone="+256 781 470 984",
                address="123 Bakery Lane, Sweet City",
                primary_color="#8B3FA0",
                secondary_color="#2FBFC0"
            )
            db.session.add(settings)
        else:
            for settings in existing_settings:
                settings.contact_email = ADMIN_EMAIL
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


#This function seeds the database with all initial data for roles, permissions, users e.t.c
def seed(source_dir=None):
    preflight_gallery_source(source_dir)
    with app.app_context(): #adds the application context to allow database operations
        _seed_admin_settings()

        # 5. Navigation
        #This checks if there are any existing navigation menu items.
        #If none exist, it creates a default set of menu items for the website's main navigation bar.
        if MenuItem.query.count() == 0:
            nav_items = [
                MenuItem(label="Home", url="/", order=1),
                MenuItem(label="About", url="/about", order=2),
                MenuItem(label="Gallery", url="/gallery", order=3),
                MenuItem(label="Contact", url="/contact", order=4),
                MenuItem(label="Order Now", url="/order", order=5, is_button=True)
            ]
            db.session.add_all(nav_items)
            db.session.commit()

        # 6. Pages & Content
        if Page.query.count() == 0:
            # HOME PAGE
            home = Page(slug="home", title="Cinderella Cakes", meta_description="Bespoke Bakery for all your cake dreams")
            db.session.add(home)
            db.session.commit()
            
            home_hero = HeroSection(
                page_id=home.id,
                eyebrow="Bespoke Bakery",
                heading="We bake your cake",
                heading_accent="dreams",
                subheading="Every occasion deserves a special cake. We specialize in custom designs, from elegant weddings to playful birthdays.",
                primary_button_text="Order Now",
                primary_button_url="/order",
                secondary_button_text="View Gallery",
                secondary_button_url="/gallery"
            )
            db.session.add(home_hero)
            
            features = ContentSection(page_id=home.id, section_type="feature_grid", order=1, eyebrow="Why Choose Us", heading="Crafted with Love & Detail")
            db.session.add(features)
            db.session.commit()
            
            db.session.add_all([
                ContentBlock(section_id=features.id, order=1, title="Premium Ingredients", text="We only use the finest chocolate, real butter, and fresh local produce."),
                ContentBlock(section_id=features.id, order=2, title="Custom Designs", text="If you can dream it, we can bake it. Our decorators are true artists.")
            ])
            
            # ABOUT PAGE
            about = Page(slug="about", title="Our Story", meta_description="Learn more about Cinderella Cakes")
            db.session.add(about)
            db.session.commit()
            
            about_hero = HeroSection(page_id=about.id, eyebrow="About Us", heading="Baking memories since", heading_accent="2018")
            db.session.add(about_hero)
            
            db.session.commit()

        # 7. Footer
        if FooterColumn.query.count() == 0:
            col1 = FooterColumn(title="Quick Links", order=1)
            db.session.add(col1)
            db.session.commit()
            
            db.session.add_all([
                FooterLink(column_id=col1.id, label="Home", url="/", order=1),
                FooterLink(column_id=col1.id, label="Order", url="/order", order=2),
                FooterLink(column_id=col1.id, label="Gallery", url="/gallery", order=3)
            ])
            db.session.commit()
            
            db.session.add_all([
                SocialLink(platform="instagram", url="#", icon_class="instagram"),
                SocialLink(platform="facebook", url="#", icon_class="facebook")
            ])
            db.session.commit()

    # 8. Gallery images bundled with the frontend
    seed_gallery_images(source_dir)
    print("Database seeded successfully!")

if __name__ == '__main__':
    try:
        if arguments.gallery_only:
            seed_gallery_images(arguments.source_dir)
        else:
            seed(arguments.source_dir)
    except (RuntimeError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
