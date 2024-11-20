from flask import Flask, request
import json
import subprocess
import logging
import os
from datetime import datetime
from monitoring import init_monitoring
from flask_sock import Sock

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
        event_type = request.headers.get('X-GitHub-Event')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # First check if this is a push or PR event
        if event_type == 'ping':  # This indicates it's a ping event
            logger.info(f"Received ping event from GitHub: data={data['zen']}")
            return {'status': 'Ping received'}, 200            
        
        # Handle PR merge event (event_type starts with 'pull' - e.g. 'pull.closed', 'pull.opened', etc.)
        if event_type.startswith('pull'):
            event_info = {
                'timestamp': timestamp,
                'branch': data['pull_request']['base']['ref'],  # Target branch to which the PR was merged
                'source_branch': data['pull_request']['head']['ref'],  # Branch that was merged
                'repo': data['repository']['clone_url'],
                'commit': data['pull_request']['merge_commit_sha'],
                'pusher': data['pull_request']['user']['login']
                # 'commit_email': data['pull_request']['user']['email']
            }
            if data['action'] == 'closed' and data['pull_request'].get('merged'):
                logger.info(f"Received PR Merge closed event: {event_info}")
            elif data['action'] == 'closed' and not data['pull_request'].get('merged'):
                logger.info(f"Received PR closed not merged event: {event_info}")
                return {'status': 'PR closed not merged'}, 220
            elif data['action'] != 'closed':
                logger.info(f"Received non closed PR event: {event_info}")
                return {'status': f"Non closed PR event '{event_type}': action={data['action']}"}, 220
        elif event_type == 'push':  # Handle push event
            event_info = {
                'timestamp': timestamp,
                'branch': data['ref'].split("/")[-1],
                'source_branch': '',  # Empty for direct pushes
                'repo': data['repository']['clone_url'],
                'commit': data['after'],
                'pusher': data['pusher']['name'],
                'commit_email': data['pusher']['email']
            }
            # Check if this is a new branch creation
            if data['before'] == '0' * 40 or data.get('created', False):
                logger.info(f"Skipping new branch create push event: {event_info}")
                return {'status': 'Skipping new branch create push event'}, 220

            # Check if this is a deletion of a branch
            if data['after'] == '0' * 40:
                logger.info(f"Received branch deletion event: {event_info}")
                return {'status': 'Branch deletion event'}, 220

            # Check if this is a push to master that might have been covered by a PR merge
            if event_info['branch'] == 'master' and event_info['source_branch'] == '':
                logger.info(f"Received push event to master, following PR Merge: {event_info}")

            # Otherwise, this is a normal push event    
            logger.info(f"Received feature branch push event: {event_info}")
        else:
            logger.warning(f"Not a PR Merge or push event: event_type={event_type}, action={data['action']}")
            return {'status': f"Not a PR Merge or push event '{event_type}': action={data['action']}"}, 400
        
        # Log event information
        logger.info(f"Received webhook event: {event_info}")

        # Save event information to a file. Use the branch name as part of the filename
        # Save event information to a file
        event_file = f'/app/data/{timestamp}-{event_info["branch"].split("/")[-1]}_event.json'
        with open(event_file, 'w') as f:
            json.dump(event_info, f, indent=2)

        # Check if there is commit email in the event_info, if not, use the default email
        if 'commit_email' not in event_info:
            event_info['commit_email'] = 'default@example.com'
            logger.info(f"Using default commit email: {event_info['commit_email']}")
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
            # 'COMMIT_EMAIL': event_info['commit_email']
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

