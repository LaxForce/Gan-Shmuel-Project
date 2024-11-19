from flask import Blueprint, jsonify
import os
import sys
import mysql.connector
import time
from db_config import db_config

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

health_bp = Blueprint("health", __name__)

def check_db_connection(max_retries=5, retry_delay=5):
    retries = 0
    while retries < max_retries:
        try:
            # Try connecting to the database
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")  # Simple query to test connection
            conn.close()
            return True  # Connection successful
        except mysql.connector.Error as err:
            retries += 1
            print(f"Error: {err} - Attempt {retries}/{max_retries}")
            time.sleep(retry_delay)  # Wait before retrying
    return False  # If all retries fail

@health_bp.route('/health', methods=['GET'])
# Function to check database availability
def health_check():
    db_available = check_db_connection()
    if db_available:
        return jsonify("OK"), 200  # If connection is successful
    else:
        return jsonify("Failure"), 500  # If connection fails