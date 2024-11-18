from flask import Blueprint, request, jsonify

from functions.create_provider import create_provider
from functions.get_rates import get_rates_db
from functions.health_check import check_health
from functions.post_rates import getting_execl_data
from functions.add_truck import add_truck

# Define a Blueprint for provider-related routes
provider_bp = Blueprint('provider', __name__)

@provider_bp.route('/provider', methods=['POST'])
def provider():
    return create_provider(request.get_json())

# Define a Blueprint for truck-related routes
truck_bp = Blueprint('truck', __name__)

@truck_bp.route('/truck', methods=['POST'])
def truck():
    return add_truck(request.get_json())

# Define a Blueprint for health-related routes
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health():
    # Call the health check function
    status, status_code = check_health()
    return jsonify(status), status_code

# Define a Blueprint for rates-related routes (POST)
post_rates_bp = Blueprint('post_rates', __name__)

@post_rates_bp.route('/rates', methods=['POST'])
def post_rates():
    response = getting_execl_data(request.args.get('filename'))
    print(response)
    return response

# Define a Blueprint for rates-related routes (GET)
get_rates_bp = Blueprint('get_rates', __name__)

@get_rates_bp.route('/rates', methods=['GET'])
def getting_execl_file():
    execl_file = get_rates_db()
    return execl_file

# Setup routes by registering the blueprints
def setup_routes(app):
    app.register_blueprint(provider_bp)
    app.register_blueprint(truck_bp)       # Register truck blueprint
    app.register_blueprint(health_bp)
    app.register_blueprint(post_rates_bp)
    app.register_blueprint(get_rates_bp)
