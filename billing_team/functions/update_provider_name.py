from sqlalchemy.orm import sessionmaker
from sql.billing_sql import Providers, engine
from flask import jsonify

def update_provider_name(id, new_name):
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Query for the provider by ID
        provider = session.query(Providers).filter_by(id=id).first()
        if not provider:
            return jsonify({"error": f"Provider with id {id} not found"}), 404

        # Update the provider's name
        provider.name = new_name
        session.commit()
        return jsonify({"message": f"Provider {id} updated successfully!"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
