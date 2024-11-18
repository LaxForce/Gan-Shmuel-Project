from flask import Blueprint, request, jsonify
from functions.create_provider import create_provider
from functions.add_truck import add_truck

# Define a Blueprint for provider-related routes
provider_bp = Blueprint('provider', __name__)

@provider_bp.route('/provider', methods=['POST'])
def provider():
    # Pass the request JSON directly to the create_provider function
    return create_provider(request.get_json())

@provider_bp.route('/truck', methods=['POST'])
def truck():
    # Pass the request JSON directly to the add_truck function
    return add_truck(request.get_json())

# Setup routes by registering the blueprint
def setup_routes(app):
    app.register_blueprint(provider_bp)
