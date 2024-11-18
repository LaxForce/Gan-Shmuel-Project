from sqlalchemy.orm import sessionmaker
from sql.billing_sql import Provider, Truck, Rates, engine
import requests
from flask import jsonify
from datetime import datetime
from functions.get_rates import get_rates_db  # Import get_rates_db function

# Create a session bound to the engine
Session = sessionmaker(bind=engine)
session = Session()

# Get Weight Microservice port dynamically
WEIGHT_TRUCK_PORT = os.getenv('WEIGHT_TRUCK_PORT', 5000)

def get_bill(id, query_params):
    # Validate if the provider exists in the database
    provider_exists = session.query(Provider).filter_by(id=id).first()
    if not provider_exists:
        return jsonify({"error": f"Provider ID {id} not found"}), 404

    # Extract query parameters or set defaults
    t1 = query_params.get('from') or datetime.now().replace(day=1, hour=0, minute=0, second=0).strftime("%Y%m%d%H%M%S")
    t2 = query_params.get('to') or datetime.now().strftime("%Y%m%d%H%M%S")

    # Calculate truck count for the provider within the time range
    truck_count = session.query(Truck).filter(Truck.provider_id == id).count()

    # Fetch sessions from the Weight Microservice
    try:
        sessions_response = requests.get(f"http://127.0.0.1:{WEIGHT_TRUCK_PORT}/api/weight?from={t1}&to={t2}&filter=in,out")
        sessions_response.raise_for_status()
        sessions_data = sessions_response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch sessions: {str(e)}"}), 500

    # Get rates for products using the provided function
    product_rates = get_rates_db()  # This will return the rates as a response (or you can store it as a dict)

    # Process sessions and products
    products = []
    total_pay = 0
    for session in sessions_data:
        product_id = session.get("produce", "na")
        # Retrieve rate for the product from the product_rates (which we got from get_rates_db())
        rate = find_rate_for_product(product_id, id, product_rates)  # Assuming product_rates is available as a list of dicts

        product = {
            "product": product_id,
            "count": len(session["containers"]),
            "amount": session.get("neto", 0),  # Net weight
            "rate": rate,
            "pay": rate * session.get("neto", 0)  # Calculate payment (rate * neto)
        }

        products.append(product)
        total_pay += product["pay"]

    # Return the bill data
    return jsonify({
        "id": id,
        "name": provider_exists.name,
        "from": t1,
        "to": t2,
        "truckCount": truck_count,  
        "sessionCount": len(sessions_data),
        "products": products,
        "total": total_pay
    })

# Function to find the rate for a product from the product_rates
def find_rate_for_product(product_id, provider_id, product_rates):
    # Filter the product rates to find those matching the product_id
    applicable_rates = [rate for rate in product_rates if rate['Product'] == product_id]

    # First, try to find the rate for the specific provider (most specific rate)
    for rate in applicable_rates:
        if rate['Scope'] == str(provider_id):  # If the rate is specific to the provider
            return rate['Rate']

    # If no provider-specific rate is found, use the general rate (Scope = "All")
    for rate in applicable_rates:
        if rate['Scope'] == "All":  # If the rate is general
            return rate['Rate']

    # Return 0 if no rate is found for the product
    return 0
