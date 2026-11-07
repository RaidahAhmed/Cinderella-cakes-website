#Seed script to populate the database with initial data for the Cinderella Cakes website. 
#This includes creating roles, permissions, a super admin user, site settings, navigation items, pages, content sections, and footer links.
import os
from app import create_app
from app.extensions import db
from app.models.rbac import User, Role, Permission
from app.models.page import Page
from app.models.navigation import MenuItem
from app.models.hero import HeroSection
from app.models.content import ContentSection, ContentBlock
from app.models.footer import FooterColumn, FooterLink, SocialLink
from app.models.settings import SiteSettings
from app.models.gallery import GalleryItem

app = create_app(os.environ.get('FLASK_ENV', 'development'))

#This function seeds the database with all initial data for roles, permissions, users e.t.c
def seed():
    with app.app_context(): #adds the application context to allow database operations
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
            
        db.session.commit()

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
            
        db.session.commit()

        # 3. Create super admin user
        #This creates a super admin user with a default email and password.
        # Migrate existing admin to new email if needed
        old_admin = User.query.filter_by(email='admin@cinderellacakes.com').first()
        if old_admin:
            old_admin.email = 'cinderellacakes2@gmail.com'
            db.session.commit()
            print("Migrated admin email to cinderellacakes2@gmail.com")

        admin_user = User.query.filter_by(email='cinderellacakes2@gmail.com').first()
        if not admin_user:
            admin_user = User(
                email='cinderellacakes2@gmail.com',
                first_name='Admin',
                last_name='User',
                role=super_admin_role
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Created super admin: cinderellacakes2@gmail.com / admin123")

        # 4. Site Settings
        #This checks if site settings like site name, contact information, etc. exist. 
        #If not, it creates default settings for the website.
        if not SiteSettings.query.first():
            settings = SiteSettings(
                site_name="Cinderella Cakes",
                contact_email="hello@cinderellacakes.com",
                contact_phone="+256 781 470 984",
                address="123 Bakery Lane, Sweet City",
                primary_color="#8B3FA0",
                secondary_color="#2FBFC0"
            )
            db.session.add(settings)
            db.session.commit()

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

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed()
