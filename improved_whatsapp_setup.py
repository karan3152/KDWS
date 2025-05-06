import os
import time
import sys
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("WhatsAppSetup")

def clear_whatsapp_session():
    """Clear the WhatsApp session directory."""
    user_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whatsapp_session')
    if os.path.exists(user_data_dir):
        import shutil
        try:
            shutil.rmtree(user_data_dir)
            logger.info(f"Cleared WhatsApp session directory: {user_data_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear WhatsApp session directory: {str(e)}")
            return False
    return True

def setup_whatsapp():
    """Set up WhatsApp Web with improved error handling."""
    logger.info("Starting WhatsApp Web setup...")
    
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # Start maximized
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Add user data directory to maintain session
    user_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whatsapp_session')
    os.makedirs(user_data_dir, exist_ok=True)
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument("--profile-directory=Default")
    
    # Add user agent to avoid detection
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    try:
        # Initialize WebDriver
        logger.info("Initializing Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Open WhatsApp Web
        logger.info("Opening WhatsApp Web...")
        driver.get("https://web.whatsapp.com/")
        
        # Wait for initial page load
        time.sleep(5)
        
        # Check if QR code is present (needs authentication)
        try:
            logger.info("Checking for QR code...")
            qr_code = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
            )
            logger.info("QR code detected. Please scan with your phone.")
            print("\n" + "="*50)
            print("SCAN QR CODE WITH YOUR PHONE")
            print("1. Open WhatsApp on your phone")
            print("2. Tap Menu or Settings and select Linked Devices")
            print("3. Tap on 'Link a Device'")
            print("4. Point your phone to this screen to capture the QR code")
            print("="*50 + "\n")
            
            # Wait for manual scan (up to 2 minutes)
            WebDriverWait(driver, 120).until_not(
                EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
            )
            logger.info("QR code scan detected!")
            
            # Wait for WhatsApp to fully load after authentication
            time.sleep(10)
            
        except TimeoutException:
            # QR code not found, assuming already authenticated
            logger.info("No QR code found. Assuming already authenticated.")
        
        # Verify authentication by checking for side panel or chat list
        try:
            logger.info("Verifying authentication...")
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='side']"))
            )
            logger.info("Authentication verified successfully!")
            
            # Test sending a message if requested
            test_message = input("Do you want to test sending a message? (y/n): ").strip().lower()
            if test_message == 'y':
                phone_number = input("Enter your phone number with country code (e.g., 919876543210): ").strip()
                message = "Test message from WhatsApp Web automation"
                
                try:
                    # Navigate to chat with proper URL encoding
                    import urllib.parse
                    encoded_message = urllib.parse.quote(message)
                    logger.info(f"Opening chat with {phone_number}...")
                    driver.get(f"https://web.whatsapp.com/send?phone={phone_number}&text={encoded_message}")
                    
                    # Wait longer for the chat to load
                    logger.info("Waiting for chat to load (this may take up to 30 seconds)...")
                    time.sleep(10)  # Initial wait
                    
                    # Wait for send button with multiple attempts
                    max_attempts = 3
                    for attempt in range(max_attempts):
                        try:
                            logger.info(f"Looking for send button (attempt {attempt+1}/{max_attempts})...")
                            send_button = WebDriverWait(driver, 20).until(
                                EC.element_to_be_clickable((By.XPATH, "//span[@data-icon='send']"))
                            )
                            
                            # Take a screenshot before clicking
                            screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whatsapp_screenshot.png')
                            driver.save_screenshot(screenshot_path)
                            logger.info(f"Screenshot saved to {screenshot_path}")
                            
                            # Click the send button
                            logger.info("Clicking send button...")
                            send_button.click()
                            
                            # Wait for message to be sent
                            time.sleep(5)
                            logger.info("Test message sent successfully!")
                            break
                        except (TimeoutException, NoSuchElementException) as e:
                            if attempt < max_attempts - 1:
                                logger.warning(f"Attempt {attempt+1} failed: {str(e)}. Retrying...")
                                time.sleep(5)  # Wait before retrying
                            else:
                                logger.error(f"Failed to find or click send button after {max_attempts} attempts")
                                raise
                except Exception as e:
                    logger.error(f"Error sending test message: {str(e)}")
            
            logger.info("WhatsApp Web setup completed successfully!")
            input("Press Enter to close the browser and exit...")
            driver.quit()
            return True
            
        except TimeoutException:
            logger.error("Failed to verify WhatsApp authentication. Side panel not found.")
            driver.quit()
            return False
            
    except WebDriverException as e:
        logger.error(f"WebDriver error: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return False

if __name__ == "__main__":
    # Ask if user wants to clear existing session
    clear_session = input("Do you want to clear existing WhatsApp session? (y/n): ").strip().lower()
    if clear_session == 'y':
        clear_whatsapp_session()
    
    # Run the setup
    setup_whatsapp()
