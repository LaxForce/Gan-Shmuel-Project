from flask import Flask, jsonify, request
import mysql.connector
from dotenv import load_dotenv
import os
import time
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Database connection configuration using environment variables
db_config = {
    'host': os.getenv("DB_HOST", "mysql-db"),
    'user': os.getenv("DB_USER", "weight_team"),
    'password': os.getenv("DB_PASSWORD", "12345"),
    'database': os.getenv("DB_NAME", "weight")
}

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the Truck Weighing API!"

# Function to check database connection
def check_db_connection():
    max_retries = 5  # Maximum number of retries
    retries = 0
    while retries < max_retries:
        try:
            # Establish a connection to check DB availability
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")  # Simple database check
            conn.close()
            return True
        except mysql.connector.Error as err:
            retries += 1
            print(f"Error: {err} - Attempt {retries}/{max_retries}")
            time.sleep(5)  # Wait 5 seconds before retrying
    return False  # If connection fails after multiple attempts

@app.route('/health', methods=['GET'])
def health_check():
    # Check database availability
    db_available = check_db_connection()
    if db_available:
        return jsonify("OK"), 200  # If connection is successful
    else:
        return jsonify("Failure"), 500  # If connection fails
    
@app.route('/unknown', methods=['GET'])
def get_unknown_weights():
    # Function that returns a list of container IDs with unknown weight (NULL values) from the containers_registered table
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
        # Close the database connection and cursor
        if conn.is_connected():
            cursor.close()
            conn.close()

# Define valid directions for filtering
VALID_DIRECTIONS = ['in', 'out', 'none']

@app.route('/weight', methods=['GET'])
def get_weights():
    # Get 'from' date (t1) - default to today's date at 00:00:00
    t1_str = request.args.get('from', default=None, type=str)
    if t1_str is None:
        # Default to today's date at 00:00:00
        t1 = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            # Try to parse 'from' date in the format yyyymmddhhmmss
            t1 = datetime.strptime(t1_str, '%Y%m%d%H%M%S')
        except ValueError:
            return jsonify({"error": "Invalid 'from' date format. Use yyyymmddhhmmss."}), 400

    # Get 'to' date (t2) - default to now if 'to' is not provided
    t2_str = request.args.get('to', default=None, type=str)
    if t2_str is None:
        # Default to current time (now)
        t2 = datetime.now()
    else:
        try:
            # Try to parse 'to' date in the format yyyymmddhhmmss
            t2 = datetime.strptime(t2_str, '%Y%m%d%H%M%S')
        except ValueError:
            return jsonify({"error": "Invalid 'to' date format. Use yyyymmddhhmmss."}), 400

    # Get 'filter' directions - default to 'in,out,none'
    filter_str = request.args.get('filter', default='in,out,none', type=str)
    
    # If the filter is a single value (not comma-separated), treat it as a list of one value
    if ',' not in filter_str:
        directions = [filter_str]  # Single direction (e.g., "in", "out", "none")
    else:
        directions = filter_str.split(',')  # Multiple directions (e.g., "in,out")

    # Validate filter directions
    invalid_directions = [direction for direction in directions if direction not in VALID_DIRECTIONS]
    if invalid_directions:
        return jsonify({"error": f"Invalid filter values: {', '.join(invalid_directions)}. Valid directions are 'in', 'out', 'none'."}), 400

    # Connect to the database and fetch the records based on the filters
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Create SQL query based on parameters
        filter_conditions = ','.join(["'{}'".format(direction) for direction in directions])
        
        query = f"""
        SELECT t.id, t.direction, t.bruto, t.neto, t.produce, t.containers
        FROM transactions t
        WHERE t.datetime BETWEEN %s AND %s
        AND t.direction IN ({filter_conditions})
        """
        
        # Execute the query with the provided date range
        cursor.execute(query, (t1, t2))
        rows = cursor.fetchall()

        # Format the response
        results = []
        for row in rows:
            # Ensure 'neto' is set to 'na' if it's None
            neto = row['neto'] if row['neto'] is not None else 'na'
            
            # Parse the containers (assuming it's stored as a comma-separated string)
            containers = row['containers'].split(',') if row['containers'] else []
            
            results.append({
                "id": row['id'],
                "direction": row['direction'],
                "bruto": row['bruto'],
                "neto": neto,
                "produce": row['produce'],
                "containers": containers
            })

        return jsonify(results)

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)  # Listen on all interfaces

