from flask import Flask, request
import json
import subprocess
import logging
import os
from datetime import datetime
from monitoring import init_monitoring
from flask_sock import Sock

# Get Webhook port from environment variable or use default
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 8080))

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
app.secret_key = os.urandom(24)  # Generate a random secret key for session management
sock=Sock(app)
init_monitoring(app, sock) # Register monitoring blueprint
logger.info("Monitoring initialized with WebSocket. Routes: {[rule.rule for rule in app.url_map.iter_rules()]}")

# Basic health check endpoint
@app.route('/health')
def health():
    return {'status': 'OK'}, 200

# Main webhook endpoint that GitHub will call
@app.route('/github-webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Handle PR merge event
        if data['event'] == 'pull_request' and data['action'] == 'closed' and data['pull_request'].get('merged'):
            event_info = {
                'timestamp': timestamp,
                'branch': 'master',  # Target branch is always master for merged PRs
                'source_branch': data['pull_request']['head']['ref'],  # Branch that was merged
                'repo': data['repository']['clone_url'],
                'commit': data['pull_request']['merge_commit_sha'],
                'pusher': data['pull_request']['user']['login']
            }
            
        # Handle push event    
        elif data['event'] == 'push':
            event_info = {
                'timestamp': timestamp,
                'branch': data['ref'].partition('refs/heads/')[-1],
                'source_branch': '',  # Empty for direct pushes
                'repo': data['repository']['clone_url'],
                'commit': data['after'],
                'pusher': data['pusher']['name']
            }
        else:
            return {'status': 'Not a PR Merge or push event'}, 400

        # Save event information to a file
        event_file = f'/app/data/{timestamp}-{event_info["branch"]}_event.json'
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
    app.run(host='0.0.0.0', port=WEBHOOK_PORT)

