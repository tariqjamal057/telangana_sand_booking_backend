import base64
import uuid
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
import tempfile

from .models import BookingMasterData


class SandBookingScript:
    def __init__(self, proxy=None, booking_master_id=None):
        # selenium
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")

        # 👇 still required on many Linux servers
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        # # 👇 unique user-data-dir every time
        # user_data_dir = tempfile.mkdtemp()
        # chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

        # 👇 unique profile directory every time
        # profile_name = f"profile_{uuid.uuid4().hex}"
        # chrome_options.add_argument(f"--profile-directory={profile_name}")

        # # 👇 unique debugging port (avoid collisions)
        # port = 9222 + int(uuid.uuid4().int % 1000)
        # chrome_options.add_argument(f"--remote-debugging-port={port}")

        # Configure proxy if provided
        # TODO: Need to diaable once issue fixed
        # if proxy:
        #     chrome_options.add_argument(f"--proxy-server={proxy}")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)

        # EasyOCR
        self.reader = easyocr.Reader(["en"])

        # Defaults
        self.username = None
        self.password = None
        self.stockyard_name = None
        self.district = None
        self.mandal = None
        self.village = None
        self.gstin = None
        self.vehicle_number = None
        self.purpose_of_sand = None
        self.slot_text = None
        self.login_url = "https://onlinebooking.sand.telangana.gov.in/Masters/Home.aspx"
        self.booking_master_id = booking_master_id

    def format_district_mandal_value(self, value, village=False):
        if len(str(value)) == 1 and not village:
            value = f"0{value}"

        if village:
            if len(str(value)) == 1:
                value = f"00{value}"
            elif len(str(value)) == 2:
                value = f"0{value}"

        return str(value)

    def initial_setup(self, booking_master_id=None):
        if booking_master_id:
            self.booking_master_id = booking_master_id

        booking_master = BookingMasterData.objects.get(id=self.booking_master_id)
        self.username = booking_master.booking_user.username
        self.password = booking_master.booking_user.password
        self.stockyard_name = booking_master.stockyard.name
        self.district = self.format_district_mandal_value(booking_master.district.did)
        self.delivery_district = self.format_district_mandal_value(
            booking_master.delivery_district.did
        )
        self.mandal = self.format_district_mandal_value(
            booking_master.delivery_mandal.mid
        )
        self.village = self.format_district_mandal_value(
            booking_master.delivery_village.vid
        )
        self.gstin = booking_master.gstin
        self.vehicle_number = booking_master.vehicle_no
        self.purpose_of_sand = str(booking_master.sand_purpose)
        self.slot_text = booking_master.delivery_slot
        self.payment_mode = booking_master.payment_mode

    def extract_captcha_text(self, captcha_url):
        print("[INFO] Captcha Image URL:", captcha_url)

        response = requests.get(captcha_url)
        captcha_image = Image.open(io.BytesIO(response.content))
        captcha_np = np.array(captcha_image)
        captcha_results = self.reader.readtext(captcha_np, detail=0)
        captcha_text = captcha_results[0] if captcha_results else ""
        captcha_text = captcha_text.strip()
        return "".join(
            [c.upper() if not c.isdigit() else c for c in captcha_text.strip()]
        )

    def extract_captcha_text_from_base64(self, data_url):
        """Handles base64 inline captchas (data:image/...)"""
        header, encoded = data_url.split(",", 1)
        image_bytes = base64.b64decode(encoded)
        captcha_image = Image.open(io.BytesIO(image_bytes))
        captcha_np = np.array(captcha_image)

        captcha_results = self.reader.readtext(captcha_np, detail=0)
        return captcha_results[0].strip() if captcha_results else ""

    def fill_login_details(self):
        """Fills username, password, captcha. Returns False if password not encrypted."""

        try:
            modal = self.driver.find_element(By.CLASS_NAME, "modal")
            if modal.is_displayed():
                self.driver.execute_script(
                    "arguments[0].style.display = 'none';", modal
                )
                print("[INFO] Closed blocking modal")
        except:
            pass

        # Fill username first
        username_input = self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//td[contains(text(), 'User name')]/following-sibling::td//input[@type='text']",
                )
            )
        )
        username_input.clear()
        username_input.send_keys(self.username)

        # Fill password
        password_input = self.driver.find_element(
            By.XPATH,
            "//td[contains(text(), 'Password')]/following-sibling::td//input[@type='password']",
        )
        print("Before adding ", password_input.get_attribute("value"))
        password_input.clear()
        password_input.send_keys(self.password)

        # Blur to trigger encryption
        self.driver.execute_script("arguments[0].blur();", password_input)
        time.sleep(0.5)  # give time for JS encryption

        print("After adding ", password_input.get_attribute("value"))

        # Check encryption
        if self.password == password_input.get_attribute("value"):
            print("[WARN] Password is still plain text — encryption failed.")
            return False
        else:
            print("[INFO] Password is encrypted.")

        self.wait.until(EC.presence_of_element_located((By.ID, "imgCaptcha")))
        captcha_url = self.driver.find_element(By.ID, "imgCaptcha").get_attribute("src")
        captcha_text = self.extract_captcha_text(captcha_url)

        print(f"[INFO] Extracted Captcha Text: {captcha_text}")

        captcha_field = self.driver.find_element(By.ID, "txtEnterCode")
        captcha_field.clear()
        captcha_field.send_keys(captcha_text)
        return True

    def get_recent_otp(self):
        otp_response = requests.get(
            f"https://bhaktabhim.duckdns.org/otp/recent/?number={self.username}"
        )
        return otp_response.json()

    def add_login_otp(self):
        OTP_VALUE = self.get_recent_otp()["otp_secret"]

        otp_input = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.ID, "txtCOTP"))
        )
        otp_input.clear()
        otp_input.send_keys(OTP_VALUE)
        print("[INFO] OTP entered")

        otp_submit = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.ID, "btnCOTPSubmit"))
        )
        self.driver.execute_script("arguments[0].scrollIntoView(true);", otp_submit)
        time.sleep(1)
        otp_submit.click()
        print("[SUCCESS] OTP submitted")
        time.sleep(3)
        try:
            alert = self.driver.switch_to.alert
            print(f"[ALERT] After OTP: {alert.text}")
            alert.accept()
            return False
        except NoAlertPresentException:
            print("[SUCCESS] No alerts after OTP submission")

        return True

    def handle_already_logged_in(self):
        try:
            # Check if logout form is present
            logout_table = self.driver.find_elements(By.ID, "tblLogOut")
            if logout_table and logout_table[0].is_displayed():
                print("[WARN] Already logged in session detected. Logging out...")

                # Click the logout button
                logout_button = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "btnLogout"))
                )
                logout_button.click()

                # Wait until login form comes back
                self.wait.until(EC.visibility_of_element_located((By.ID, "tblLogIn")))
                print("[INFO] Successfully logged out of old session.")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to handle already logged in state: {e}")
            return False

    def process_login(self):
        """Clicks login and handles OTP."""
        print("[INFO] Waiting for login button to be enabled...")

        login_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.ID, "btnLogin"))
        )

        try:
            self.driver.execute_script("arguments[0].disabled = false;", login_button)
            login_button.click()
            print("[INFO] Login button clicked successfully")
        except UnexpectedAlertPresentException as e:
            print(f"[ALERT] Alert appeared: {e.alert_text}")
            alert = self.driver.switch_to.alert
            alert.accept()
            print("[INFO] Alert accepted")

        # if not handle_already_logged_in(driver, wait):
        #     return False

        time.sleep(5)
        try:
            alert = self.driver.switch_to.alert
            print(f"[ALERT] Alert text: {alert.text}")
            alert.accept()
            print("[INFO] Alert accepted")
        except NoAlertPresentException:
            pass

        current_url = self.driver.current_url
        print(f"[INFO] Current URL: {current_url}")

        try:
            otp_modal = self.driver.find_element(By.ID, "myModal")
            if otp_modal.is_displayed():
                print("[SUCCESS] OTP modal appeared")
                time.sleep(10)
                login_otp_verification = False

                for _ in range(3):
                    if self.add_login_otp():
                        login_otp_verification = True
                        break

                if not login_otp_verification:
                    login_otp_reset_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "btnCOTPResend"))
                    )
                    login_otp_reset_button.click()
                    time.sleep(10)
                    for _ in range(3):
                        if self.add_login_otp():
                            break

                return True
        except Exception as e:
            print(f"[INFO] Checking page state: {e}")
            return False

    def navigate_to_new_booking(self):
        """Click NEW BOOKING and switch to popup window."""
        # Find <li id="liCustomerOrders"> and its <a> child
        new_booking_link = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//li[@id='liCustomerOrders']/a"))
        )
        self.driver.execute_script("arguments[0].click();", new_booking_link)
        print("[INFO] Clicked NEW BOOKING")

        # Handle popup window
        time.sleep(5)
        main_window = self.driver.current_window_handle
        for handle in self.driver.window_handles:
            if handle != main_window:
                self.driver.switch_to.window(handle)
                print("[INFO] Switched to NEW BOOKING popup")
                break

    def select_district(self):
        label_td = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//td[@class='TopSearchCat' and contains(text(), 'District')]",
                )
            )
        )

        dropdown = label_td.find_element(By.XPATH, "./following-sibling::td/select")

        select = Select(dropdown)
        select.select_by_value(self.district)
        print(f"[SUCCESS] District selected: {self.district}")

    def select_stockyard(self, timeout=30):
        """Select stockyard radio by name with fuzzy matching (works with dynamic table IDs)."""
        try:
            # Wait until at least one row is present
            rows = WebDriverWait(self.driver, timeout).until(
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
                    if self.stockyard_name.lower() in name.lower():
                        target_radio = r.find_element(
                            By.XPATH, ".//input[@type='radio']"
                        )
                except Exception:
                    continue

            print("[INFO] Available stockyards:", available)

            if not target_radio:
                print(f"[ERROR] Stockyard '{self.stockyard_name}' not found")
                return False

            self.driver.execute_script("arguments[0].click();", target_radio)
            print(f"[SUCCESS] Stockyard selected: {self.stockyard_name}")
            return True

        except Exception as e:
            print(f"[ERROR] select_stockyard failed: {e}")
            return False

    def fill_customer_gstin(self):
        gst_input = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//th[contains(text(),'Customer GSTIN')]/following-sibling::td//input",
                )
            )
        )
        self.driver.execute_script("arguments[0].scrollIntoView(true);", gst_input)
        gst_input.clear()
        gst_input.send_keys(self.gstin)
        print(f"[SUCCESS] Customer GSTIN entered: {self.gstin}")

    def fill_vehicle_number(self):
        """Fill Vehicle Number in the form."""
        veh_input = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//th[contains(text(),'Vehicle No')]/following-sibling::td//input",
                )
            )
        )
        self.driver.execute_script("arguments[0].scrollIntoView(true);", veh_input)
        veh_input.clear()
        veh_input.send_keys(self.vehicle_number)
        print(f"[SUCCESS] Vehicle Number entered: {self.vehicle_number}")

    def select_purpose_of_sand(self):
        dropdown = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//th[contains(text(),'Purpose of Sand')]/following-sibling::td//select",
                )
            )
        )
        Select(dropdown).select_by_value(self.purpose_of_sand)
        print(f"[SUCCESS] Purpose of Sand selected: {self.purpose_of_sand}")

    def fill_delivery_address(self):
        # District
        district_select = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//th[contains(text(),'District')]/following-sibling::td//select",
                )
            )
        )
        Select(district_select).select_by_value(self.delivery_district)
        print(f"[SUCCESS] Delivery District selected: {self.delivery_district}")
        time.sleep(2)

        # Mandal/Municipality
        mandal_select = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//th[contains(text(),'Mandal')]/following-sibling::td//select",
                )
            )
        )
        Select(mandal_select).select_by_value(self.mandal)
        print(f"[SUCCESS] Mandal selected: {self.mandal}")
        time.sleep(2)

        # Village (optional)
        if self.village:
            village_select = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//th[contains(text(),'Village')]/following-sibling::td//select",
                    )
                )
            )
            Select(village_select).select_by_value(self.village)
            print(f"[SUCCESS] Village selected: {self.village}")

    def fill_captcha_and_payment(self):
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.ID, "ccMain_imgCaptcha"))
        )
        captcha_url = self.driver.find_element(
            By.ID, "ccMain_imgCaptcha"
        ).get_attribute("src")

        if captcha_url.startswith("data:image"):
            captcha_text = self.extract_captcha_text_from_base64(captcha_url)
        else:
            captcha_text = self.extract_captcha_text(captcha_url)

        print(f"[INFO] Captcha extracted: {captcha_text}")

        captcha_input = self.driver.find_element(
            By.XPATH, "//input[@id='ccMain_txtCECode']"
        )
        captcha_input.clear()
        captcha_input.send_keys(captcha_text)

        payu_radio = self.driver.find_element(
            By.XPATH, "//input[@type='radio' and @value='PAYU']"
        )
        self.driver.execute_script("arguments[0].click();", payu_radio)
        print("[SUCCESS] Payment Gateway selected: PAYU")

    def select_delivery_slot_by_text(self):
        """Select delivery slot by visible text instead of value."""
        try:
            slot_select = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//th[contains(text(),'Select Delivery Slot')]/following-sibling::td//select",
                    )
                )
            )
            Select(slot_select).select_by_visible_text(self.slot_text)
            print(f"[SUCCESS] Delivery slot selected: {self.slot_text}")
        except Exception as e:
            print(f"[ERROR] select_delivery_slot_by_text failed: {e}")

    def click_register(self):
        """Enable (force show) and click the Register button."""
        register_btn = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.ID, "btnRegister"))
        )
        self.driver.execute_script("arguments[0].disabled = false;", register_btn)
        register_btn.click()

        time.sleep(3)
        try:
            alert = self.driver.switch_to.alert
            print(f"[ALERT] After clicking Register: {alert.text}")
            alert.accept()
        except NoAlertPresentException:
            print("[SUCCESS] No alerts after clicking Register")

        # register_btn = WebDriverWait(self.driver, 20).until(
        #     EC.presence_of_element_located((By.ID, "btnRegister"))
        # )

        # # Force show + enable + click in one go
        # self.driver.execute_script(
        #     """
        #     arguments[0].style.display = 'block';
        #     arguments[0].disabled = false;
        #     arguments[0].click();
        # """,
        #     register_btn,
        # )

        print("[SUCCESS] Register button enabled and clicked")

    def handle_booking_otp(self):
        """Handle OTP popup after clicking Register"""
        try:
            otp_modal = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.ID, "myModal"))
            )
            if otp_modal.is_displayed():
                print("[INFO] OTP modal displayed after Register")

                # Fetch OTP from your backend
                otp_value = self.get_recent_otp()["otp_secret"]

                otp_input = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "ccMain_txtCOTP"))
                )
                otp_input.clear()
                otp_input.send_keys(otp_value)
                print(f"[SUCCESS] Entered OTP: {otp_value}")

                # Enable and click Submit button
                submit_btn = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "btnCOTPSubmit"))
                )
                self.driver.execute_script("arguments[0].disabled = false;", submit_btn)
                submit_btn.click()
                print("[SUCCESS] Booking OTP submitted")

                time.sleep(3)
                try:
                    alert = self.driver.switch_to.alert
                    print(f"[ALERT] After booking OTP: {alert.text}")
                    alert.accept()
                except NoAlertPresentException:
                    print("[SUCCESS] No alerts after booking OTP")

                return True

        except Exception as e:
            print(f"[ERROR] Booking OTP handling failed: {e}")
            return False

    def is_server_error_page(self):
        """Check if current page shows server error"""
        try:
            # Check for common server error indicators
            error_indicators = [
                "server error",
                "503 service unavailable",
                "504 gateway timeout",
                "502 bad gateway",
                "500 internal server error",
                "maintenance",
                "temporarily unavailable",
            ]

            page_source = self.driver.page_source.lower()
            for indicator in error_indicators:
                if indicator in page_source:
                    print(f"[ERROR] Server error detected: {indicator}")
                    return True

            # Check page title for errors
            title = self.driver.title.lower()
            error_titles = ["error", "service unavailable", "maintenance"]
            for error_title in error_titles:
                if error_title in title:
                    print(f"[ERROR] Error page detected via title: {title}")
                    return True

            return False
        except Exception as e:
            print(f"[WARN] Error checking server status: {e}")
            return False

    def wait_for_page_load(self, timeout=30):
        """Wait for page to load and check for server errors"""
        try:
            # Wait for page to start loading
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState")
                == "complete"
            )

            # Check if it's a server error page
            if self.is_server_error_page():
                return False

            # Check if login form elements are present
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "tblLogIn"))
                )
                return True
            except TimeoutException:
                print("[WARN] Login form not found - possible server issue")
                return False

        except TimeoutException:
            print("[ERROR] Page load timeout")
            return False
        except Exception as e:
            print(f"[ERROR] Error during page load: {e}")
            return False

    def retry_with_backoff(self, max_retries=5, base_delay=2, max_delay=30):
        """Retry mechanism with exponential backoff for server errors"""
        retry_count = 0

        while retry_count < max_retries:
            try:
                print(f"[INFO] Attempt {retry_count + 1}/{max_retries}")

                # Navigate to login page
                self.driver.get(self.login_url)

                # Wait for page to load properly
                if not self.wait_for_page_load():
                    raise Exception("Server error or page load failure")

                # Try to fill login details
                if not self.fill_login_details():
                    raise Exception("Failed to fill login details")

                # Process login
                if self.process_login():
                    # Continue with booking process
                    self.navigate_to_new_booking()
                    self.select_district()
                    self.select_stockyard()
                    self.fill_customer_gstin()
                    self.select_purpose_of_sand()
                    self.fill_delivery_address()
                    self.fill_vehicle_number()
                    self.select_delivery_slot_by_text()
                    self.fill_captcha_and_payment()
                    self.click_register()
                    self.handle_booking_otp()

                    time.sleep(200)
                    return True
                else:
                    raise Exception("Login process failed")

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"[ERROR] Max retries ({max_retries}) reached. Giving up.")
                    return False

                # Calculate exponential backoff delay
                delay = min(base_delay * (2 ** (retry_count - 1)), max_delay)
                print(f"[INFO] Retrying in {delay} seconds... Error: {str(e)}")

                # Add some jitter to prevent thundering herd
                import random

                jitter = random.uniform(0.1, 0.5) * delay
                total_delay = delay + jitter

                time.sleep(total_delay)

                # Refresh page before retry
                try:
                    self.driver.refresh()
                    time.sleep(2)
                except:
                    pass

        return False

    def run(self):
        """Main execution with robust retry mechanism"""
        print("[INFO] Starting booking process with server error handling...")

        # Use the new retry mechanism
        success = self.retry_with_backoff(max_retries=5, base_delay=3, max_delay=60)

        if not success:
            print("[ERROR] Booking process failed after all retries")
        else:
            print("[SUCCESS] Booking process completed successfully")

        # Optionally quit driver
        # self.driver.quit()
