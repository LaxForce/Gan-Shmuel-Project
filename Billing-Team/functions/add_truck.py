from sqlalchemy.orm import sessionmaker
from sql.billing_sql import Truck, engine

# Create a session maker bound to the engine
Session = sessionmaker(bind=engine)
session = Session()

def add_truck(data):
    provider_id = data.get('provider_id')
    id = data.get('id')
    
    if not id and provider_id:
        return {"error": "id and provider_id is required"}, 400

    try:
        # Create a new instance of the Providers class
        new_truck = Truck(id=id, provider_id=provider_id)

        # Add the new provider to the session
        session.add(new_truck)

        # Commit the transaction to persist the data
        session.commit()

        # Return the created provider details
        return {"id": new_truck.id, "provider id": new_truck.provider_id}, 201
    except Exception as e:
        # Rollback in case of an error
        session.rollback()
        return {"error": f"Failed to add truck: {str(e)}"}, 500


        