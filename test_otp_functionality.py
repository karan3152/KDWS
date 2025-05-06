import os
import sys
from dotenv import load_dotenv
from app import app
from models import User, OTP, db
from utils.otp_utils import send_otp

# Load environment variables
load_dotenv()

def test_otp_functionality():
    """Test the OTP functionality by generating and sending an OTP."""
    print("OTP Functionality Test")
    print("=====================")
    
    # Get test email
    test_email = input("Enter test email address: ").strip()
    if not test_email:
        print("Email address is required.")
        return
    
    # Get test phone number (optional)
    test_phone = input("Enter test phone number (optional): ").strip()
    
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
    test_otp_functionality()
