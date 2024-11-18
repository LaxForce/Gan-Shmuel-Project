from sql.billing_sql import session, Truck

def update_truck(truck_id, data):
    # Get the new provider ID from the request
    new_provider_id = data.get('provider_id')

    # Validate that the new provider ID is provided
    if not new_provider_id:
        return {"error": "New Provider ID is required"}, 400

    # Find the truck by its ID
    truck = session.query(Truck).get(truck_id)
    if not truck:
        return {"error": f"Truck with ID {truck_id} does not exist"}, 404

    try:
        # Update the truck's provider_id
        truck.provider_id = new_provider_id

        # Commit the changes to the database
        session.commit()
        return {"id": truck.id, "provider_id": truck.provider_id}, 200
    except Exception as e:
        # Rollback in case of an error
        session.rollback()
        return {"error": f"Failed to update truck provider: {str(e)}"}, 500
