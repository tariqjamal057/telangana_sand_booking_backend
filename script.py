import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
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


def extract_captcha_text(captcha_url):
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
    return captcha_text


def extract_captcha_text_from_base64(data_url):
    """Handles base64 inline captchas (data:image/...)"""
    header, encoded = data_url.split(",", 1)
    image_bytes = base64.b64decode(encoded)
    captcha_image = Image.open(io.BytesIO(image_bytes))
    captcha_np = np.array(captcha_image)

    reader = easyocr.Reader(["en"])
    captcha_results = reader.readtext(captcha_np, detail=0)
    captcha_text = captcha_results[0] if captcha_results else ""
    return captcha_text.strip()


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

    wait.until(EC.presence_of_element_located((By.ID, "imgCaptcha")))
    captcha_url = driver.find_element(By.ID, "imgCaptcha").get_attribute("src")
    captcha_text = extract_captcha_text(captcha_url)

    print(f"[INFO] Extracted Captcha Text: {captcha_text}")

    captcha_field = driver.find_element(By.ID, "txtEnterCode")
    captcha_field.clear()
    captcha_field.send_keys(captcha_text)
    return True


def get_recent_otp():
    otp_response = requests.get(
        f"https://bhaktabhim.duckdns.org/otp/recent/?number={USERNAME}"
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


def handle_already_logged_in(driver, wait):
    try:
        # Check if logout form is present
        logout_table = driver.find_elements(By.ID, "tblLogOut")
        if logout_table and logout_table[0].is_displayed():
            print("[WARN] Already logged in session detected. Logging out...")

            # Click the logout button
            logout_button = wait.until(EC.element_to_be_clickable((By.ID, "btnLogout")))
            logout_button.click()

            # Wait until login form comes back
            wait.until(EC.visibility_of_element_located((By.ID, "tblLogIn")))
            print("[INFO] Successfully logged out of old session.")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to handle already logged in state: {e}")
        return False


def process_login():
    """Clicks login and handles OTP."""
    print("[INFO] Waiting for login button to be enabled...")
    # register_btn = WebDriverWait(driver, 20).until(
    #     EC.presence_of_element_located((By.ID, "btnRegister"))
    # )

    # # Force show + enable + click in one go
    # driver.execute_script(
    #     """
    #     arguments[0].style.display = 'block';
    #     arguments[0].disabled = false;
    #     arguments[0].click();
    # """,
    #     register_btn,
    # )

    login_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "btnLogin"))
    )

    try:
        #     login_button = WebDriverWait(driver, 20).until(
        #         EC.presence_of_element_located((By.ID, "btnLogin"))
        #     )
        #     driver.execute_script(
        #         """
        #     arguments[0].style.display = 'block';
        #     arguments[0].disabled = false;
        #     arguments[0].click();
        # """,
        #         login_button,
        #     )
        driver.execute_script("arguments[0].disabled = false;", login_button)
        login_button.click()
        print("[INFO] Login button clicked successfully")
    except UnexpectedAlertPresentException as e:
        print(f"[ALERT] Alert appeared: {e.alert_text}")
        alert = driver.switch_to.alert
        alert.accept()
        print("[INFO] Alert accepted")

    # if not handle_already_logged_in(driver, wait):
    #     return False

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


def navigate_to_new_booking():
    """Click NEW BOOKING and switch to popup window."""
    # Find <li id="liCustomerOrders"> and its <a> child
    new_booking_link = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//li[@id='liCustomerOrders']/a"))
    )
    driver.execute_script("arguments[0].click();", new_booking_link)
    print("[INFO] Clicked NEW BOOKING")

    # Handle popup window
    time.sleep(5)
    main_window = driver.current_window_handle
    for handle in driver.window_handles:
        if handle != main_window:
            driver.switch_to.window(handle)
            print("[INFO] Switched to NEW BOOKING popup")
            break


def select_district():
    """Select district with value 24 (BHADRADRI KOTHAGUDEM)."""
    label_td = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, "//td[@class='TopSearchCat' and contains(text(), 'District')]")
        )
    )

    dropdown = label_td.find_element(By.XPATH, "./following-sibling::td/select")

    select = Select(dropdown)
    select.select_by_value("24")
    print("[SUCCESS] District selected: 24")


def select_stockyard(driver, stockyard_name, timeout=30):
    """Select stockyard radio by name with fuzzy matching (works with dynamic table IDs)."""
    try:
        # Wait until at least one row is present
        rows = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located(
                (
                    By.XPATH,
                    "//table[contains(@class,'GridviewScrollTable')]//tr[contains(@class,'GridviewScrollItem')]",
                )
            )
        )
        print(f"[INFO] Stockyard table loaded with {len(rows)} rows")

        available = []
        target_radio = None

        for r in rows:
            try:
                name = r.find_element(By.XPATH, "./td[3]").text.strip()
                available.append(name)
                if stockyard_name.lower() in name.lower():
                    target_radio = r.find_element(By.XPATH, ".//input[@type='radio']")
            except Exception:
                continue

        print("[INFO] Available stockyards:", available)

        if not target_radio:
            print(f"[ERROR] Stockyard '{stockyard_name}' not found")
            return False

        driver.execute_script("arguments[0].click();", target_radio)
        print(f"[SUCCESS] Stockyard selected: {stockyard_name}")
        return True

    except Exception as e:
        print(f"[ERROR] select_stockyard failed: {e}")
        return False


