import os
import sys
from flask import Blueprint, jsonify
import mysql.connector

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_config import db_config

unknown_bp = Blueprint("unknown", __name__)

@unknown_bp.route('/unknown', methods=['GET'])
# Function that returns a list of container IDs with unknown weight (NULL values) from the containers_registered table
def get_unknown_weights():
    conn = None  
    cursor = None
    try:
        # Connect to the MySQL database
        conn = mysql.connector.connect(**db_config) 
        cursor = conn.cursor(dictionary=True)
        
        # SQL query to find containers with unknown weight (NULL value)
        query = """
        SELECT cr.container_id
        FROM containers_registered cr
        WHERE cr.weight IS NULL
        """
        
        # Execute the query
        cursor.execute(query)
        rows = cursor.fetchall()

        # Extract the container_ids from the query result
        unknown_container_ids = [row['container_id'] for row in rows]

        # Return the list of container IDs with unknown weight as JSON
        return jsonify(unknown_container_ids)

    except mysql.connector.Error as err:
        # If there's a database error, return an error message
        return jsonify({"error": str(err)}), 500

    finally:
        # Ensure that the cursor and connection are closed if they were created
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()