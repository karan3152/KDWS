import os
import sys
from dotenv import load_dotenv
from utils.otp_utils import send_otp_via_email

# Load environment variables from .env file
load_dotenv()

def test_otp_email(recipient_email):
    """Send a test OTP email to verify the OTP email functionality.
    
    Args:
        recipient_email: The recipient's email address
    """
    # Generate a test OTP code
    otp_code = "123456"
    
    # Send OTP via email
    print(f"Sending test OTP email to {recipient_email}")
    result = send_otp_via_email(recipient_email, otp_code, 'password_reset')
    
    if result:
        print(f"Test OTP email sent successfully to {recipient_email}")
    else:
        print(f"Failed to send test OTP email to {recipient_email}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_otp_send.py recipient@example.com")
        sys.exit(1)
    
    recipient_email = sys.argv[1]
    test_otp_email(recipient_email)
