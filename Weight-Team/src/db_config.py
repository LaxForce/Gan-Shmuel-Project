import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

db_config = {
    'host': os.getenv("DB_HOST", "mysql-db"),
    'user': os.getenv("DB_USER", "weight_team"),
    'password': os.getenv("DB_PASSWORD", "12345"),
    'database': os.getenv("DB_NAME", "weight"),
    'port': 3306  
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        raise RuntimeError(f"Database connection error: {str(e)}")
