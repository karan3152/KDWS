import os
import sys
import shutil
from utils.whatsapp_utils import setup_whatsapp_session, send_whatsapp_message

def main():
    print("WhatsApp Web Setup and Test Utility")
    print("===================================")

    # Ask if user wants to clear existing session
    clear_session = input("Do you want to clear existing WhatsApp session? (y/n): ").strip().lower()
    if clear_session == 'y':
        user_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whatsapp_session')
        if os.path.exists(user_data_dir):
            try:
                shutil.rmtree(user_data_dir)
                print(f"Cleared WhatsApp session directory: {user_data_dir}")
            except Exception as e:
                print(f"Failed to clear WhatsApp session directory: {str(e)}")

    # Set up WhatsApp session
    print("\nSetting up WhatsApp session...")
    success = setup_whatsapp_session()

    if not success:
        print("Failed to set up WhatsApp session. Please try again.")
        return

    # Test sending a message
    test_message = input("\nDo you want to test sending a message? (y/n): ").strip().lower()
    if test_message == 'y':
        phone_number = input("Enter your phone number with country code (e.g., 919876543210): ").strip()
        message = "Test message from KDWS WhatsApp OTP system"

        print(f"\nSending test message to {phone_number}...")
        if send_whatsapp_message(phone_number, message):
            print("Test message sent successfully!")
        else:
            print("Failed to send test message. Check the logs for details.")

    print("\nSetup complete!")

if __name__ == "__main__":
    main()
