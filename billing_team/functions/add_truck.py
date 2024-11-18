from sqlalchemy.orm import sessionmaker
from sql.billing_sql import Truck, engine

# Create a session maker bound to the engine
Session = sessionmaker(bind=engine)
session = Session()

def add_truck(data):
    if data is None or not isinstance(data, dict):
        return {"error": "Invalid JSON or empty request body"}, 400

    provider_id = data.get('provider_id')
    id = data.get('id')
    
    if not id or not provider_id:  # Fixed logic to ensure both are required
        return {"error": "id and provider_id are required"}, 400

    try:
        # Create a new instance of the Truck class
        new_truck = Truck(id=id, provider_id=provider_id)

        # Add the new truck to the session
        session.add(new_truck)

        # Commit the transaction to persist the data
        session.commit()

        # Return the created truck details
        return {"id": new_truck.id, "provider id": new_truck.provider_id}, 201
    except Exception as e:
        # Rollback in case of an error
        session.rollback()
        return {"error": f"Failed to add truck: {str(e)}"}, 500
