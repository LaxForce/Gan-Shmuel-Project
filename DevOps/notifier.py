# notifier.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

class CINotifier:
    def __init__(self):
        # Get email configuration from environment variables
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_user = os.environ.get('SMTP_USER')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.sender_email = os.environ.get('SMTP_USER')  # Use SMTP_USER as sender
        self.recipient_emails = os.environ.get('RECIPIENT_EMAILS', '').split(',')
        
        # Setup logging
        self.logger = logging.getLogger('ci_notifier')
        
    def send_notification(self, status, message, log_file=None):
        """
        Send CI notification email
        
        Args:
            status (str): Status of the CI run ('SUCCESS' or 'FAILURE')
            message (str): Detailed message about the CI run
            log_file (str, optional): Path to the CI log file
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.recipient_emails)
            msg['Subject'] = f'CI {status}: {message[:50]}...' if len(message) > 50 else f'CI {status}: {message}'
            
            # Create email body with more detailed information
            body = f"""
CI Build Status: {status}

Message: {message}

Build Details:
- Status: {status}
- Timestamp: {os.environ.get('TIMESTAMP', 'N/A')}
- Branch: {os.environ.get('BRANCH', 'N/A')}
- Commit: {os.environ.get('COMMIT_SHA', 'N/A')}
"""
            
            # Add log file content if provided
            if log_file and os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    log_content = f.read()
                body += f"\n\nCI Log:\n{log_content}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"Notification sent successfully: {status} - {message}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")
            return False

# For testing directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    notifier = CINotifier()
    # Create a test log file
    with open('test_log.txt', 'w') as f:
        f.write("This is a test log\nWith multiple lines\nTesting CI notification")
    
    # Test both success and failure notifications
    notifier.send_notification("SUCCESS", "Test build completed successfully", "test_log.txt")
    notifier.send_notification("FAILURE", "Test build failed: Error in unit tests", "test_log.txt")
