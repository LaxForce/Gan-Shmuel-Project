from flask import Blueprint, request, jsonify
import pandas as pd
import json
import io
import mysql.connector

# DB connection function
def get_db_connection():
    db_config = {
        "host": "mysql-db",
        "user": "weight_team",
        "password": "12345",
        "database": "weight"
    }
    conn = mysql.connector.connect(**db_config)  # Use mysql.connector.connect() directly
    return conn

batch_weight_bp = Blueprint("batch_weight", __name__)

# Helper function to insert batch data into the database
def insert_batch_weight(container_data):
    try:
        # Get the database connection
        conn = get_db_connection()  # This is your one connection
        cursor = conn.cursor()

        inserted_count = 0

        for data in container_data:
            if data['weight'] == 0:
                data['weight'] = None

            cursor.execute(
                "SELECT COUNT(*) FROM containers_registered WHERE container_id = %s", 
                (data['container_id'],)
            )
            exists = cursor.fetchone()[0]

            if exists == 0:
                cursor.execute(
                    """
                    INSERT INTO containers_registered (container_id, weight, unit)
                    VALUES (%s, %s, %s)
                    """, 
                    (data['container_id'], data['weight'], data['unit'])
                )
                inserted_count += 1
            else:
                print(f"Skipping {data['container_id']} as it already exists.")

        conn.commit()
        return inserted_count
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        raise
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@batch_weight_bp.route('/batch-weight', methods=['POST'])
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
                    
                    # Default to 'kg' if no unit specified
                    unit = entry['unit'].strip() if 'unit' in entry else 'kg'  
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
