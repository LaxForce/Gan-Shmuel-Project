import os
import requests

from sqlalchemy.orm import sessionmaker
from sql.billing_sql import Truck, engine
from flask import jsonify
from datetime import datetime

# Create a session bound to the engine
Session = sessionmaker(bind=engine)
session = Session()

# Get Weight Microservice port dynamically
WEIGHT_TRUCK_PORT = os.getenv('WEIGHT_TRUCK_PORT', 5002)  # Default to 5000 if not set

def fetch_truck_details(truck_id, query_params):
    # Validate if the truck exists in the database
    truck_exists = session.query(Truck).filter_by(id=truck_id).first()
    if not truck_exists:
        return jsonify({"error": f"Truck ID {truck_id} not found"}), 404

    # Extract query parameters or set defaults
    t1 = query_params.get('from') or datetime.now().replace(day=1, hour=0, minute=0, second=0).strftime("%Y%m%d%H%M%S")
    t2 = query_params.get('to') or datetime.now().strftime("%Y%m%d%H%M%S")
    f = query_params.get('f') or 'in/out/none'

    # Fetch tara from the Weight Microservice
    try:
        tara_response = requests.get(f"http://weights-trucks-app:{WEIGHT_TRUCK_PORT}/item/{truck_id}")
        tara_response.raise_for_status()
        tara = tara_response.json().get("tara", "na")
        session_id = tara_response.json().get("sessions", "na")
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch tara: {str(e)}"}), 500

    # # Fetch sessions from the Weight Microservice
    # try:
    #     sessions_response = requests.get(f"http://weights-trucks-app:{WEIGHT_TRUCK_PORT}/weight?from={t1}&to={t2}&filter={f}")
    #     sessions_response.raise_for_status()
    #     session_ids = [session["id"] for session in sessions_response.json()]
    # except requests.exceptions.RequestException as e:
    #     return jsonify({"error": f"Failed to fetch sessions: {str(e)}"}), 500

    # Combine and return the data
    return jsonify({
        "id": truck_id,
        "tara": tara,
        "sessions": session_id
    })
