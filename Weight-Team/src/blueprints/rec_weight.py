from flask import Blueprint, request, jsonify
from db_config import db_config
import mysql.connector
from datetime import datetime

rec_weight_bp = Blueprint("rec_weight", __name__)

@rec_weight_bp.route('/weight', methods=['POST'])
def record_weight():
    data = request.json

    direction = data.get('direction')
    truck = data.get('truck', "na")
    containers = data.get('containers', "").split(",")
    weight = data.get('weight')  # This is the bruto
    unit = data.get('unit', "kg")
    force = str(data.get('force', "false")).lower() == "true"
    produce = data.get('produce', "na")

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Check if the truck exists in the database
        query = "SELECT id FROM trucks WHERE id = %s"
        cursor.execute(query, (truck,))
        if cursor.fetchone() is None:
            if weight is not None:
                query = "INSERT INTO trucks (id, weight, unit) VALUES (%s, %s, 'kg')"
                cursor.execute(query, (truck, weight))
            else:
                return jsonify({"error": "Truck not found and weight is required."}), 400
        
        # If weight is not provided, retrieve it from the database
        elif weight is None:
            query = "SELECT weight FROM trucks WHERE id = %s"
            cursor.execute(query, (truck,))
            truck_weight = cursor.fetchone()
            if truck_weight and truck_weight['weight'] is not None:
                weight = truck_weight['weight']
            else:
                return jsonify({"error": "Weight is required and could not be determined from the DB."}), 400

        # Convert weight to KG if it's in lbs
        if unit == "lbs":
            weight = round(weight * 0.453592, 2)

        if direction == "in":
            # Generate session_id based on datetime (max 12 digits)
            session_id = datetime.now().strftime('%Y%m%d%H%M')[:20]

            # Check if there's already an 'in' record for the truck
            query = """
                SELECT id, bruto, direction
                FROM transactions
                WHERE truck = %s
                ORDER BY datetime DESC LIMIT 1
            """
            cursor.execute(query, (truck,))
            existing_in = cursor.fetchone()

            # Handle existing 'in' record
            if existing_in:
                if 'direction' in existing_in and existing_in['direction'] == 'in':
                    if not force:
                        return jsonify({"error": "Truck already weighed in. Use force=true to overwrite."}), 400
                    # Force overwrite the 'in' record
                    query = """
                        UPDATE transactions
                        SET bruto = %s
                        WHERE id = %s
                    """
                    cursor.execute(query, (weight, existing_in['id']))
                    conn.commit()
                    return jsonify({"id": existing_in['id'], "truck": truck, "bruto": weight}), 201

            # Insert a new 'in' transaction
            query = """
                INSERT INTO transactions (sessionId, truck, containers, datetime, direction, bruto, produce)
                VALUES (%s, %s, %s, NOW(), 'in', %s, %s)
            """
            cursor.execute(query, (session_id, truck, ",".join(containers), weight, produce))
            
            # Fetch the last inserted ID
            transaction_id = cursor.lastrowid
            conn.commit()

            return jsonify({"id": transaction_id, "truck": truck, "bruto": weight}), 201

        elif direction == "out":
            # Check for the latest 'in' transaction for the truck
            query = """
                SELECT id, bruto, direction
                FROM transactions
                WHERE truck = %s
                ORDER BY datetime DESC LIMIT 1
            """
            cursor.execute(query, (truck,))
            previous_in = cursor.fetchone()

            if not previous_in or 'direction' not in previous_in or previous_in['direction'] != "in":
                return jsonify({"error": "No previous 'in' record found for this truck."}), 400

            # Calculate net weight and insert 'out' transaction
            bruto = previous_in['bruto']
            truck_tara = weight
            neto = bruto - truck_tara
            query = """
                INSERT INTO transactions (truck, datetime, direction, bruto, truckTara, neto, produce)
                VALUES (%s, NOW(), 'out', %s, %s, %s, %s)
            """
            cursor.execute(query, (truck, bruto, truck_tara, neto, produce))
            
            # Fetch the last inserted ID
            transaction_id = cursor.lastrowid
            conn.commit()

            return jsonify({"id": transaction_id, "truck": truck, "bruto": bruto, "truckTara": truck_tara, "neto": neto}), 201

        else:
            return jsonify({"error": "Invalid direction."}), 400

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
