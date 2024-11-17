# routes.py
from flask import Blueprint, request, jsonify
from functions.create_provider import create_provider

provder_bp = Blueprint('provider', __name__)

@provder_bp.route('/provide', methods=['POST'])
def provide():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON or empty request body"}), 400

    provider, status_code = create_provider(data)
    return jsonify(provider), status_code

def setup_routes(app):
    app.register_blueprint(provder_bp)