def fill_customer_gstin(value="ABCDE1234F"):
    gst_input = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//th[contains(text(),'Customer GSTIN')]/following-sibling::td//input",
            )
        )
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", gst_input)
    gst_input.clear()
    gst_input.send_keys(value)
    print(f"[SUCCESS] Customer GSTIN entered: {value}")


def fill_vehicle_number(value="TS09AB1234"):
    """Fill Vehicle Number in the form."""
    veh_input = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//th[contains(text(),'Vehicle No')]/following-sibling::td//input",
            )
        )
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", veh_input)
    veh_input.clear()
    veh_input.send_keys(value)
    print(f"[SUCCESS] Vehicle Number entered: {value}")


def select_purpose_of_sand(value="1"):
    dropdown = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//th[contains(text(),'Purpose of Sand')]/following-sibling::td//select",
            )
        )
    )
    Select(dropdown).select_by_value(value)
    print(f"[SUCCESS] Purpose of Sand selected: {value}")


def fill_delivery_address(district="24", mandal="16", village=None):
    # District
    district_select = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//th[contains(text(),'District')]/following-sibling::td//select",
            )
        )
    )
    Select(district_select).select_by_value(district)
    print(f"[SUCCESS] Delivery District selected: {district}")
    time.sleep(2)

    # Mandal/Municipality
    mandal_select = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, "//th[contains(text(),'Mandal')]/following-sibling::td//select")
        )
    )
    Select(mandal_select).select_by_value(mandal)
    print(f"[SUCCESS] Mandal selected: {mandal}")
    time.sleep(2)

    # Village (optional)
    if village:
        village_select = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//th[contains(text(),'Village')]/following-sibling::td//select",
                )
            )
        )
        Select(village_select).select_by_value(village)
        print(f"[SUCCESS] Village selected: {village}")


def fill_captcha_and_payment():
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "ccMain_imgCaptcha"))
    )
    captcha_url = driver.find_element(By.ID, "ccMain_imgCaptcha").get_attribute("src")

    if captcha_url.startswith("data:image"):
        captcha_text = extract_captcha_text_from_base64(captcha_url)
    else:
        captcha_text = extract_captcha_text(captcha_url)

    print(f"[INFO] Captcha extracted: {captcha_text}")

    captcha_input = driver.find_element(By.XPATH, "//input[@id='ccMain_txtCECode']")
    captcha_input.clear()
    captcha_input.send_keys(captcha_text)

    payu_radio = driver.find_element(
        By.XPATH, "//input[@type='radio' and @value='PAYU']"
    )
    driver.execute_script("arguments[0].click();", payu_radio)
    print("[SUCCESS] Payment Gateway selected: PAYU")


def select_delivery_slot_by_text(slot_text="14-08-2025 (12NOON - 06PM)"):
    """Select delivery slot by visible text instead of value."""
    try:
        slot_select = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//th[contains(text(),'Select Delivery Slot')]/following-sibling::td//select",
                )
            )
        )
        Select(slot_select).select_by_visible_text(slot_text)
        print(f"[SUCCESS] Delivery slot selected: {slot_text}")
    except Exception as e:
        print(f"[ERROR] select_delivery_slot_by_text failed: {e}")


def click_register():
    """Enable (force show) and click the Register button."""
    register_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "btnRegister"))
    )
    driver.execute_script("arguments[0].disabled = false;", register_btn)
    register_btn.click()

    print("[SUCCESS] Register button enabled and clicked")


# === Main execution ===
driver.get(LOGIN_URL)
time.sleep(2)

# Retry loop if encryption fails
attempt = 0
skip_fill_details = False
for i in range(3):
    print(f"[INFO] Login attempt #{attempt}")
    if not fill_login_details():
        driver.refresh()
        time.sleep(2)
        continue
    else:
        if process_login():
            print("[SUCCESS] Login successful")
            navigate_to_new_booking()
            select_district()
            select_stockyard(driver, "GP Palli De-Siltation(2025)")
            fill_customer_gstin("ABCDE1234F")
            select_purpose_of_sand("1")
            fill_delivery_address(district="24", mandal="14", village="001")
            fill_captcha_and_payment()
            fill_vehicle_number()
            select_delivery_slot_by_text()
            click_register()
            break


time.sleep(30)
# driver.quit()
