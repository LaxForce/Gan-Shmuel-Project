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
    cursor.execute("SELECT * FROM trucks WHERE id = %s", (id,))
    truck = cursor.fetchone()
    
    if truck:
        item_type = 'truck'
        tara = truck.get('weight')  # Avoid KeyError
        if tara is None:
            return jsonify({"error": "Truck record is missing the 'weight' field!"}), 500
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
    
    t1_str = request.args.get('from')
    t2_str = request.args.get('to')
    t1 = datetime.strptime(t1_str, '%Y%m%d%H%M%S') if t1_str else now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    t2 = datetime.strptime(t2_str, '%Y%m%d%H%M%S') if t2_str else now
    
    cursor.execute("""
        SELECT sessionId FROM transactions
        WHERE (truck = %s OR containers LIKE %s) AND datetime BETWEEN %s AND %s
    """, (id, f"%{id}%", t1, t2))
    
    sessions = cursor.fetchall()
    session_ids = [session['sessionId'] for session in sessions]

    cursor.close()
    conn.close()

    return jsonify({
        "id": id,
        "tara": tara,
        "sessions": session_ids
    })