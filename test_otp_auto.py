import os
import sys
from dotenv import load_dotenv
from app import app
from models import User, OTP, db
from utils.otp_utils import send_otp

# Load environment variables
load_dotenv()

def test_otp_functionality(test_email="karanr3152@gmail.com"):
    """Test the OTP functionality by generating and sending an OTP."""
    print("OTP Functionality Test")
    print("=====================")

    print(f"Testing with email: {test_email}")

    with app.app_context():
        # Find user by email
        user = User.query.filter_by(email=test_email).first()
        if not user:
            print(f"No user found with email: {test_email}")
            return

        print(f"Found user: {user.username} (ID: {user.id})")

        # Generate OTP
        print("Generating OTP...")
        otp = OTP.generate_otp(user.id, 'password_reset')
        print(f"OTP generated: {otp.otp_code}")

        # Send OTP
        print("Sending OTP...")
        email_sent, whatsapp_sent = send_otp(user, otp.otp_code, 'password_reset')

        # Print results
        print("\nResults:")
        print(f"Email OTP sent: {'Success' if email_sent else 'Failed'}")
        print(f"WhatsApp OTP sent: {'Success' if whatsapp_sent else 'Failed'}")

        if email_sent or whatsapp_sent:
            print("\nOTP system is working!")
        else:
            print("\nOTP system is not working. Check the logs for details.")

if __name__ == "__main__":
    # Use command line argument if provided, otherwise use default
    test_email = sys.argv[1] if len(sys.argv) > 1 else "karanr3152@gmail.com"
    test_otp_functionality(test_email)
