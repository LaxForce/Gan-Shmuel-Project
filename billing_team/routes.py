from flask import Blueprint, request, jsonify
from functions import post_rates

app = Flask(__name__)

@app.route('/rates', methods=['GET', 'POST'])
def update_rates():


def setup_routes(app):