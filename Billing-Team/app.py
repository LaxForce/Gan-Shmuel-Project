from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/billing')
def billing():
    # Try to connect to weight service to show dependency
    try:
        requests.get('http://weight:8081/api/weight')
        return jsonify({"billing": True}), 200
    except:
        return jsonify({"error": "Weight service not accessible"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)
