from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException
import time
import json
import requests
from PIL import Image
import io
import easyocr
import numpy as np

# Your credentials
USERNAME = "6387980386"
PASSWORD = "12345678"
OTP_VALUE = "12345g"  # constant for now
LOGIN_URL = "https://onlinebooking.sand.telangana.gov.in/Masters/Home.aspx"

# Set up Selenium
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=chrome_options)
driver.get(LOGIN_URL)

# Wait for page to load
time.sleep(3)

# Handle any initial alerts
try:
    alert = driver.switch_to.alert
    alert.accept()
    print("[INFO] Initial alert accepted")
except NoAlertPresentException:
    pass

# Find username input and fill it
username_input = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located(
        (
            By.XPATH,
            "//td[contains(text(), 'User name')]/following-sibling::td//input[@type='text']",
        )
    )
)
username_input.clear()
username_input.send_keys(USERNAME)

# Find password input and fill it
password_input = driver.find_element(
    By.XPATH,
    "//td[contains(text(), 'Password')]/following-sibling::td//input[@type='password']",
)
password_input.clear()
password_input.send_keys(PASSWORD)

# Wait for captcha image
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "imgCaptcha")))

# Extract captcha image
captcha_url = driver.find_element(By.ID, "imgCaptcha").get_attribute("src")
print("[INFO] Captcha Image URL:", captcha_url)

# Create an EasyOCR reader for English
reader = easyocr.Reader(["en"])

# Download captcha
response = requests.get(captcha_url)

# Convert to NumPy array
captcha_image = Image.open(io.BytesIO(response.content))
captcha_np = np.array(captcha_image)

# Read text from captcha
captcha_results = reader.readtext(captcha_np, detail=0)
captcha_text = captcha_results[0] if captcha_results else ""
captcha_text = captcha_text.strip()

print(f"[INFO] Extracted Captcha Text: {captcha_text}")

# Fill captcha
captcha_field = driver.find_element(By.ID, "txtEnterCode")
captcha_field.clear()
captcha_field.send_keys(captcha_text)

# Wait for login button to become enabled (after timer)
print("[INFO] Waiting for login button to be enabled...")
try:
    login_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.ID, "btnLogin"))
    )

    # Click the login button
    print("[INFO] Clicking login button...")
    
    # Handle any alerts that might appear
    try:
        login_button.click()
        print("[INFO] Login button clicked successfully")
    except UnexpectedAlertPresentException as e:
        print(f"[ALERT] Alert appeared: {e.alert_text}")
        alert = driver.switch_to.alert
        alert.accept()
        print("[INFO] Alert accepted")

    # Wait for response
    time.sleep(5)

    # Check for any alerts
    try:
        alert = driver.switch_to.alert
        print(f"[ALERT] Alert text: {alert.text}")
        alert.accept()
        print("[INFO] Alert accepted")
    except NoAlertPresentException:
        pass

    # Check current state
    current_url = driver.current_url
    print(f"[INFO] Current URL: {current_url}")

    # Check if OTP form is available
    try:
        # Check if OTP modal is displayed
        otp_modal = driver.find_element(By.ID, "myModal")
        if otp_modal.is_displayed():
            print("[SUCCESS] OTP modal appeared")

            # Find OTP input field
            otp_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "txtCOTP"))
            )
            otp_input.clear()
            otp_input.send_keys(OTP_VALUE)
            print("[INFO] OTP entered")

            # Find submit button
            otp_submit = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.ID, "btnCOTPSubmit"))
            )
            
            # Ensure button is visible and clickable
            driver.execute_script("arguments[0].scrollIntoView(true);", otp_submit)
            time.sleep(1)
            
            # Click OTP submit button
            try:
                otp_submit.click()
                print("[SUCCESS] OTP submitted")
                
                # Wait for response
                time.sleep(3)
                
                # Check for any alerts after OTP
                try:
                    alert = driver.switch_to.alert
                    print(f"[ALERT] After OTP: {alert.text}")
                    alert.accept()
                except NoAlertPresentException:
                    print("[SUCCESS] No alerts after OTP submission")
                    
            except UnexpectedAlertPresentException as e:
                print(f"[ALERT] After OTP click: {e.alert_text}")
                alert = driver.switch_to.alert
                alert.accept()
                
    except Exception as e:
        print(f"[INFO] Checking page state: {e}")
        
        # Check for any error messages on page
        try:
            error_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(text(), 'invalid')]")
            for error in error_elements:
                print(f"[ERROR] Found error: {error.text}")
        except:
            pass

except Exception as e:
    print(f"[ERROR] Failed during login process: {e}")

# Keep browser open for verification
time.sleep(30)
driver.quit()
