from flask import Blueprint, request, jsonify
from functions import provider, truck, rates, billing, health

def setup_routes(app): 


    @app.route('/health', methods=['GET'])
    def health_check():
        status, code = health.check_health()
        return jsonify(status), code
