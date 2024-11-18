from http.client import responses

from flask import Blueprint, request, jsonify, make_response

from functions.create_provider import create_provider
from functions.get_rates import get_rates_db
from functions.health_check import check_health
from functions.update_provider_name import update_provider_name  # Import your logic function
from functions.post_rates import getting_execl_data


# Define a Blueprint for provider-related routes
provider_bp = Blueprint('provider', __name__)

@provider_bp.route('/provider', methods=['POST'])
def provider():
    data = request.get_json()
    if data is None or not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON or empty request body"}), 400

    # Call create_provider function and handle its response
    provider, status_code = create_provider(data)
    return jsonify(provider), status_code


# Define a Blueprint for health-related routes
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health():
    # Call the health check function
    status, status_code = check_health()
    return jsonify(status), status_code

post_rates_bp = Blueprint('post_rates', __name__)

@provider_bp.route('/provider/<int:id>', methods=['PUT'])
def update_provider(id):
    provider_data = request.get_json()
    if not provider_data or "name" not in provider_data:
        return jsonify({"error": "Provider name is required"}), 400

    # Call the update_provider_name function
    return update_provider_name(id, provider_data["name"])
@post_rates_bp.route('/rates', methods=['POST'])
def post_rates():
    response = getting_execl_data(request.args.get('filename'))
    print(response)
    return response

get_rates_bp = Blueprint('get_rates', __name__)

@get_rates_bp.route('/rates', methods=['GET'])
def getting_execl_file():
    execl_file = get_rates_db()
    return execl_file

# Setup routes by registering the blueprint
def setup_routes(app):
    app.register_blueprint(provider_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(post_rates_bp)
    app.register_blueprint(get_rates_bp)
