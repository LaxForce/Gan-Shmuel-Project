from flask import Blueprint, jsonify
import mysql.connector
from db_config import db_config

session_bp = Blueprint("session", __name__)

@session_bp.route('/session/<id>', methods=['GET'])
def get_session(id):
    conn = None  # Initialize conn to avoid UnboundLocalError

    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Query the session based on the ID (with LIMIT 2 to allow two transactions)
        query = """
        SELECT t.id, t.direction, t.truck, t.bruto, t.truckTara, t.neto, t.containers
        FROM transactions t
        WHERE t.SessionId = %s
        LIMIT 2
        """
        cursor.execute(query, (id,))
        rows = cursor.fetchall()

        # If no sessions are found, return a 404 error
        if not rows:
            return jsonify({"error": "Session not found"}), 404
        
        # Prepare the response list to handle multiple rows
        results = []

        for row in rows:
            response = {
                "id": row['id'],
                "truck": row['truck'] if row['truck'] is not None else "na",
                "bruto": row['bruto'],
            }

            # Only add truckTara and neto for 'in' direction
            if row['direction'] == 'in':
                neto = row['neto'] if row['neto'] is not None else "na"
                response.update({
                    "truckTara": row['truckTara'],
                    "neto": neto
                })

            # No need for 'else' block for 'out' - just append the result
            results.append(response)

        # Return the list of transactions as JSON
        return jsonify(results)

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn is not None and conn.is_connected():  # Check if conn is initialized and connected
            cursor.close()
            conn.close()
