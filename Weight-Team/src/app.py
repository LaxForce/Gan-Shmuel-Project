from flask import Flask
from blueprints import init_blueprints
from dotenv import load_dotenv
from config import get_config
from blueprints.trucks import create_table
import mysql.connector

# Load environment variables
load_dotenv()

# Load configuration
config = get_config()

app = Flask(__name__)

# Initialize blueprints
init_blueprints(app)

# Creating trucks table on mysql db 
create_table()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
