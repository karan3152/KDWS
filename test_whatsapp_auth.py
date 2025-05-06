import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Try to import webdriver_manager, install if not available
try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("Installing webdriver-manager...")
    import subprocess
    subprocess.check_call(["pip", "install", "webdriver-manager"])
    from webdriver_manager.chrome import ChromeDriverManager

def setup_whatsapp_session():
    """Set up WhatsApp Web session by scanning QR code."""
    print("Setting up WhatsApp Web session...")
    
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Add user data directory to maintain session
    user_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whatsapp_session')
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
            qr_code = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
            )
            print("WhatsApp QR code detected. Please scan it with your phone to authenticate.")
            print("1. Open WhatsApp on your phone")
            print("2. Tap Menu or Settings and select Linked Devices")
            print("3. Tap on 'Link a Device'")
            print("4. Point your phone to this screen to capture the QR code")
            
            # Wait for manual scan (up to 60 seconds)
            WebDriverWait(driver, 60).until_not(
                EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
            )
            print("WhatsApp authentication successful!")
            
            # Wait a bit to make sure everything is loaded
            time.sleep(5)
            
        except TimeoutException:
            # QR code not found, assuming already authenticated
            print("WhatsApp already authenticated.")
        
        # Test sending a message to yourself (optional)
        test_message = input("Do you want to test sending a message? (y/n): ")
        if test_message.lower() == 'y':
            phone_number = input("Enter your phone number with country code (e.g., 919876543210): ")
            message = "Test message from WhatsApp Web automation"
            
            # Navigate to chat
            driver.get(f"https://web.whatsapp.com/send?phone={phone_number}&text={message}")
            
            # Wait for send button and click it
            send_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//span[@data-icon='send']"))
            )
            send_button.click()
            print("Test message sent successfully!")
            time.sleep(5)
        
        print("WhatsApp Web setup completed successfully!")
        driver.quit()
        return True
        
    except Exception as e:
        print(f"Error setting up WhatsApp Web: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return False

if __name__ == "__main__":
    setup_whatsapp_session()
