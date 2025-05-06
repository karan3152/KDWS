import os
import requests
import logging
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WhatsApp API configuration
WHATSAPP_API_URL = os.environ.get('WHATSAPP_API_URL', '')
WHATSAPP_API_KEY = os.environ.get('WHATSAPP_API_KEY', '')

def send_whatsapp_message_api(phone_number, message):
    """Send a WhatsApp message using a third-party API service.

    Args:
        phone_number: The recipient's phone number (with country code, no spaces or symbols)
        message: The message to send

    Returns:
        bool: True if the message was sent successfully, False otherwise
    """
    # Check if WhatsApp API is configured
    if not WHATSAPP_API_URL or not WHATSAPP_API_KEY:
        logger.warning("WhatsApp API URL or API key not configured. Using fallback method.")
        return False

    # Log API configuration (without key)
    logger.info(f"WhatsApp API Configuration: URL={WHATSAPP_API_URL}")

    try:
        # Format phone number (remove any non-digit characters)
        formatted_phone = ''.join(filter(str.isdigit, phone_number))
        logger.info(f"Sending WhatsApp message to {formatted_phone}")

        # Prepare the API request
        headers = {
            'Authorization': f'Bearer {WHATSAPP_API_KEY}',
            'Content-Type': 'application/json'
        }

        payload = {
            'phone': formatted_phone,
            'message': message
        }

        # Log request details (without sensitive data)
        logger.info(f"Sending API request to {WHATSAPP_API_URL}")

        # Send the API request
        response = requests.post(WHATSAPP_API_URL, headers=headers, data=json.dumps(payload), timeout=30)

        # Check if the request was successful
        if response.status_code == 200:
            logger.info(f"WhatsApp message sent to {phone_number} via API")
            return True
        else:
            logger.error(f"Failed to send WhatsApp message via API. Status code: {response.status_code}, Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        logger.error("WhatsApp API request timed out")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("Connection error when calling WhatsApp API")
        return False
    except Exception as e:
        logger.error(f"Error sending WhatsApp message via API: {str(e)}")
        return False

# Function to determine which method to use
def send_whatsapp_message(phone_number, message):
    """Send a WhatsApp message using the best available method.

    Args:
        phone_number: The recipient's phone number (with country code, no spaces or symbols)
        message: The message to send

    Returns:
        bool: True if the message was sent successfully, False otherwise
    """
    # Try API method first if configured
    if WHATSAPP_API_URL and WHATSAPP_API_KEY:
        return send_whatsapp_message_api(phone_number, message)

    # Fall back to Selenium method
    try:
        from .whatsapp_utils import send_whatsapp_message as send_via_selenium
        return send_via_selenium(phone_number, message)
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message via Selenium: {str(e)}")
        return False
