from flask import Flask, request
import json
import subprocess
import logging
import os
from datetime import datetime

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,  # Set logging level
    format='%(asctime)s - %(levelname)s - %(message)s',  # Format: timestamp - level - message
    handlers=[
        logging.FileHandler('/app/logs/ci.log'),  # Save logs to file
        logging.StreamHandler()  # Also print to console
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Basic health check endpoint
@app.route('/health')
def health():
    return {'status': 'OK'}, 200

# Main webhook endpoint that GitHub will call
@app.route('/github-webhook', methods=['POST'])
def webhook():
    try:
        # Get JSON data from GitHub webhook
        data = request.json
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        branch = data['ref'].split('/')[-1]  # Extract branch name from ref (e.g., 'refs/heads/master' -> 'master')

        # Extract and organize relevant information
        event_info = {
            'timestamp': timestamp,
            'branch': branch,
            'repo': data['repository']['clone_url'],
            'commit': data['after'],  # The new commit hash
            'pusher': data['pusher']['name']
        }

        # Save event information to a file
        event_file = f'/app/data/{timestamp}-{branch}_event.json'
        with open(event_file, 'w') as f:
            json.dump(event_info, f, indent=2)

        # Start the CI process
        trigger_ci(event_info)

        return {'status': 'CI process triggered', 'info': event_info}, 200

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500

def trigger_ci(event_info):
    """Function to start the CI process for a received webhook event"""
    try:
        # Create environment variables for the CI script
        env = os.environ.copy()  # Copy current environment
        env.update({
            'BRANCH': event_info['branch'],
            'REPO_URL': event_info['repo'],
            'COMMIT_SHA': event_info['commit'],
            'TIMESTAMP': event_info['timestamp']
        })

        # Run the CI script asynchronously (non-blocking)
        subprocess.Popen(
            ['./ci_script.sh'],  # The script to run
            env=env,  # Pass environment variables
            stdout=open(f'/app/logs/ci_{event_info["timestamp"]}.log', 'w'),  # Log output to file
            stderr=subprocess.STDOUT  # Redirect stderr to stdout
        )

        logger.info(f"CI process triggered for commit {event_info['commit']} on branch {event_info['branch']}")

    except Exception as e:
        logger.error(f"Failed to trigger CI: {str(e)}")
        raise

# Start the Flask server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

