from flask import Flask, jsonify, request
import mysql.connector # type: ignore
from dotenv import load_dotenv
import os
import time
from datetime import datetime
import json
import io
import pandas as pd
from mysql.connector import Error

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

# Function to create the table in the database
def create_table():
    attempts = 5
    for i in range(attempts):
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            print("Creating table...") 
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trucks (
                    id VARCHAR(50) NOT NULL,
                    weight FLOAT NOT NULL,
                    unit VARCHAR(50) NOT NULL
                )
            """)
            conn.commit()
            print("Table 'trucks' created successfully.")
            # Call to import data from the JSON file
            import_trucks_data(conn, cursor)
            break
        except Error as e:
            print(f"Error creating table: {str(e)}")
            if i < attempts - 1:
                print("Retrying...")
                time.sleep(5)  # Wait 5 seconds before retrying
            else:
                print("Max retry attempts reached.")
                break
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

# Function to import truck data from the JSON file into the database
def import_trucks_data(conn, cursor):
    # Reading the trucks.json file in the weight_db directory
    try:
        with open('./trucks.json', 'r') as file:
            trucks_data = json.load(file)
        
        print(f"Importing {len(trucks_data)} records into the 'trucks' table.")
        
        for truck in trucks_data:
            id = truck.get('id')
            weight = truck.get('weight')
            unit = truck.get('unit')
            
            # Insert data into the table
            cursor.execute("""
                INSERT INTO trucks (id, weight, unit)
                VALUES (%s, %s, %s)
            """, (id, weight, unit))
        
        conn.commit()
        print(f"{len(trucks_data)} records imported successfully.")
    except FileNotFoundError:
        print("trucks.json file not found.")
    except json.JSONDecodeError:
        print("Error decoding JSON file.")
    except Error as e:
        print(f"Error importing data: {str(e)}")

create_table()

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
        return jsonify({"error": "No files provided"}), 400  # If no files were uploaded, return an error response
    
    message = []  # Initialize the message list to store response messages

    for file in files:
        # Check if the file is empty
        file_content = file.read()
        if len(file_content) == 0:
            message.append(f"Empty file {file.filename}.")
            return jsonify({"error": "Empty file uploaded"}), 400  # Return a 400 error for empty files

        file_extension = file.filename.split('.')[-1].lower()

        # Handle CSV files
        if file_extension == 'csv':
            try:
                # Use pandas to read the CSV
                df = pd.read_csv(io.BytesIO(file_content))
                
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
            
            except pd.errors.EmptyDataError:
                message.append(f"CSV file {file.filename} is empty.")
            except Exception as e:
                message.append(f"Error processing CSV {file.filename}: {str(e)}")

        # Handle JSON files
        elif file_extension == 'json':
            try:
                # Load the JSON data from the file content
                file_data = json.loads(file_content)
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
            
            except json.JSONDecodeError:
                message.append(f"Invalid JSON format in {file.filename}.")
            except Exception as e:
                message.append(f"Error processing JSON {file.filename}: {str(e)}")

        # Handle unsupported file formats
        else:
            message.append(f"Unsupported file format in {file.filename}.")
            return jsonify({"error": "Unsupported file format"}), 400  # Return 400 error for unsupported formats
    
    # Return the collected messages in the response
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

@app.route('/item/<id>', methods=['GET'])
def get_item(id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # Check the type of item (truck or container)
    cursor.execute("SELECT * FROM trucks WHERE id = %s", (id,))
    truck = cursor.fetchone()
    
    if truck:
        item_type = 'truck'
        tara = truck['weight']
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
        WHERE t.sessionId = %s
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
@app.route('/weight', methods=['POST'])
def record_weight():
    data = request.json

    direction = data.get('direction')
    truck = data.get('truck', "na")
    containers = data.get('containers', "").split(",")
    weight = data.get('weight')  # This is the bruto
    unit = data.get('unit', "kg")
    force = data.get('force', "false").lower() == "true"
    produce = data.get('produce', "na")

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Check if id is in the trucks table and if we get weight - if not return error, else insert
        query = "SELECT id FROM trucks WHERE id = %s"
        cursor.execute(query, (truck,))
        if cursor.fetchone() is None:
            if weight is not None:
                query = "INSERT INTO trucks (id, weight, unit) VALUES (%s, %s, 'kg')"
                cursor.execute(query, (truck, weight))
            else:
                return jsonify({"error": "Truck not found and weight is required."}), 400
        
        # If weight is not provided, search for it in the trucks table
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

            if existing_in and not force:
                if existing_in['direction'] == 'in':
                    return jsonify({"error": "Truck already weighed in. Use force=true to overwrite."}), 400
            elif existing_in and force and existing_in['direction'] == 'in':
                query = """
                    UPDATE transactions
                    SET bruto = %s
                    WHERE id = %s
                """
                cursor.execute(query, (weight, existing_in['id']))
                conn.commit()
                return jsonify({"id": existing_in['id'], "truck": truck, "bruto": weight}), 201

            else:
                # Insert the 'in' transaction (bruto is the weight)
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
                SELECT id, bruto, sessionId, direction, truckTara, neto
                FROM transactions
                WHERE truck = %s
                ORDER BY datetime DESC LIMIT 1
            """
            cursor.execute(query, (truck,))
            previous = cursor.fetchone()

            if not previous:
                return jsonify({"error": "No previous 'in' record found for this truck."}), 400
            elif not force and previous['direction'] == "out" or previous['direction'] == "none":
                return jsonify({"error": "Truck already weighed out. Use force=true to overwrite."}), 400
            elif force and previous['direction'] == "out":
                 # Get the sum of container tara from the containers table
                neto_up = previous['neto'] + previous['truckTara'] - weight
                
                # Update the 'in' transaction with the new weight
                query = """
                    UPDATE transactions
                    SET truckTara = %s, neto = %s
                    WHERE id = %s
                """
                cursor.execute(query, (weight, neto_up, previous['id']))
                conn.commit()

                query = """
                    SELECT bruto
                    FROM transactions
                    WHERE truck = %s AND direction = 'in'
                    ORDER BY datetime DESC LIMIT 1
                """
                cursor.execute(query, (truck,))
                previous_in = cursor.fetchone()
                
                return jsonify({
                    "id": previous['id'],
                    "truck": truck,
                    "bruto": previous_in['bruto'],
                    "truckTara": weight,
                    "neto": neto_up
                }), 201

            # Get the sum of container tara from the containers table
            container_tara_sum = 0
            if containers:
                query = "SELECT SUM(weight) as tara FROM containers_registered WHERE container_id IN (%s)"
                cursor.execute(query, containers)
                container_tara = cursor.fetchone()
                container_tara_sum = container_tara['tara'] if container_tara and container_tara['tara'] else 0
            
             # Check for the latest 'in' transaction for the truck
            query = """
                SELECT id, bruto, sessionId, direction, truckTara, neto
                FROM transactions
                WHERE truck = %s AND direction = 'in'
                ORDER BY datetime DESC LIMIT 1
            """
            cursor.execute(query, (truck,))
            previous_in = cursor.fetchone()
            
            # the same session id as in transaction
            session_id = previous_in['sessionId']

            # Calculate truck tara and neto
            bruto = previous_in['bruto']
            truck_tara = weight
            neto = bruto - truck_tara - container_tara_sum

            # If any container has unknown tara, return "na" for neto
            if neto < 0:
                neto = "na"

            query = """
                INSERT INTO transactions (sessionId, truck, containers, datetime, direction, bruto, truckTara, neto, produce)
                VALUES (%s, %s, %s, NOW(), 'out', %s, %s, %s, %s)
            """
            cursor.execute(query, (session_id, truck, ",".join(containers), previous_in['bruto'], truck_tara, neto, produce))
            
            # Fetch the last inserted ID
            transaction_id = cursor.lastrowid
            conn.commit()
            

            return jsonify({
                "id": transaction_id,
                "truck": truck,
                "bruto": bruto,
                "truckTara": truck_tara,
                "neto": neto
            }), 201

        elif direction == "none":

            # Check for the latest 'in' transaction for the truck
            query = """
                SELECT direction, id 
                FROM transactions
                WHERE truck = %s
                ORDER BY datetime DESC LIMIT 1
            """
            cursor.execute(query, (truck,))
            last_transaction = cursor.fetchone()

            # If the last transaction was 'in', prevent 'none' direction
            if last_transaction and last_transaction['direction'] == 'in':
                return jsonify({"error": "'none' direction is not supported after 'in'."}), 400
            elif last_transaction and last_transaction['direction'] == 'none' and force:
                query = """
                    UPDATE transactions
                    SET bruto = %s
                    WHERE truck = %s
                    """
                cursor.execute(query, (weight, truck))
                conn.commit()

                return jsonify({"id": last_transaction['id'], "truck": truck, "bruto": weight}), 201

            # Generate session_id based on datetime (max 12 digits)
            session_id = datetime.now().strftime('%Y%m%d%H%M')[:20]
                
            # Insert the 'none' transaction (bruto is the weight)
            query = """
                INSERT INTO transactions (sessionId, truck, containers, datetime, direction, bruto, produce)
                VALUES (%s, %s, %s, NOW(), 'none', %s, %s)
            """
            cursor.execute(query, (session_id, truck, ",".join(containers), weight, produce))
                
            # Fetch the last inserted ID
            transaction_id = cursor.lastrowid
            conn.commit()

            return jsonify({"id": transaction_id, "truck": truck, "bruto": weight}), 201

        # New checks for "in" followed by "in" or "out" followed by "out"
        if direction in ["in", "out"]:
            # Check if there's an existing transaction of the same direction
            query = """
                SELECT direction 
                FROM transactions
                WHERE truck = %s
                ORDER BY datetime DESC LIMIT 1
            """
            cursor.execute(query, (truck,))
            last_transaction = cursor.fetchone()

            if last_transaction and last_transaction['direction'] == direction:
                if not force:
                    return jsonify({"error": f"Truck already weighed {direction}. Use force=true to overwrite."}), 400

            # Handle overwriting if force is true (if needed, update the previous record)
            if force:
                # Delete previous transaction of the same direction (optional)
                query = """
                    DELETE FROM transactions
                    WHERE truck = %s AND direction = %s
                """
                cursor.execute(query, (truck, direction))
                conn.commit()

                # Re-insert the transaction
                session_id = datetime.now().strftime('%Y%m%d%H%M')[:20]
                query = """
                    INSERT INTO transactions (sessionId, truck, containers, datetime, direction, bruto, produce)
                    VALUES (%s, %s, %s, NOW(), %s, %s, %s)
                """
                cursor.execute(query, (session_id, truck, ",".join(containers), direction, weight, produce))
                transaction_id = cursor.lastrowid
                conn.commit()

                return jsonify({"id": transaction_id, "truck": truck, "bruto": weight}), 201

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)  # Listen on all interfaces

