
from flask import Blueprint
from .routes import monitor_bp

def init_monitoring(app, sock):
    app.register_blueprint(monitor_bp)
    monitor_bp.sock = sock
    print(f"Blueprint registered with WebSocket. Available routes: {[rule.rule for rule in app.url_map.iter_rules() if rule.rule.startswith('/monitoring')]}")
