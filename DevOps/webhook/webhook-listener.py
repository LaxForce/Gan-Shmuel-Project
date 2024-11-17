from flask import Flask, request
import json
from datetime import datetime
import os

app = Flask(__name__)

WEBHOOK_DIR = "webhook_data"
os.makedirs(WEBHOOK_DIR, exist_ok=True)

@app.route('/health')
def health():
    return {'status': 'OK'}, 200

@app.route('/github-webhook', methods=['POST'])
def webhook():
    data = request.json
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    branch = data['ref'].split('/')[-1]
    
    event_info = {
        'timestamp': timestamp,
        'branch': branch,
        'repo': data['repository']['clone_url'],
        'commit': data['after'],
        'pusher': data['pusher']['name']
    }
    
    # Save webhook data with new naming format
    with open(f'{WEBHOOK_DIR}/{timestamp}-{branch}_webhook.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    # Save processed info with new naming format
    with open(f'{WEBHOOK_DIR}/{timestamp}-{branch}_event.json', 'w') as f:
        json.dump(event_info, f, indent=2)
    
    return {'status': 'received', 'info': event_info}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
