#Erez added for git push test

import sqlite3
from flask import Flask, request

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check verifies:
    1. The GET method is successful.
    2. The database connection works by executing a simple SELECT 1 query.
       ***Need to Rename database in check_database() when its ready
    """
    try:
        # Check if the request method is GET
        if request.method != 'GET':
            raise Exception("GET method failed")
        
        # Check database connection
        check_database()

        # If all checks pass, return success
        return "Health Check: SUCCESS", 200

    except Exception as e:
        # If any check fails, log the error and return failure
        print(f"Health check failed: {e}")
        return "Health Check: FAILURE", 500


def check_database():
    """
    Function to check database connectivity
    """
    try:
        connection = sqlite3.connect("billdb.db")  # Connect to the database
        cursor = connection.cursor()
        cursor.execute("SELECT 1;")         
        cursor.close()
        connection.close()
    except Exception as e:
        raise Exception(f"Database connection failed: {e}")


if __name__ == '__main__': 
    app.run(debug=True)