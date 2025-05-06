import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_gmail_settings():
    """Check if the Gmail account is properly configured for sending emails."""
    # Get email configuration from environment variables
    sender_email = os.environ.get('EMAIL_USER')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    smtp_server = os.environ.get('SMTP_SERVER')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    
    print(f"Checking Gmail settings for {sender_email}")
    print(f"SMTP Server: {smtp_server}")
    print(f"SMTP Port: {smtp_port}")
    
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
        
        # Check connection
        print("Checking connection")
        server.noop()
        
        # Close connection
        server.quit()
        
        print("\nGmail account is properly configured for sending emails.")
        print("If you're not receiving emails, check the following:")
        print("1. Check your spam/junk folder")
        print("2. Make sure 'Less secure app access' is enabled in your Google account settings")
        print("3. If you have 2-factor authentication enabled, use an App Password instead of your regular password")
        print("4. Check if your Gmail account has any sending limits or restrictions")
        
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"\nSMTP Authentication Error: {str(e)}")
        print("This usually means your password is incorrect or Google is blocking the login attempt.")
        print("Possible solutions:")
        print("1. Make sure your EMAIL_PASSWORD in .env is correct")
        print("2. If you have 2-factor authentication enabled, use an App Password instead of your regular password")
        print("3. Enable 'Less secure app access' in your Google account settings")
        print("4. Check if your account has been locked due to suspicious activity")
        return False
    except smtplib.SMTPException as e:
        print(f"\nSMTP Error: {str(e)}")
        return False
    except Exception as e:
        print(f"\nFailed to check Gmail settings: {str(e)}")
        return False

if __name__ == "__main__":
    check_gmail_settings()
