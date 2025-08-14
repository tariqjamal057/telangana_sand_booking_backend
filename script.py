from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    UnexpectedAlertPresentException,
    NoAlertPresentException,
)
import time
import requests
from PIL import Image
import io
import easyocr
import numpy as np

USERNAME = "8838051718"
PASSWORD = "12345678"
LOGIN_URL = "https://onlinebooking.sand.telangana.gov.in/Masters/Home.aspx"

chrome_options = Options()
chrome_options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)


def fill_login_details():
    """Fills username, password, captcha. Returns False if password not encrypted."""

    try:
        modal = driver.find_element(By.CLASS_NAME, "modal")
        if modal.is_displayed():
            driver.execute_script("arguments[0].style.display = 'none';", modal)
            print("[INFO] Closed blocking modal")
    except:
        pass

    # Fill username first
    username_input = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//td[contains(text(), 'User name')]/following-sibling::td//input[@type='text']",
            )
        )
    )
    username_input.clear()
    username_input.send_keys(USERNAME)

    # Fill password
    password_input = driver.find_element(
        By.XPATH,
        "//td[contains(text(), 'Password')]/following-sibling::td//input[@type='password']",
    )
    print("Before adding ", password_input.get_attribute("value"))
    password_input.clear()
    password_input.send_keys(PASSWORD)

    # Blur to trigger encryption
    driver.execute_script("arguments[0].blur();", password_input)
    time.sleep(0.5)  # give time for JS encryption

    print("After adding ", password_input.get_attribute("value"))

    # Check encryption
    if PASSWORD == password_input.get_attribute("value"):
        print("[WARN] Password is still plain text — encryption failed.")
        return False
    else:
        print("[INFO] Password is encrypted.")

    # Solve captcha
    wait.until(EC.presence_of_element_located((By.ID, "imgCaptcha")))
    captcha_url = driver.find_element(By.ID, "imgCaptcha").get_attribute("src")
    print("[INFO] Captcha Image URL:", captcha_url)

    reader = easyocr.Reader(["en"])
    response = requests.get(captcha_url)
    captcha_image = Image.open(io.BytesIO(response.content))
    captcha_np = np.array(captcha_image)
    captcha_results = reader.readtext(captcha_np, detail=0)
    captcha_text = captcha_results[0] if captcha_results else ""
    captcha_text = captcha_text.strip()
    final_captcha_text = ""
    for char in captcha_text:
        if not char.isdigit():
            final_captcha_text += char.upper()
        else:
            final_captcha_text += char
    captcha_text = final_captcha_text.strip()

    print(f"[INFO] Extracted Captcha Text: {captcha_text}")

    captcha_field = driver.find_element(By.ID, "txtEnterCode")
    captcha_field.clear()
    captcha_field.send_keys(captcha_text)
    return True


def get_recent_otp():
    otp_response = requests.get(
        f"https://telangana-sand-booking-backend.onrender.com/otp/recent/?number={USERNAME}"
    )
    return otp_response.json()


def add_login_otp():
    OTP_VALUE = get_recent_otp()["otp_secret"]

    otp_input = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "txtCOTP"))
    )
    otp_input.clear()
    otp_input.send_keys(OTP_VALUE)
    print("[INFO] OTP entered")

    otp_submit = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.ID, "btnCOTPSubmit"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", otp_submit)
    time.sleep(1)
    otp_submit.click()
    print("[SUCCESS] OTP submitted")
    time.sleep(3)
    try:
        alert = driver.switch_to.alert
        print(f"[ALERT] After OTP: {alert.text}")
        alert.accept()
        return False
    except NoAlertPresentException:
        print("[SUCCESS] No alerts after OTP submission")

    return True


def process_login():
    """Clicks login and handles OTP."""
    print("[INFO] Waiting for login button to be enabled...")
    login_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.ID, "btnLogin"))
    )

    try:
        login_button.click()
        print("[INFO] Login button clicked successfully")
    except UnexpectedAlertPresentException as e:
        print(f"[ALERT] Alert appeared: {e.alert_text}")
        alert = driver.switch_to.alert
        alert.accept()
        print("[INFO] Alert accepted")

    time.sleep(5)
    try:
        alert = driver.switch_to.alert
        print(f"[ALERT] Alert text: {alert.text}")
        alert.accept()
        print("[INFO] Alert accepted")
    except NoAlertPresentException:
        pass

    current_url = driver.current_url
    print(f"[INFO] Current URL: {current_url}")

    try:
        otp_modal = driver.find_element(By.ID, "myModal")
        if otp_modal.is_displayed():
            print("[SUCCESS] OTP modal appeared")
            time.sleep(10)
            login_otp_verification = False

            for _ in range(3):
                if add_login_otp():
                    login_otp_verification = True
                    break

            if not login_otp_verification:
                login_otp_reset_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "btnCOTPResend"))
                )
                login_otp_reset_button.click()
                time.sleep(10)
                for _ in range(3):
                    if add_login_otp():
                        break

            return True
    except Exception as e:
        print(f"[INFO] Checking page state: {e}")
        return False


# === Main execution ===
driver.get(LOGIN_URL)
time.sleep(2)

# Retry loop if encryption fails
attempt = 0
for i in range(3):
    print(f"[INFO] Login attempt #{attempt}")
    if not fill_login_details():
        driver.refresh()
        time.sleep(2)
        continue
    else:
        if process_login():
            print("[SUCCESS] Login successful")
            break

time.sleep(30)
driver.quit()
