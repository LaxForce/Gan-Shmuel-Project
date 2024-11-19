import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Config:
    """Base configuration class."""
    # General settings
    DEBUG = False
    TESTING = False

    # Database settings
    DB_HOST = os.getenv("DB_HOST", "mysql-db")
    DB_USER = os.getenv("DB_USER", "weight_team")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "12345")
    DB_NAME = os.getenv("DB_NAME", "weight")
    DB_PORT = int(os.getenv("DB_PORT", 3306))

    # Other settings can go here
    JSON_SORT_KEYS = False  # Keep JSON response keys in the original order


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DB_NAME = "test_weight"  # Separate test database


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


# Dictionary to select the appropriate configuration
configurations = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig
}

def get_config(env: str = "development"):
    """Get the appropriate configuration class based on the environment."""
    return configurations.get(env.lower(), DevelopmentConfig)
