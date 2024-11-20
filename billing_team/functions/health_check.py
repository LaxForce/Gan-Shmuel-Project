from sql.billing_sql import engine

def check_health():
    try:
        # Attempt to connect to the database
        with engine.connect() as connection:
            # If the connection is successful
            return {"status": "OK"}, 200
    except Exception as e:
        # If an error occurs
        return {"error": f"Health check failed: {str(e)}"}, 500
