from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

import os

db_config = {
    'host': os.environ.get("DB_HOST", "localhost"),
    'port': int(os.environ.get("DB_PORT", 3306)),
    'user': os.environ.get("DB_USER", "root"),
    'password': os.environ.get("MYSQL_ROOT_PASSWORD", "123456"),
    'database': os.environ.get("MYSQL_DATABASE", "billdb"),
}

# Build the connection string
DATABASE_URL = (
    f"mysql+pymysql://{db_config['user']}:{db_config['password']}@"
    f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
)

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        print("Connected to the database successfully!")
except Exception as e:
    print(f"Failed to connect to the database: {e}")

# Define the base class for ORM models
Base = automap_base()
# Reflect the existing database tables
Base.prepare(autoload_with=engine)

# Access tables dynamically
Providers = Base.classes.Provider
Rates = Base.classes.Rates
Truck = Base.classes.Trucks

# Create a session maker bound to the engine
session = Session(engine)
