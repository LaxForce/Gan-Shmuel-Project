# app.py
from flask import Flask
from routes import setup_routes

app = Flask(__name__)

# Register the blueprint
setup_routes(app)
if __name__ == "__main__":
    # Run the app on port 5001
    app.run(host='0.0.0.0', port=5001, debug=True)