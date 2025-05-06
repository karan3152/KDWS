import os
import time
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .whatsapp_utils import send_whatsapp_message

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def send_otp_via_email(recipient_email, otp_code, purpose):
    """Send OTP via email.

    Args:
        recipient_email: The recipient's email address
        otp_code: The OTP code to send
        purpose: The purpose of the OTP ('password_reset' or 'account_activation')

    Returns:
        True if the email was sent successfully, False otherwise
    """
    # Email configuration
    sender_email = os.environ.get('EMAIL_USER', 'your_email@example.com')
    sender_password = os.environ.get('EMAIL_PASSWORD', 'your_email_password')
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))

    # Log email configuration (without password)
    logger.debug(f"Email Configuration: Server={smtp_server}, Port={smtp_port}, From={sender_email}")
    logger.debug(f"Recipient email: {recipient_email}")

    # Check if email configuration is valid
    if sender_email == 'your_email@example.com' or sender_password == 'your_email_password':
        logger.error("Email configuration is using default values. Please set EMAIL_USER and EMAIL_PASSWORD in .env file.")
        return False

    # Create message
    msg = MIMEMultipart()
    msg['From'] = f"HRTS_KARAN <{sender_email}>"
    msg['To'] = recipient_email
    msg['Reply-To'] = sender_email

    # Add additional headers to improve deliverability
    msg.add_header('X-Priority', '1')  # High priority
    msg.add_header('X-MSMail-Priority', 'High')
    msg.add_header('Importance', 'High')

    if purpose == 'password_reset':
        msg['Subject'] = 'Your Password Reset Code - HRTS_KARAN'
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <h2 style="color: #333;">Password Reset Request</h2>
            <p>You have requested to reset your password for your HRTS_KARAN account.</p>
            <p>Your verification code is: <strong style="font-size: 18px; background: #f5f5f5; padding: 5px 10px; border-radius: 3px;">{otp_code}</strong></p>
            <p>This code will expire in 5 minutes.</p>
            <p>If you did not request this password reset, please ignore this email.</p>
            <p>Thank you,<br>HRTS_KARAN Team</p>
        </body>
        </html>
        """
    else:  # account_activation
        msg['Subject'] = 'Your Account Activation Code - HRTS_KARAN'
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <h2 style="color: #333;">Account Activation</h2>
            <p>Welcome to HRTS_KARAN! To activate your account, please use the following verification code:</p>
            <p>Your verification code is: <strong style="font-size: 18px; background: #f5f5f5; padding: 5px 10px; border-radius: 3px;">{otp_code}</strong></p>
            <p>This code will expire in 5 minutes.</p>
            <p>Thank you,<br>HRTS_KARAN Team</p>
        </body>
        </html>
        """

    msg.attach(MIMEText(body, 'html'))

    try:
        # Connect to SMTP server
        logger.debug(f"Connecting to SMTP server {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.set_debuglevel(1)  # Enable debug output

        # Start TLS
        logger.debug("Starting TLS")
        server.starttls()

        # Login
        logger.debug(f"Logging in as {sender_email}")
        server.login(sender_email, sender_password)

        # Send email
        logger.debug(f"Sending email to {recipient_email}")
        server.send_message(msg)

        # Verify delivery
        logger.debug("Verifying email delivery")
        server.noop()  # Check connection is still alive

        # Close connection
        server.quit()

        logger.info(f"OTP email sent successfully to {recipient_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {str(e)}. Please check your email credentials.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to send OTP email: {str(e)}")
        return False


def send_otp_via_whatsapp(phone_number, otp_code, purpose):
    """Send OTP via WhatsApp using Selenium.

    Args:
        phone_number: The recipient's phone number (with country code, no spaces or symbols)
        otp_code: The OTP code to send
        purpose: The purpose of the OTP ('password_reset' or 'account_activation')

    Returns:
        True if the message was sent successfully, False otherwise
    """
    # Prepare message based on purpose
    if purpose == 'password_reset':
        message = f"Your HRTS_KARAN password reset OTP is: {otp_code}. This OTP will expire in 5 minutes."
    else:  # account_activation
        message = f"Your HRTS_KARAN account activation OTP is: {otp_code}. This OTP will expire in 5 minutes."

    # Use the WhatsApp utility to send the message
    from .whatsapp_utils import send_whatsapp_message
    return send_whatsapp_message(phone_number, message)


def send_otp(user, otp_code, purpose, provided_phone=None):
    """Send OTP via both email and WhatsApp.

    Args:
        user: The User object
        otp_code: The OTP code to send
        purpose: The purpose of the OTP ('password_reset' or 'account_activation')
        provided_phone: Optional phone number provided by the user in the form

    Returns:
        A tuple (email_sent, whatsapp_sent) indicating whether each method was successful
    """
    logger.debug(f"Sending OTP to user {user.id} for purpose: {purpose}")
    logger.debug(f"OTP code: {otp_code}")
    logger.debug(f"User email: {user.email}")

    # Send via email
    email_sent = False
    try:
        email_sent = send_otp_via_email(user.email, otp_code, purpose)
        if email_sent:
            logger.info(f"Email OTP sent successfully to {user.email}")
        else:
            logger.warning(f"Failed to send OTP via email to {user.email}")
    except Exception as e:
        logger.error(f"Exception while sending email OTP: {str(e)}")

    # Use provided phone number if available, otherwise try to get from profile
    phone_number = provided_phone
    if not phone_number:
        if user.is_employee() and user.employee_profile:
            phone_number = user.employee_profile.phone_number
            logger.info(f"Using employee profile phone number: {phone_number}")
        elif user.is_employer() and user.employer_profile:
            phone_number = user.employer_profile.company_phone
            logger.info(f"Using employer profile phone number: {phone_number}")
        else:
            logger.warning("No phone number found in user profile")

    # Send via WhatsApp if phone number is available
    whatsapp_sent = False
    if phone_number:
        try:
            # Format phone number (remove spaces, dashes, etc.)
            formatted_phone = ''.join(filter(str.isdigit, phone_number))
            logger.info(f"Formatted phone number: {formatted_phone}")

            # Add country code if not present (assuming India +91 as default)
            if len(formatted_phone) == 10:  # Indian mobile number without country code
                formatted_phone = '91' + formatted_phone
                logger.info(f"Added country code: {formatted_phone}")

            # Try to send via WhatsApp API first
            try:
                from .whatsapp_api import send_whatsapp_message_api
                whatsapp_sent = send_whatsapp_message_api(formatted_phone, f"Your OTP is: {otp_code}")
                if whatsapp_sent:
                    logger.info(f"WhatsApp OTP sent via API to {formatted_phone}")
                else:
                    logger.warning(f"Failed to send OTP via WhatsApp API, trying fallback method")
            except Exception as e:
                logger.error(f"Error using WhatsApp API: {str(e)}")

            # If API method failed, try Selenium method
            if not whatsapp_sent:
                whatsapp_sent = send_otp_via_whatsapp(formatted_phone, otp_code, purpose)
                if whatsapp_sent:
                    logger.info(f"WhatsApp OTP sent via Selenium to {formatted_phone}")
                else:
                    logger.warning(f"Failed to send OTP via WhatsApp Selenium method")
        except Exception as e:
            logger.error(f"Exception while sending WhatsApp OTP: {str(e)}")
    else:
        logger.warning("No phone number available for WhatsApp OTP")

    # If both methods failed, log a critical error
    if not email_sent and not whatsapp_sent:
        logger.critical(f"Failed to send OTP to user {user.id} via any method")

    return (email_sent, whatsapp_sent)
