from sql.billing_sql import session, Truck, Providers

def update_truck(truck_id, data):
    # Validate the input data
    provider_id = data.get('provider')
    if not provider_id:
        return {"error": "Provider ID is required"}, 400

    # Validate that the provider exists
    provider = session.query(Providers).get(provider_id)
    if not provider:
        return {"error": f"Provider with ID {provider_id} does not exist"}, 404

    # Find the truck and update it
    truck = session.query(Truck).get(truck_id)
    if not truck:
        return {"error": f"Truck with ID {truck_id} does not exist"}, 404

    try:
        truck.provider_id = provider_id
        session.commit()
        return {"id": truck.id, "provider_id": truck.provider_id}, 200
    except Exception as e:
        session.rollback()
        return {"error": f"Failed to update truck: {str(e)}"}, 500
