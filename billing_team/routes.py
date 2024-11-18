from flask import Blueprint, request
from functions.create_provider import create_provider
from functions.get_rates import get_rates_db
from functions.health_check import check_health
from functions.update_provider_name import update_provider_name  # Import your logic function
from functions.post_rates import getting_execl_data
from functions.update_truck import update_truck
from functions.add_truck import add_truck
from functions.get_truck import fetch_truck_details


provider_bp = Blueprint('provider', __name__)

@provider_bp.route('/provider', methods=['POST'])
def provider():
    return create_provider(request.get_json())

truck_bp = Blueprint('truck', __name__)

@truck_bp.route('/truck', methods=['POST'])
def post_truck():
    return add_truck(request.get_json())

@truck_bp.route('/truck/<id>', methods=['GET'])
def get_truck(id):
    return fetch_truck_details(id, request.args)

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health():
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
    return getting_execl_data(request.args.get('filename'))

get_rates_bp = Blueprint('get_rates', __name__)

@get_rates_bp.route('/rates', methods=['GET'])
def get_rates():
    return get_rates_db()


truck_bp = Blueprint('truck', __name__)

@truck_bp.route('/truck/<string:truck_id>', methods=['PUT'])
def modify_truck(truck_id):
    # Parse the request JSON
    data = request.get_json()
    if data is None or not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON or empty request body"}), 400

    # Call the update_truck function
    response, status_code = update_truck(truck_id, data)
    return jsonify(response), status_code

# Setup routes by registering the blueprint

def setup_routes(app):
    app.register_blueprint(provider_bp)
    app.register_blueprint(truck_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(post_rates_bp)
    app.register_blueprint(get_rates_bp)
    app.register_blueprint(truck_bp)
    app.register_blueprint(get_rates_bp)

