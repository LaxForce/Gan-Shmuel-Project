from sqlalchemy.orm import sessionmaker
from sql.billing_sql import Providers, engine

# Create a session maker bound to the engine
Session = sessionmaker(bind=engine)
session = Session()

def create_provider(data):
    name = data.get('name')
    if not name:
        return {"error": "Name is required"}, 400

    try:
        # Create a new instance of the Providers class
        new_provider = Providers(name=name)

        # Add the new provider to the session
        session.add(new_provider)

        # Commit the transaction to persist the data
        session.commit()

        # Return the created provider details
        return {"id": new_provider.id, "name": new_provider.name}, 201
    except Exception as e:
        # Rollback in case of an error
        session.rollback()
        return {"error": f"Failed to create provider: {str(e)}"}, 500
