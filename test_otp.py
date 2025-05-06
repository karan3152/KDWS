import os
import sys
import logging
from dotenv import load_dotenv
from models import User, OTP, db
from utils.otp_utils import send_otp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_otp_system():
    """Test the OTP system by generating and sending an OTP."""
    print("OTP System Test Utility")
    print("======================")
    
    # Get test email
    test_email = input("Enter test email address: ").strip()
    if not test_email:
        print("Email address is required.")
        return
    
    # Get test phone number
    test_phone = input("Enter test phone number with country code (e.g., 919876543210): ").strip()
    
    # Find or create a test user
    user = User.query.filter_by(email=test_email).first()
    if not user:
        print(f"No user found with email {test_email}. Creating a test user...")
        from werkzeug.security import generate_password_hash
        user = User(
            username="test_user",
            email=test_email,
            password_hash=generate_password_hash("test_password"),
            role="employee",
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        print(f"Test user created with ID: {user.id}")
    
    # Generate OTP
    print("Generating OTP...")
    otp = OTP.generate_otp(user.id, 'password_reset')
    print(f"OTP generated: {otp.otp_code}")
    
    # Send OTP
    print("Sending OTP...")
    email_sent, whatsapp_sent = send_otp(user, otp.otp_code, 'password_reset', test_phone)
    
    # Print results
    print("\nResults:")
    print(f"Email OTP sent: {'Success' if email_sent else 'Failed'}")
    print(f"WhatsApp OTP sent: {'Success' if whatsapp_sent else 'Failed'}")
    
    if email_sent or whatsapp_sent:
        print("\nOTP system is working!")
    else:
        print("\nOTP system is not working. Check the logs for details.")

if __name__ == "__main__":
    # Import Flask app context
    from app import app
    with app.app_context():
        test_otp_system()
