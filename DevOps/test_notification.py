# test_notification.py
import os
import sys
import logging
from pathlib import Path

# Ensure the script can find the notifier module
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

from notifier import CINotifier

# Setup logging
logging.basicConfig(level=logging.INFO)

def setup_test_env():
    """Setup test environment variables if not already set"""
    # First get the email address since we'll use it for both SMTP_USER and SENDER_EMAIL
    smtp_user = input("Enter email address: ")
    
    test_vars = {
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SMTP_USER': smtp_user,
        'SMTP_PASSWORD': input("Enter app password: "),
        'SENDER_EMAIL': smtp_user,  # Use the same email address
        'RECIPIENT_EMAILS': input("Enter recipient email(s) (comma-separated): ")
    }
    
    # Set all environment variables
    for key, value in test_vars.items():
        os.environ[key] = value

def test_notification():
    """Test both success and failure notifications"""
    notifier = CINotifier()
    
    # Create a test log file
    log_file = Path(current_dir) / 'test_log.txt'
    with open(log_file, 'w') as f:
        f.write("Sample log content\nTest build output\nThis is a test log file")
    
    # Test success notification
    print("\nTesting SUCCESS notification...")
    success = notifier.send_notification(
        'SUCCESS',
        'Test build completed successfully',
        str(log_file)
    )
    print(f"Success notification {'sent' if success else 'failed'}")
    
    # Test failure notification
    print("\nTesting FAILURE notification...")
    success = notifier.send_notification(
        'FAILURE',
        'Test build failed: Error in unit tests',
        str(log_file)
    )
    print(f"Failure notification {'sent' if success else 'failed'}")

if __name__ == '__main__':
    print("=== CI Notification System Test ===")
    setup_test_env()
    test_notification()
