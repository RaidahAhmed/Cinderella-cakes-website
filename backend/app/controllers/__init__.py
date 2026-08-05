from .orders.orders_controller import orders
from .gallery.gallery_controller import gallery
from .auth.auth_controller import auth
from .public_controller import public_bp
from .settings_controller import settings_bp
from .page_controller import page_bp
from .navigation_controller import navigation_bp
from .hero_controller import hero_bp
from .content_controller import content_bp
from .footer_controller import footer_bp
from .user_controller import user_bp
from .rbac_controller import rbac_bp

all_blueprints = [
    orders, 
    gallery, 
    auth,
    public_bp,
    settings_bp,
    page_bp,
    navigation_bp,
    hero_bp,
    content_bp,
    footer_bp,
    user_bp,
    rbac_bp
]
