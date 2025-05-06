
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import webdriver_manager, install if not available
try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    logger.info("Installing webdriver-manager...")
    import subprocess
    subprocess.check_call(["pip", "install", "webdriver-manager"])
    from webdriver_manager.chrome import ChromeDriverManager

def check_whatsapp_session():
    """Check if WhatsApp Web session exists and is valid.
    
    Returns:
        bool: True if session is valid, False otherwise
    """
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode for checking
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Add user data directory to maintain session
    user_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'whatsapp_session')
    if not os.path.exists(user_data_dir):
        logger.info("WhatsApp session directory does not exist.")
        return False
        
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument("--profile-directory=Default")
    
    try:
        # Initialize WebDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Open WhatsApp Web
        driver.get("https://web.whatsapp.com/")
        
        # Wait for WhatsApp to load (check for side panel which indicates logged in state)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='side']"))
            )
            logger.info("WhatsApp session is valid.")
            driver.quit()
            return True
        except TimeoutException:
            logger.info("WhatsApp session is invalid or expired.")
            driver.quit()
            return False
            
    except Exception as e:
        logger.error(f"Error checking WhatsApp session: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return False

def setup_whatsapp_session():
    """Set up WhatsApp Web session by scanning QR code.
    
    Returns:
        bool: True if setup was successful, False otherwise
    """
    logger.info("Setting up WhatsApp Web session...")
    
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Add user data directory to maintain session
    user_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'whatsapp_session')
    os.makedirs(user_data_dir, exist_ok=True)
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument("--profile-directory=Default")
    
    try:
        # Initialize WebDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Open WhatsApp Web
        driver.get("https://web.whatsapp.com/")
        
        # Check if QR code is present (needs authentication)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
            )
            logger.info("WhatsApp QR code detected. Please scan it with your phone to authenticate.")
            logger.info("1. Open WhatsApp on your phone")
            logger.info("2. Tap Menu or Settings and select Linked Devices")
            logger.info("3. Tap on 'Link a Device'")
            logger.info("4. Point your phone to this screen to capture the QR code")
            
            # Wait for manual scan (up to 60 seconds)
            WebDriverWait(driver, 60).until_not(
                EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
            )
            logger.info("WhatsApp authentication successful!")
            
            # Wait a bit to make sure everything is loaded
            time.sleep(5)
            
        except TimeoutException:
            # QR code not found, assuming already authenticated
            logger.info("WhatsApp already authenticated.")
        
        # Verify authentication by checking for side panel
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='side']"))
            )
            logger.info("WhatsApp Web setup completed successfully!")
            driver.quit()
            return True
        except TimeoutException:
            logger.error("Failed to authenticate with WhatsApp Web.")
            driver.quit()
            return False
        
    except Exception as e:
        logger.error(f"Error setting up WhatsApp Web: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return False

def send_whatsapp_message(phone_number, message):
    """Send a WhatsApp message using Selenium.
    
    Args:
        phone_number: The recipient's phone number (with country code, no spaces or symbols)
        message: The message to send
    
    Returns:
        bool: True if the message was sent successfully, False otherwise
    """
    # Check if session is valid, if not, set up a new one
    if not check_whatsapp_session():
        if not setup_whatsapp_session():
            logger.error("Failed to set up WhatsApp session.")
            return False
    
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Add user data directory to maintain session
    user_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'whatsapp_session')
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument("--profile-directory=Default")
    
    try:
        # Initialize WebDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Navigate to chat with the phone number
        driver.get(f"https://web.whatsapp.com/send?phone={phone_number}&text={message}")
        
        # Wait for WhatsApp to load and for the send button to be clickable
        send_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Send"]'))
        )
        
        # Click the send button
        send_button.click()
        
        # Wait for the message to be sent
        time.sleep(5)
        
        logger.info(f"WhatsApp message sent to {phone_number}")
        driver.quit()
        return True
    except TimeoutException:
        logger.error("Timed out waiting for WhatsApp Web to load or send button to be clickable")
        if 'driver' in locals():
            driver.quit()
        return False
    except NoSuchElementException:
        logger.error("Could not find the send button element")
        if 'driver' in locals():
            driver.quit()
        return False
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return False

