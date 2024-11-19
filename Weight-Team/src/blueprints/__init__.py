from flask import Blueprint
from .home import home_bp
from .health import health_bp
from .unknown import unknown_bp
from .batch_weight import batch_weight_bp
from .weight import weight_bp
from .item import item_bp
from .session import session_bp
from .trucks import trucks_bp
from .rec_weight import rec_weight_bp

def init_blueprints(app):
    # Register all blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(unknown_bp)
    app.register_blueprint(batch_weight_bp)
    app.register_blueprint(weight_bp)
    app.register_blueprint(item_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(trucks_bp)
    app.register_blueprint(rec_weight_bp)