from flask import Flask, jsonify, request
import mysql.connector
from dotenv import load_dotenv
import os
import time
from datetime import datetime
import json
import pandas as pd

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

# Helper function to check database connection
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
# Function to check database availability
def health_check():
    db_available = check_db_connection()
    if db_available:
        return jsonify("OK"), 200  # If connection is successful
    else:
        return jsonify("Failure"), 500  # If connection fails
    
@app.route('/unknown', methods=['GET'])
# Function that returns a list of container IDs with unknown weight (NULL values) from the containers_registered table
def get_unknown_weights():
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

# Helper function to insert batch data into the database
def insert_batch_weight(container_data):
    try:
        # Connect to the database using the provided db_config
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        inserted_count = 0  # Initialize a counter for the inserted records

        # Loop through each record in container_data and insert it into the database
        for data in container_data:
            # Convert weight of 0 to NULL before inserting
            if data['weight'] == 0:
                data['weight'] = None

            # Check if the container_id already exists in the database
            cursor.execute("SELECT COUNT(*) FROM containers_registered WHERE container_id = %s", (data['container_id'],))
            exists = cursor.fetchone()[0]
            
            # If the container_id does not exist, insert it
            if exists == 0:
                cursor.execute("""
                    INSERT INTO containers_registered (container_id, weight, unit)
                    VALUES (%s, %s, %s)
                """, (data['container_id'], data['weight'], data['unit']))
                inserted_count += 1
            else:
                # If the container_id exists, skip the insertion
                print(f"Skipping {data['container_id']} as it already exists.")

        # Commit the transaction to the database
        conn.commit()
        
        # Return the number of records inserted
        return inserted_count
    except mysql.connector.Error as err:
        # If any database error occurs, print and raise the error
        print(f"Error: {err}")
        raise
    finally:
        # Close the database connection if it's open
        if conn.is_connected():
            cursor.close()
            conn.close()
            
@app.route('/batch-weight', methods=['POST'])
# Function to parse CSV or JSON file and insert the data into the database
def batch_weight():
    files = request.files.getlist('file')
    if not files:
        return jsonify({"error": "No files provided"}), 400
    
    message = []

    for file in files:
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension == 'csv':
            try:
                # Use pandas to read the CSV
                df = pd.read_csv(file)
                
                # Check if the necessary columns are present in the CSV
                required_columns = ['id', 'weight', 'unit']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    raise ValueError(f"Missing columns in CSV file: {', '.join(missing_columns)}")
                
                # Clean the data and handle missing or invalid weight
                df['container_id'] = df['id'].str.strip()
                df['weight'] = pd.to_numeric(df['weight'], errors='coerce')

                # The unit should be taken from the CSV directly, so we assume the unit is in the file
                df['unit'] = df['unit'].str.strip()  # Clean any unwanted spaces in 'unit' column

                # Prepare data to insert into the DB
                container_data = df[['container_id', 'weight', 'unit']].to_dict(orient='records')

                # Insert data into the database
                inserted_count = insert_batch_weight(container_data)
                message.append(f"CSV data from {file.filename} processed successfully. {inserted_count} records inserted.")
            
            except Exception as e:
                message.append(f"Error processing CSV {file.filename}: {str(e)}")

        elif file_extension == 'json':
            try:
                file_data = json.loads(file.read())
                container_data = []
                
                # Check if the necessary fields are present in each entry in the JSON
                for entry in file_data:
                    if not all(key in entry for key in ['id', 'weight', 'unit']):
                        raise ValueError(f"Missing required fields in JSON entry. Each entry must contain 'id', 'weight', and 'unit'.")
                    
                    weight = entry['weight']
                    try:
                        weight = float(weight) if weight else None
                    except ValueError:
                        weight = None
                    
                    unit = entry['unit'].strip() if 'unit' in entry else 'kg'  # Default to 'kg' if no unit specified
                    container_data.append({
                        'container_id': entry['id'],
                        'weight': weight if weight is not None else None,
                        'unit': unit
                    })

                # Insert data into the database
                inserted_count = insert_batch_weight(container_data)
                message.append(f"JSON data from {file.filename} processed successfully. {inserted_count} records inserted.")
            
            except Exception as e:
                message.append(f"Error processing JSON {file.filename}: {str(e)}")

        else:
            message.append(f"Unsupported file format in {file.filename}.")

    return jsonify({"message": message}), 200

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
    
    if t1 > t2:
        return jsonify({"error": "Invalid date range. 'from' date must be before 'to' date."}), 400

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

@app.route('/session/<id>', methods=['GET'])
def get_session(id):
    # Connect to the database
    try:
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
        if conn.is_connected():
            cursor.close()
            conn.close()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)  # Listen on all interfaces

