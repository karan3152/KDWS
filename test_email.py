import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def send_test_email(recipient_email):
    """Send a test email to verify SMTP configuration.

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

    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = 'Test Email from KDWS OTP System'

    body = """
    <html>
    <body>
        <h2>Test Email</h2>
        <p>This is a test email from the KDWS OTP system.</p>
        <p>If you received this email, the email configuration is working correctly.</p>
        <p>Thank you,<br>KDWS Team</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        # Connect to SMTP server
        print(f"\nConnecting to SMTP server {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()

        # Login to SMTP server
        print(f"Logging in as {sender_email}...")
        server.login(sender_email, sender_password)

        # Send email
        print(f"Sending email to {recipient_email}...")
        server.send_message(msg)
        server.quit()

        print("\nEmail sent successfully!")
        return True
    except Exception as e:
        print(f"\nError sending email: {str(e)}")
        return False

def main():
    print("Email Test Utility")
    print("=================")

    recipient_email = input("Enter the recipient email address: ").strip()
    if not recipient_email:
        print("Email address is required.")
        return

    send_test_email(recipient_email)

if __name__ == "__main__":
    main()
