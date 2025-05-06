import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def test_email_delivery(recipient_email):
    """Send a test email to verify email delivery.

    Args:
        recipient_email: The recipient's email address

    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    # Get email configuration from environment variables
    sender_email = os.environ.get('EMAIL_USER')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    smtp_server = os.environ.get('SMTP_SERVER')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))

    # Print configuration (without password)
    print(f"Email Configuration:")
    print(f"  Sender: {sender_email}")
    print(f"  SMTP Server: {smtp_server}")
    print(f"  SMTP Port: {smtp_port}")
    print(f"  Recipient: {recipient_email}")

    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = 'Test Email Delivery from KDWS'

    body = """
    <html>
    <body>
        <h2>Test Email Delivery</h2>
        <p>This is a test email to verify that emails are being delivered correctly.</p>
        <p>If you received this email, the email delivery system is working properly.</p>
        <p>Thank you,<br>KDWS Team</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        # Connect to SMTP server
        print(f"Connecting to SMTP server {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.set_debuglevel(1)  # Enable debug output

        # Start TLS
        print("Starting TLS")
        server.starttls()

        # Login
        print(f"Logging in as {sender_email}")
        server.login(sender_email, sender_password)

        # Send email
        print(f"Sending email to {recipient_email}")
        server.send_message(msg)

        # Verify delivery
        print("Verifying email delivery")
        server.noop()  # Check connection is still alive

        # Close connection
        server.quit()

        print(f"Test email sent successfully to {recipient_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {str(e)}. Please check your email credentials.")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {str(e)}")
        return False
    except Exception as e:
        print(f"Failed to send test email: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_email_delivery.py recipient@example.com")
        sys.exit(1)

    recipient_email = sys.argv[1]
    test_email_delivery(recipient_email)
