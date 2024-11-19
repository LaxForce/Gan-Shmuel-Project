from sqlalchemy.orm import sessionmaker
from sql.billing_sql import Providers, Truck, engine
from flask import jsonify, request
from datetime import datetime
import requests
import os

# Create a session bound to the engine
Session = sessionmaker(bind=engine)
session = Session()

# Get environment settings
WEIGHT_TRUCK_PORT = os.getenv('WEIGHT_TRUCK_PORT', 5002)

def get_bill(provider_id):
    # Validate if the provider exists
    provider = session.query(Providers).filter_by(id=provider_id).first()
    if not provider:
        return jsonify({"error": f"Provider ID {provider_id} not found"}), 404

    # Use query parameters directly from the request
    t1 = request.args.get('from', datetime.now().replace(day=1, hour=0, minute=0, second=0).strftime("%Y%m%d%H%M%S"))
    t2 = request.args.get('to', datetime.now().strftime("%Y%m%d%H%M%S"))
    filter_directions = request.args.get('filter', 'in,out,none')

    # Fetch trucks for the provider and their sessions
    trucks = session.query(Truck).filter(Truck.provider_id == provider_id).all()
    truck_ids = [truck.id for truck in trucks]

    # Fetch weight data for these trucks within the specified date range using the filter parameters
    try:
        response = requests.get(f"http://weights-trucks-app:{WEIGHT_TRUCK_PORT}/weight?from={t1}&to={t2}&filter={filter_directions}")
        response.raise_for_status()
        weight_data = response.json()
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch weight data: {str(e)}"}), 500

    # Filter the weight data to only include entries related to the provider's trucks
    relevant_data = [entry for entry in weight_data if entry['truck'] in truck_ids]

    # Aggregate weights by produce
    weights = {}
    for entry in relevant_data:
        produce = entry['produce']
        neto = entry.get('neto', 0)
        if produce not in weights:
            weights[produce] = 0
        weights[produce] += neto

    # Get rates and calculate payments
    rates = get_rates_db()  # Assume this fetches rate information from the database
    payments, total_pay = calculate_payments(weights, rates, provider_id)

    # Construct response
    return jsonify({
        "provider_id": provider_id,
        "name": provider.name,
        "from": t1,
        "to": t2,
        "truck_count": len(truck_ids),
        "session_count": len(relevant_data),
        "products": payments,
        "total": total_pay
    }), 200

def calculate_payments(weights, rates, provider_id):
    payments = []
    total_pay = 0
    for produce, weight in weights.items():
        rate = find_rate_for_product(produce, provider_id, rates)
        pay = rate * weight
        payments.append({
            "product": produce,
            "weight": weight,
            "rate": rate,
            "pay": pay
        })
        total_pay += pay
    return payments, total_pay

def find_rate_for_product(product_id, provider_id, product_rates):
    applicable_rates = [rate for rate in product_rates if rate['Product'] == product_id]
    for rate in applicable_rates:
        if rate['Scope'] == str(provider_id):
            return rate['Rate']
    for rate in applicable_rates:
        if rate['Scope'] == "All":
            return rate['Rate']
    return 0