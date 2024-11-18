import os
from sqlalchemy.orm import sessionmaker
from sql.billing_sql import Truck, engine
import requests
from flask import jsonify
from datetime import datetime

# Create a session bound to the engine
Session = sessionmaker(bind=engine)
session = Session()

# Get Weight Microservice port dynamically
WEIGHT_TRUCK_PORT = os.getenv('WEIGHT_TRUCK_PORT', 5000)  # Default to 5000 if not set

def fetch_truck_details(truck_id, query_params):
    # Validate if the truck exists in the database
    truck_exists = session.query(Truck).filter_by(id=truck_id).first()
    if not truck_exists:
        return jsonify({"error": f"Truck ID {truck_id} not found"}), 404

    # Extract query parameters or set defaults
    t1 = query_params.get('from') or datetime.now().replace(day=1, hour=0, minute=0, second=0).strftime("%Y%m%d%H%M%S")
    t2 = query_params.get('to') or datetime.now().strftime("%Y%m%d%H%M%S")

    # Fetch tara from the Weight Microservice
    try:
        tara_response = requests.get(f"http://127.0.0.1:{WEIGHT_TRUCK_PORT}/api/item/{truck_id}")
        tara_response.raise_for_status()
        tara = tara_response.json().get("tara", "na")
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch tara: {str(e)}"}), 500

    # Fetch sessions from the Weight Microservice
    try:
        sessions_response = requests.get(f"http://127.0.0.1:{WEIGHT_TRUCK_PORT}/api/weight?from={t1}&to={t2}&filter=in,out")
        sessions_response.raise_for_status()
        session_ids = [session["id"] for session in sessions_response.json()]
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch sessions: {str(e)}"}), 500

    # Combine and return the data
    return jsonify({
        "id": truck_id,
        "tara": tara,
        "sessions": session_ids
    })
