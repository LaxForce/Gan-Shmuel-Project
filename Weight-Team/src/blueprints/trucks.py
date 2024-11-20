import os
import sys
import mysql.connector
from mysql.connector import Error
from flask import Blueprint
import json
import time

trucks_bp = Blueprint('trucks', __name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_config import db_config

@trucks_bp.before_app_request
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