from flask import Blueprint, request, jsonify
from db_config import db_config
import mysql.connector
from datetime import datetime

item_bp = Blueprint("item", __name__)

@item_bp.route("/item/<id>", methods=["GET"])
def get_item(id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # Check the type of item (truck or container)
    cursor.execute("SELECT weight AS tara FROM trucks WHERE id = %s", (id,))
    truck = cursor.fetchone()
    
    if truck:
        item_type = 'truck'
        tara = truck['tara']
    else:
        # Query the containers_registered table for container data
        cursor.execute("SELECT weight AS tara FROM containers_registered WHERE container_id = %s", (id,))
        container = cursor.fetchone()
        if container:
            item_type = 'container'
            tara = container['tara']  # Use the weight field from the containers_registered table
        else:
            # Item not found in either table
            return jsonify({"error": "Item not found!"}), 404

    # Parse `from` and `to` query parameters
    now = datetime.now()
    
    # Get `from` and `to` query parameters, default to None if not provided
    t1_str = request.args.get('from')
    t2_str = request.args.get('to')
    
    # Default t1 is the first day of the current month at 00:00:00 if no `from` is provided
    t1 = datetime.strptime(t1_str, '%Y%m%d%H%M%S') if t1_str else now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Default t2 is the current time if no `to` is provided
    t2 = datetime.strptime(t2_str, '%Y%m%d%H%M%S') if t2_str else now
    
    # Print out the parsed dates to ensure they are correct
    print(f"Date range for {id}: from {t1} to {t2}")

    # Query sessions within the date range
    cursor.execute("""
        SELECT sessionId FROM transactions
        WHERE (truck = %s OR containers LIKE %s) AND datetime BETWEEN %s AND %s
    """, (id, f"%{id}%", t1, t2))
    
    sessions = cursor.fetchall()
    session_ids = [session['sessionId'] for session in sessions]

    # Close the connection
    cursor.close()
    conn.close()

    # Return the JSON response
    return jsonify({
        "id": id,
        "tara": tara,
        "sessions": session_ids
    })