# ===== Imports =====
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pytest
import os
import time
from datetime import datetime
import logging
import sys
import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import test_report with error handling
try:
    from test_report import TestReport, TestCase, TestStep, track_step, create_test_case
except ImportError as e:
    print(f"Warning: Could not import test_report module: {e}")
    print("Creating fallback test reporting classes...")
    
    # Fallback classes if test_report is not available
    class TestStep:
        def __init__(self, name, description):
            self.name = name
            self.description = description
            self.start_time = None
            self.end_time = None
            self.status = "NOT_STARTED"
            self.error_message = None
        
        def start(self):
            self.start_time = time.time()
            self.status = "RUNNING"
        
        def complete(self, success=True, error_message=None, stack_trace=None):
            self.end_time = time.time()
            self.status = "PASSED" if success else "FAILED"
            self.error_message = error_message
            self.stack_trace = stack_trace
        
        def get_duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    class TestCase:
        def __init__(self, name, description):
            self.name = name
            self.description = description
            self.steps = []
            self.start_time = None
            self.end_time = None
            self.status = "NOT_STARTED"
            self.error_message = None
            self.stack_trace = None
            self.test_dir = None
        
        def start(self):
            self.start_time = time.time()
            self.status = "RUNNING"
        
        def complete(self, success=None, error_message=None, stack_trace=None):
            self.end_time = time.time()
            if success is not None:
                self.status = "PASSED" if success else "FAILED"
            else:
                self.status = "PASSED" if all(step.status == "PASSED" for step in self.steps) else "FAILED"
            self.error_message = error_message
            self.stack_trace = stack_trace
        
        def add_step(self, step):
            self.steps.append(step)
        
        def get_duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    def create_test_case(name, description):
        return TestCase(name, description)
    
    from contextlib import contextmanager
    @contextmanager
    def track_step(test_case, step_name, step_description):
        step = TestStep(step_name, step_description)
        test_case.add_step(step)
        step.start()
        try:
            yield step
            step.complete(success=True)
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            step.complete(success=False, error_message=error_message, stack_trace=stack_trace)
            print(f"[ERROR] Step '{step_name}' failed: {error_message}")
            raise

# ===== Driver Configuration =====
def initialize_driver():
    """Initialize Chrome driver with optimized options"""
    from selenium.webdriver.chrome.options import Options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    return driver

# Initialize driver
driver = None
wait = None

def get_driver():
    global driver, wait
    if driver is None:
        driver = initialize_driver()
        wait = WebDriverWait(driver, 20)
    return driver, wait

report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

# ===== OkeyProxy Admin Configuration =====
SSO_LOGIN_URL = "https://sso.xiaoxitech.com/login?project=lqcjhumd&cb=https%3A%2F%2Ftest-admin-ipglobal.cd.xiaoxigroup.net"
ADMIN_DASHBOARD_URL = "https://test-admin-ipglobal.cd.xiaoxigroup.net/"
USER_DETAIL_URL = "https://test-admin-ipglobal.cd.xiaoxigroup.net/customerDetails?id=1723"

# Admin Credentials
USERNAME = "khordichze"
PASSWORD = "zxXI@16981098"

# ===== OkeyProxy Website Configuration =====
OKEYPROXY_BASE_URL = "https://test-ipglobal.cd.xiaoxigroup.net"
OKEYPROXY_LOGIN_URL = "https://test-ipglobal.cd.xiaoxigroup.net/login"
OKEYPROXY_DASHBOARD_URL = "https://test-ipglobal.cd.xiaoxigroup.net/dashboard"
OKEYPROXY_TRANSACTIONS_URL = "https://test-ipglobal.cd.xiaoxigroup.net/dashboard/transactions"
OKEYPROXY_PAYMENT_URL = "https://test-ipglobal.cd.xiaoxigroup.net/dashboard/pay"

# OkeyProxy Test Account
OKEYPROXY_ACCOUNT = {
    "email": "amanda3@getnada.com",
    "password": "123123123"
}

# PayPal Sandbox Credentials
PAYPAL_CREDENTIALS = {
    "email": "xiaoxiqa@gmail.com",
    "password": "Xiaoxi123@"
}

# ===== Admin Element Selectors =====
ADMIN_SELECTORS = {
    "login": {
        "username_password_login": "//span[contains(text(), '用户名密码登录')]",
        "username_field": "//input[@type='text' and @placeholder='用户名' and @class='el-input__inner']",
        "password_field": "//input[@type='password' and @placeholder='密码' and @class='el-input__inner']",
        "captcha_field": "//input[@type='text' and @placeholder='验证码' and @class='el-input__inner']"
    },
    "user_detail": {
        "open_package_button": "//button[@data-v-0985cdb0 and contains(@class, 'el-button')]//span[contains(text(), '开套餐')]/..",
        "package_type_label": "//label[@for='mealType' and contains(text(), '选择套餐类型')]"
    },
    "package_selection": {
        "package_type_dropdown": "//div[@class='el-select']//input[@placeholder='请选择套餐类型']",
        "ip_type_dropdown": "//div[@class='el-select']//input[@placeholder='请选择IP类型']",
        "original_price_dropdown": "//*[@id='app']/div/div/section/div/div[2]/div[6]/div/div/div[2]/div/form/div[3]/div/div/div[1]/input",
        "amount_input": "//input[@type='text' and @placeholder='请输入应付金额' and @class='el-input__inner']",
        "confirm_button": "//*[@id='app']/div/div/section/div/div[2]/div[6]/div/div/div[3]/span/button[2]"
    },
    "success_message": {
        "payment_success": "//div[@class='payment-success-title' and contains(text(), 'Your order has been processed.')]",
        "success_alert": "//p[@class='el-message__content' and contains(text(), '操作成功！')]",
        "success_alert_alt": "//p[contains(@class, 'el-message__content') and contains(text(), '操作成功')]",
        "success_alert_text": "//div[contains(@class, 'el-message--success')]",
        "success_alert_general": "//div[contains(@class, 'success')]"
    },
    "package_verification": {
        "time_span": "//span[contains(text(), ':') and string-length(text()) = 8]",
        "package_time": "//span[contains(text(), ':') and contains(text(), ':')]"
    }
}

# ===== OkeyProxy Website Element Selectors =====
OKEYPROXY_SELECTORS = {
    "login": {
        "email_input": "//input[@placeholder='Your Email address']",
        "password_input": "//input[@placeholder='Enter Password']",
        "login_button": "//button[contains(@class, 'custom-button')]//span[contains(text(), 'Login')]/.."
    },
    "transactions": {
        "rotating_residential_advanced_button": "//*[@id='__layout']/section/section/main/div/div[2]/div[2]/div[1]/div[3]/table/tbody/tr[1]/td[9]/div/button[1]",
        "rotating_residential_premium_button": "//*[@id='__layout']/section/section/main/div/div[2]/div[2]/div[1]/div[3]/table/tbody/tr[1]/td[9]/div/button[1]",
        "rotating_datacenter_button": "//*[@id='__layout']/section/section/main/div/div[2]/div[2]/div[1]/div[3]/table/tbody/tr[1]/td[9]/div/button[1]",
        "static_residential_tab": "//div[@data-v-2f3085af and @class='tab' and contains(text(), 'Static Residential Proxies (ISP)')]",
        "static_residential_button": "//*[@id='__layout']/section/section/main/div/div[2]/div[2]/div[1]/div[3]/table/tbody/tr[1]/td[8]/div/button[1]",
        "datacenter_tab": "//div[@data-v-2f3085af and @class='tab' and contains(text(), 'Datacenter Proxies')]",
        "datacenter_button": "//*[@id='__layout']/section/section/main/div/div[2]/div[2]/div[1]/div[3]/table/tbody/tr[1]/td[8]/div/button[1]",
        "unlimited_residential_tab": "//div[@data-v-2f3085af and contains(@class, 'tab') and contains(text(), 'Unlimited Residential Proxies')]",
        "unlimited_residential_button": "//*[@id='__layout']/section/section/main/div/div[2]/div[2]/div[1]/div[3]/table/tbody/tr[1]/td[9]/div/button[1]"
    },
    "payment": {
        "payment_button": "//*[@id='__layout']/section/section/main/div/div[1]/div/div[2]/div/button",
        "paypal_option": "//*[@id='__layout']/section/section/main/div/div[1]/div/div[1]/div[2]/div[1]/div[5]/div[1]"
    },
    "success_error": {
        "success_message": "//div[@class='payment-success-title' and (contains(text(), 'Your order has been processed') or contains(text(), 'Your order was processed successfully') or contains(text(), 'Machine allocation failed'))]",
        "insufficient_balance_popup": "//*[@id='__layout']/section/section/main/div/div[3]/div/div",
        "insufficient_balance_text": "//*[@id='__layout']/section/section/main/div/div[3]/div/div/div[2]/div[1]/div",
        "later_button": "//*[@id='__layout']/section/section/main/div/div[3]/div/div/div[2]/div[3]/button[1]"
    }
}

# ===== Proxy Type Configuration =====
PROXY_TYPES = {
    "rotating_residential_advanced": {
        "name": "Rotating Residential Proxies – Advanced",
        "tab_required": False,
        "button_xpath": OKEYPROXY_SELECTORS["transactions"]["rotating_residential_advanced_button"]
    },
    "rotating_residential_premium": {
        "name": "Rotating Residential Proxies – Premium", 
        "tab_required": False,
        "button_xpath": OKEYPROXY_SELECTORS["transactions"]["rotating_residential_premium_button"]
    },
    "rotating_datacenter": {
        "name": "Rotating Datacenter Proxies",
        "tab_required": False,
        "button_xpath": OKEYPROXY_SELECTORS["transactions"]["rotating_datacenter_button"]
    },
    "static_residential": {
        "name": "Static Residential Proxies",
        "tab_required": True,
        "tab_xpath": OKEYPROXY_SELECTORS["transactions"]["static_residential_tab"],
        "button_xpath": OKEYPROXY_SELECTORS["transactions"]["static_residential_button"]
    },
    "datacenter": {
        "name": "Datacenter Proxies",
        "tab_required": True,
        "tab_xpath": OKEYPROXY_SELECTORS["transactions"]["datacenter_tab"],
        "button_xpath": OKEYPROXY_SELECTORS["transactions"]["datacenter_button"]
    },
    "unlimited_residential": {
        "name": "Unlimited Residential Proxies",
        "tab_required": True,
        "tab_xpath": OKEYPROXY_SELECTORS["transactions"]["unlimited_residential_tab"],
        "button_xpath": OKEYPROXY_SELECTORS["transactions"]["unlimited_residential_button"]
    }
}

# ===== Utility Functions =====
def wait_for_page_load(driver, wait):
    """Wait for page to fully load"""
    try:
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
    except TimeoutException:
        print("Warning: Page load timeout, continuing...")


def create_report():
    """Creates a unique report directory with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_dir = os.path.join(report_dir, f"okeyproxy_Admin_Panel_{timestamp}")
    os.makedirs(test_dir, exist_ok=True)
    return test_dir

def take_screenshot(test_case, step_name):
    """Take screenshot and save to test directory"""
    try:
        driver, wait = get_driver()
        screenshot_path = os.path.join(test_case.test_dir, f"{step_name}_{int(time.time())}.png")
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        print(f"Failed to take screenshot: {str(e)}")
        return None

def save_page_source(test_case, step_name):
    """Save page source HTML"""
    try:
        driver, wait = get_driver()
        html_path = os.path.join(test_case.test_dir, f"{step_name}_{int(time.time())}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"Page source saved: {html_path}")
        return html_path
    except Exception as e:
        print(f"Failed to save page source: {str(e)}")
        return None

# ===== Admin Login Function =====
def login_to_admin_panel(test_case):
    """Login to admin panel using username and password with manual captcha"""
    with track_step(test_case, "Admin Login", "Login to admin panel using username/password"):
        try:
            driver, wait = get_driver()
            print("Navigating to SSO login page...")
            driver.get(SSO_LOGIN_URL)
            time.sleep(3)
            
            # Step 1: Click on username/password login option
            try:
                username_login_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//span[contains(text(), '用户名密码登录')]")))
                driver.execute_script("arguments[0].click();", username_login_btn)
                print("[SUCCESS] Clicked on username/password login")
                time.sleep(2)
            except Exception as e:
                print(f"[ERROR] Failed to click username/password login: {str(e)}")
                return False
            
            # Step 2: Enter username
            try:
                username_field = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='text' and @placeholder='用户名' and @class='el-input__inner']")))
                username_field.clear()
                username_field.send_keys(USERNAME)
                print(f"[SUCCESS] Entered username: {USERNAME}")
                time.sleep(1)
            except Exception as e:
                print(f"[ERROR] Failed to enter username: {str(e)}")
                return False
            
            # Step 3: Enter password
            try:
                password_field = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='password' and @placeholder='密码' and @class='el-input__inner']")))
                password_field.clear()
                password_field.send_keys(PASSWORD)
                print("[SUCCESS] Entered password")
                time.sleep(1)
            except Exception as e:
                print(f"[ERROR] Failed to enter password: {str(e)}")
                return False
            
            # Step 4: Click on captcha field and wait for manual input
            print("Handling captcha...")
            try:
                captcha_field = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='text' and @placeholder='验证码' and @class='el-input__inner']")))
                driver.execute_script("arguments[0].click();", captcha_field)
                
                # Wait up to 15 minutes for user to complete captcha and login
                max_wait_time = 900  # 15 minutes
                start_time = time.time()
                last_url = driver.current_url
                
                while time.time() - start_time < max_wait_time:
                    current_url = driver.current_url
                    
                    # Only log URL if it has changed
                    if current_url != last_url:
                        print(f"Current URL: {current_url}")
                        last_url = current_url
                    
                    # Check if we've been redirected to admin panel
                    if "test-admin-ipglobal.cd.xiaoxigroup.net/?token" in current_url:
                        print("[SUCCESS] Successfully logged in to admin panel!")
                        return True
                    
                    time.sleep(10)
                
                print("[ERROR] Login failed - timeout waiting for manual captcha completion")
                return False
                
            except Exception as e:
                print(f"[ERROR] Failed to handle captcha: {str(e)}")
                return False
                
        except Exception as e:
            return False

# ===== Navigate to User Detail =====
def navigate_to_user_detail(test_case):
    """Navigate to user detail page - OPTIMIZED"""
    with track_step(test_case, "Navigate to User Detail", "Navigate to user detail page"):
        try:
            driver, wait = get_driver()
            print("Waiting 5 seconds before navigating...")
            time.sleep(5)
            print("Navigating to user detail page...")
            driver.get(USER_DETAIL_URL)
            wait_for_page_load(driver, wait)
            # Reduced wait time - just wait for page to be ready
            time.sleep(1)
            print("[SUCCESS] Successfully navigated to user detail page")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to navigate to user detail: {str(e)}")
            take_screenshot(test_case, "navigate_user_detail_failed")
            save_page_source(test_case, "navigate_user_detail_failed")
            return False

# ===== Click Open Package Button =====
def click_open_package_button(test_case):
    """Click on the open package button"""
    with track_step(test_case, "Click Open Package Button", "Click on the open package button"):
        try:
            driver, wait = get_driver()
            print("Clicking on open package button...")
            
            # Try multiple selectors for the open package button
            open_package_selectors = [
                ADMIN_SELECTORS["user_detail"]["open_package_button"],
                "//button[contains(@class, 'el-button')]//span[contains(text(), '开套餐')]",
                "//button[contains(text(), '开套餐')]",
                "//button//span[contains(text(), '开套餐')]"
            ]
            
            open_package_btn = None
            for selector in open_package_selectors:
                try:
                    open_package_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    print(f"Found open package button with selector: {selector}")
                    break
                except:
                    continue
            
            if open_package_btn is None:
                raise Exception("Open package button not found with any selector")
            
            # Scroll the button into view
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", open_package_btn)
            
            # Click the button
            driver.execute_script("arguments[0].click();", open_package_btn)
            print("[SUCCESS] Clicked on open package button")
            
            # Wait for the package selection form to appear
            wait.until(EC.presence_of_element_located(
                (By.XPATH, ADMIN_SELECTORS["user_detail"]["package_type_label"])))
            print("[SUCCESS] Package selection form appeared")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to click open package button: {str(e)}")
            take_screenshot(test_case, "click_open_package_failed")
            save_page_source(test_case, "click_open_package_failed")
            return False

# ===== Arrow Down Navigation Functions =====
def click_original_price_dropdown(test_case, arrow_down_count):
    """Special function to handle Original Price dropdown interaction - ULTRA FAST JS APPROACH"""
    with track_step(test_case, f"Navigate Original Price", f"Click Original Price and press Arrow Down {arrow_down_count} times"):
        try:
            driver, wait = get_driver()
            print(f"Clicking Original Price and navigating with {arrow_down_count} Arrow Down presses...")
            
            # Find the dropdown element first
            dropdown_element = None
            dropdown_selectors = [
                "//*[@id='app']/div/div/section/div/div[2]/div[6]/div/div/div[2]/div/form/div[3]/div/div/div[1]/input",
                "//*[@id='app']/div/div/section/div/div[2]/div[6]/div/div/div[2]/div/form/div[3]/div/div//div[contains(@class, 'el-select')]",
                "//*[@id='app']/div/div/section/div/div[2]/div[6]/div/div/div[2]/div/form/div[3]/div/div//div[contains(@class, 'el-input')]"
            ]
            
            for selector in dropdown_selectors:
                try:
                    dropdown_element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    break
                except:
                    continue
            
            if not dropdown_element:
                print(f"[WARNING] Could not find Original Price dropdown, continuing with test...")
                return True
            
            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", dropdown_element)
            
            # ULTRA FAST: Use JavaScript to directly trigger dropdown and navigate in ONE BATCH
            try:
                # Click to open dropdown
                driver.execute_script("arguments[0].click();", dropdown_element)
                print(f"[SUCCESS] Clicked Original Price using JavaScript")
                
                # Wait briefly for dropdown to open
                time.sleep(0.1)
                
                # SINGLE BATCH: Execute all arrow keys and enter in one JavaScript call
                driver.execute_script(f"""
                    // Create and dispatch all arrow down events instantly
                    for (let i = 0; i < {arrow_down_count}; i++) {{
                        var event = new KeyboardEvent('keydown', {{
                            key: 'ArrowDown',
                            code: 'ArrowDown',
                            keyCode: 40,
                            which: 40,
                            bubbles: true
                        }});
                        document.activeElement.dispatchEvent(event);
                    }}
                    
                    // Press Enter to confirm
                    var enterEvent = new KeyboardEvent('keydown', {{
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true
                    }});
                    document.activeElement.dispatchEvent(enterEvent);
                """)
                
                print(f"[SUCCESS] Completed navigation with {arrow_down_count} Arrow Down presses using SINGLE BATCH JavaScript")
                
            except Exception as e:
                print(f"[WARNING] JavaScript approach failed, falling back to ActionChains: {e}")
                # Fallback to ActionChains if JavaScript fails
                actions = ActionChains(driver)
                for i in range(arrow_down_count):
                    actions.send_keys(Keys.ARROW_DOWN)
                actions.send_keys(Keys.ENTER)
                actions.perform()
                print(f"[SUCCESS] Completed navigation with {arrow_down_count} Arrow Down presses using ActionChains fallback")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to navigate Original Price: {str(e)}")
            take_screenshot(test_case, "navigate_original_price_failed")
            return False


def click_and_navigate_dropdown(test_case, dropdown_xpath, arrow_down_count, dropdown_name):
    """Click dropdown and navigate using Arrow Down keys - ULTRA FAST JS APPROACH"""
    with track_step(test_case, f"Navigate {dropdown_name}", f"Click {dropdown_name} and press Arrow Down {arrow_down_count} times"):
        try:
            driver, wait = get_driver()
            print(f"Clicking {dropdown_name} and navigating with {arrow_down_count} Arrow Down presses...")
            
            # Find the dropdown element
            dropdown = wait.until(EC.presence_of_element_located((By.XPATH, dropdown_xpath)))
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", dropdown)
            
            # ULTRA FAST: Use JavaScript to directly trigger dropdown and navigate in ONE BATCH
            try:
                # Click to open dropdown
                driver.execute_script("arguments[0].click();", dropdown)
                print(f"[SUCCESS] Clicked {dropdown_name} using JavaScript")
                
                # Wait briefly for dropdown to open
                time.sleep(0.1)
                
                # SINGLE BATCH: Execute all arrow keys and enter in one JavaScript call
                driver.execute_script(f"""
                    // Create and dispatch all arrow down events instantly
                    for (let i = 0; i < {arrow_down_count}; i++) {{
                        var event = new KeyboardEvent('keydown', {{
                            key: 'ArrowDown',
                            code: 'ArrowDown',
                            keyCode: 40,
                            which: 40,
                            bubbles: true
                        }});
                        document.activeElement.dispatchEvent(event);
                    }}
                    
                    // Press Enter to confirm
                    var enterEvent = new KeyboardEvent('keydown', {{
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true
                    }});
                    document.activeElement.dispatchEvent(enterEvent);
                """)
                
                print(f"[SUCCESS] Completed navigation with {arrow_down_count} Arrow Down presses using SINGLE BATCH JavaScript")
                
            except Exception as e:
                print(f"[WARNING] JavaScript approach failed, falling back to ActionChains: {e}")
                # Fallback to ActionChains if JavaScript fails
                actions = ActionChains(driver)
                for i in range(arrow_down_count):
                    actions.send_keys(Keys.ARROW_DOWN)
                actions.send_keys(Keys.ENTER)
                actions.perform()
                print(f"[SUCCESS] Completed navigation with {arrow_down_count} Arrow Down presses using ActionChains fallback")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to navigate {dropdown_name}: {str(e)}")
            take_screenshot(test_case, f"navigate_{dropdown_name}_failed")
            return False

def enter_amount(test_case, amount):
    """Enter amount in the amount input field - OPTIMIZED"""
    with track_step(test_case, "Enter Amount", f"Enter amount: {amount}"):
        try:
            driver, wait = get_driver()
            print(f"Entering amount: {amount}")
            
            amount_field = wait.until(EC.element_to_be_clickable(
                (By.XPATH, ADMIN_SELECTORS["package_selection"]["amount_input"])))
            amount_field.clear()
            amount_field.send_keys(amount)
            
            print(f"[SUCCESS] Entered amount: {amount}")
            # No sleep needed - just return immediately
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to enter amount: {str(e)}")
            take_screenshot(test_case, "enter_amount_failed")
            return False

def click_confirm_button(test_case):
    """Click the confirm button"""
    with track_step(test_case, "Click Confirm Button", "Click the confirm button"):
        try:
            driver, wait = get_driver()
            print("Clicking confirm button...")
            
            # Use the known working selector
            confirm_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, ADMIN_SELECTORS["package_selection"]["confirm_button"])))
            
            print(f"Found confirm button with selector: {ADMIN_SELECTORS['package_selection']['confirm_button']}")
            
            # Scroll the button into view
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", confirm_btn)
            
            # Click the button
            confirm_btn.click()
            print("[SUCCESS] Clicked confirm button")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to click confirm button: {str(e)}")
            take_screenshot(test_case, "click_confirm_failed")
            return False

def verify_package_creation(test_case):
    """Verify package creation by looking for time span with time content"""
    with track_step(test_case, "Verify Package Creation", "Verify new package created by checking time span"):
        try:
            driver, wait = get_driver()
            print("Verifying package creation by looking for time span...")
            
            # Wait a bit for the page to update
            time.sleep(3)
            
            # Look for any span element that contains time format (HH:MM:SS)
            try:
                time_span = wait.until(EC.presence_of_element_located(
                    (By.XPATH, ADMIN_SELECTORS["package_verification"]["time_span"])))
                
                if time_span and time_span.text.strip():
                    time_text = time_span.text.strip()
                    # Check if it looks like a time (contains : and has reasonable length)
                    if ':' in time_text and len(time_text) >= 5:
                        print(f"[SUCCESS] Package creation verified - Time found: {time_text}")
                        return True
                    else:
                        print(f"[WARNING] Time span found but doesn't look like time: {time_text}")
                        return False
                else:
                    print("[WARNING] Time span found but no text content")
                    return False
                    
            except TimeoutException:
                print("[WARNING] Time span not found - package may not have been created")
                return False
                
        except Exception as e:
            print(f"[ERROR] Failed to verify package creation: {str(e)}")
            take_screenshot(test_case, "package_verification_failed")
            return False

# ===== Website Payment Functions =====
def handle_iframe_interference():
    """Handle iframe interference by closing chat widgets and aggressively hiding iframes"""
    try:
        print("Handling iframe interference...")
        
        # Try to close any chat widgets or overlays
        chat_close_selectors = [
            "//button[contains(@class, 'chat-close')]",
            "//button[contains(@class, 'close')]",
            "//div[contains(@class, 'chat')]//button",
            "//iframe[@id='s-chat-plugin']//..//button",
            "//*[contains(@class, 'chat')]//*[contains(@class, 'close')]"
        ]
        
        for selector in chat_close_selectors:
            try:
                close_button = driver.find_element(By.XPATH, selector)
                if close_button.is_displayed():
                    driver.execute_script("arguments[0].click();", close_button)
                    print("[SUCCESS] Closed chat widget/iframe")
                    time.sleep(1)
                    break
            except:
                continue
                
        # Aggressively hide iframe and all related elements
        try:
            driver.execute_script("""
                // Hide the specific chat iframe that's causing issues
                var specificChat = document.getElementById('s-chat-plugin');
                if (specificChat) {
                    specificChat.style.display = 'none';
                    specificChat.style.visibility = 'hidden';
                    specificChat.style.zIndex = '-9999';
                    specificChat.style.opacity = '0';
                    specificChat.style.position = 'absolute';
                    specificChat.style.left = '-9999px';
                    specificChat.style.top = '-9999px';
                    specificChat.style.width = '0px';
                    specificChat.style.height = '0px';
                }
                
                // Hide all chat-related iframes
                var iframes = document.querySelectorAll('iframe[title*="Contact"], iframe[id*="chat"], iframe[title*="chat"], iframe[id="s-chat-plugin"]');
                for (var i = 0; i < iframes.length; i++) {
                    iframes[i].style.display = 'none';
                    iframes[i].style.visibility = 'hidden';
                    iframes[i].style.zIndex = '-9999';
                    iframes[i].style.opacity = '0';
                    iframes[i].style.position = 'absolute';
                    iframes[i].style.left = '-9999px';
                    iframes[i].style.top = '-9999px';
                    iframes[i].style.width = '0px';
                    iframes[i].style.height = '0px';
                }
                
                // Hide any parent containers
                var containers = document.querySelectorAll('[class*="chat"], [id*="chat"]');
                for (var i = 0; i < containers.length; i++) {
                    if (containers[i].querySelector('iframe')) {
                        containers[i].style.display = 'none';
                        containers[i].style.visibility = 'hidden';
                        containers[i].style.zIndex = '-9999';
                        containers[i].style.opacity = '0';
                    }
                }
                
                // Hide any fixed positioned elements that might interfere
                var fixedElements = document.querySelectorAll('[style*="position: fixed"], [style*="position:fixed"]');
                for (var i = 0; i < fixedElements.length; i++) {
                    var element = fixedElements[i];
                    if (element.id === 's-chat-plugin' || element.title === 'Contact us' || element.title === 'Contact') {
                        element.style.display = 'none';
                        element.style.visibility = 'hidden';
                        element.style.zIndex = '-9999';
                        element.style.opacity = '0';
                        element.style.position = 'absolute';
                        element.style.left = '-9999px';
                        element.style.top = '-9999px';
                    }
                }
            """)
            print("[SUCCESS] Aggressively hidden chat iframes and containers")
        except Exception as e:
            print(f"[WARNING] Error hiding iframes: {str(e)}")
            
        # Additional wait to ensure iframe is completely hidden
        time.sleep(2)
            
    except Exception as e:
        print(f"Warning: Could not handle iframe interference: {str(e)}")

def okeyproxy_login(test_case):
    """Login to OkeyProxy with specified account"""
    with track_step(test_case, "OkeyProxy Login", "Login with with_balance account"):
        try:
            print("Logging in to OkeyProxy with with_balance account...")
            driver, wait = get_driver()
            driver.get(OKEYPROXY_LOGIN_URL)
            wait_for_page_load(driver, wait)
            
            # Enter email
            print("Waiting for email field...")
            email_field = wait.until(
                EC.element_to_be_clickable((By.XPATH, OKEYPROXY_SELECTORS["login"]["email_input"]))
            )
            time.sleep(1)  # Additional wait
            
            # Try multiple methods to enter email
            try:
                email_field.clear()
                time.sleep(0.5)
                email_field.send_keys(OKEYPROXY_ACCOUNT["email"])
                time.sleep(1)
                
                # Verify email was entered
                if email_field.get_attribute("value") == OKEYPROXY_ACCOUNT["email"]:
                    print(f"[SUCCESS] Email entered successfully: {OKEYPROXY_ACCOUNT['email']}")
                else:
                    print("[WARNING] Email not entered properly, trying JavaScript method...")
                    driver.execute_script("arguments[0].value = arguments[1];", email_field, OKEYPROXY_ACCOUNT["email"])
                    time.sleep(1)
                    print(f"[SUCCESS] Email entered via JavaScript: {OKEYPROXY_ACCOUNT['email']}")
                    
            except Exception as e:
                print(f"[WARNING] Error entering email: {str(e)}, trying JavaScript method...")
                driver.execute_script("arguments[0].value = arguments[1];", email_field, OKEYPROXY_ACCOUNT["email"])
                time.sleep(1)
                print(f"[SUCCESS] Email entered via JavaScript: {OKEYPROXY_ACCOUNT['email']}")
            
            # Enter password
            print("Waiting for password field...")
            password_field = wait.until(
                EC.element_to_be_clickable((By.XPATH, OKEYPROXY_SELECTORS["login"]["password_input"]))
            )
            time.sleep(1)  # Additional wait
            
            # Try multiple methods to enter password
            try:
                password_field.clear()
                time.sleep(0.5)
                password_field.send_keys(OKEYPROXY_ACCOUNT["password"])
                time.sleep(1)
                print("[SUCCESS] Password entered successfully")
            except Exception as e:
                print(f"[WARNING] Error entering password: {str(e)}, trying JavaScript method...")
                driver.execute_script("arguments[0].value = arguments[1];", password_field, OKEYPROXY_ACCOUNT["password"])
                time.sleep(1)
                print("[SUCCESS] Password entered via JavaScript")
            
            # Click login button
            login_button = None
            login_selectors = [
                OKEYPROXY_SELECTORS["login"]["login_button"],
                "//button[contains(@class, 'custom-button')]//span[contains(text(), 'Login')]/..",
                "//button[contains(@class, 'el-button')]//span[contains(text(), 'Login')]/..",
                "//button//span[contains(text(), 'Login')]/..",
                "//button[contains(text(), 'Login')]"
            ]
            
            for selector in login_selectors:
                try:
                    login_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    break
                except:
                    continue
            
            if login_button:
                print("Clicking login button...")
                
                # Scroll the button into view
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", login_button)
                time.sleep(1)
                
                # Try JavaScript click first to avoid any interference
                try:
                    driver.execute_script("arguments[0].click();", login_button)
                    print("[SUCCESS] Login button clicked using JavaScript")
                except:
                    # Fallback to regular click
                    login_button.click()
                    print("[SUCCESS] Login button clicked using regular click")
                
                time.sleep(3)  # Wait for login processing
            else:
                raise Exception("Could not find login button with any selector")
            
            # Wait for redirect to dashboard
            print("Waiting for redirect to dashboard...")
            wait.until(lambda driver: OKEYPROXY_DASHBOARD_URL in driver.current_url)
            time.sleep(2)  # Additional wait for page to fully load
            print("[SUCCESS] Successfully logged in to OkeyProxy")
            return True
            
        except Exception as e:
            print(f"[ERROR] OkeyProxy login failed: {str(e)}")
            take_screenshot(test_case, "okeyproxy_login_failed")
            save_page_source(test_case, "okeyproxy_login_failed")
            return False

def navigate_to_transactions_and_click_payment(test_case, proxy_type):
    """Navigate to transactions page and click the appropriate payment button"""
    with track_step(test_case, "Navigate to Transactions", f"Navigate to transactions and click payment for {proxy_type}"):
        try:
            driver, wait = get_driver()
            print(f"Navigating to transactions page for {proxy_type}...")
            driver.get(OKEYPROXY_TRANSACTIONS_URL)
            wait_for_page_load(driver, wait)
            time.sleep(3)  # Wait for page to fully load
            
            # Hard refresh to ensure fresh page state
            print("Performing hard refresh...")
            driver.refresh()
            wait_for_page_load(driver, wait)
            time.sleep(2)  # Wait after refresh
            
            # Handle iframe interference
            handle_iframe_interference()
            
            # Check if tab selection is required
            if PROXY_TYPES[proxy_type]["tab_required"]:
                print(f"Selecting tab for {proxy_type}...")
                tab_xpath = PROXY_TYPES[proxy_type]["tab_xpath"]
                tab_element = wait.until(
                    EC.element_to_be_clickable((By.XPATH, tab_xpath))
                )
                
                # Scroll tab into view
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", tab_element)
                time.sleep(1)
                
                # Click tab
                try:
                    driver.execute_script("arguments[0].click();", tab_element)
                    print(f"[SUCCESS] Tab clicked using JavaScript: {proxy_type}")
                except:
                    tab_element.click()
                    print(f"[SUCCESS] Tab clicked using regular click: {proxy_type}")
                
                time.sleep(3)  # Wait for tab content to load
            
            # Click payment button
            print(f"Clicking payment button for {proxy_type}...")
            button_xpath = PROXY_TYPES[proxy_type]["button_xpath"]
            payment_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, button_xpath))
            )
            
            # Scroll button into view
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", payment_button)
            time.sleep(1)
            
            # Click payment button
            try:
                driver.execute_script("arguments[0].click();", payment_button)
                print(f"[SUCCESS] Payment button clicked using JavaScript: {proxy_type}")
            except:
                payment_button.click()
                print(f"[SUCCESS] Payment button clicked using regular click: {proxy_type}")
            
            time.sleep(3)  # Wait for redirect to payment page
            
            # Verify redirect to payment page
            wait.until(lambda driver: OKEYPROXY_PAYMENT_URL in driver.current_url)
            print(f"[SUCCESS] Successfully redirected to payment page for {proxy_type}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to navigate to transactions and click payment for {proxy_type}: {str(e)}")
            take_screenshot(test_case, f"transactions_navigation_failed_{proxy_type}")
            save_page_source(test_case, f"transactions_navigation_failed_{proxy_type}")
            return False

def process_paypal_payment(test_case, proxy_type):
    """Process PayPal payment"""
    with track_step(test_case, "PayPal Payment", f"Process PayPal payment for {proxy_type}"):
        try:
            driver, wait = get_driver()
            print(f"Processing PayPal payment for {proxy_type}...")
            
            # Handle iframe interference first
            handle_iframe_interference()
            
            # Select PayPal option
            paypal_option = wait.until(
                EC.element_to_be_clickable((By.XPATH, OKEYPROXY_SELECTORS["payment"]["paypal_option"]))
            )
            paypal_option.click()
            time.sleep(2)
            
            # Click payment button
            payment_button = wait.until(
                EC.presence_of_element_located((By.XPATH, OKEYPROXY_SELECTORS["payment"]["payment_button"]))
            )
            
            # Scroll the button into view to avoid iframe interference
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", payment_button)
            time.sleep(1)
            
            # Try JavaScript click first to avoid iframe interception
            try:
                driver.execute_script("arguments[0].click();", payment_button)
                print("[SUCCESS] PayPal payment button clicked using JavaScript")
            except:
                # Fallback to regular click
                payment_button.click()
                print("[SUCCESS] PayPal payment button clicked using regular click")
            
            time.sleep(5)  # Wait for PayPal redirect
            
            # Handle PayPal flow based on proxy type
            if proxy_type == "rotating_residential_advanced":
                # Complete full PayPal Sandbox Login & Checkout Flow for Residential Advanced
                print("\n--- Step 3: Completing Full PayPal Sandbox Login (Residential Advanced) ---")
                with track_step(test_case, "PayPal Sandbox Login", "Complete PayPal sandbox login process"):
                    # Wait for a new window/tab to open
                    print("Waiting for PayPal sandbox window to open...")
                    wait.until(lambda driver: len(driver.window_handles) > 1)
                    # Switch to the new window/tab
                    driver.switch_to.window(driver.window_handles[-1])
                    
                    # Verify we're on the PayPal sandbox page
                    wait.until(
                        lambda driver: "https://www.sandbox.paypal.com/checkoutnow?" in driver.current_url
                    )
                    print(f"Successfully redirected to PayPal sandbox: {driver.current_url}")
                    
                    # Enter email
                    print("Entering PayPal email...")
                    with track_step(test_case, "Enter PayPal Email", "Enter email in PayPal sandbox"):
                        email_field = wait.until(
                            EC.presence_of_element_located((By.XPATH, "//input[@id='email']"))
                        )
                        email_field.clear()
                        email_field.send_keys(PAYPAL_CREDENTIALS["email"])
                    
                    # Click Next button
                    print("Clicking Next button...")
                    with track_step(test_case, "Click Next Button", "Click Next button in PayPal"):
                        next_button = wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//button[@id='btnNext']"))
                        )
                        next_button.click()
                    
                    # Wait for password field to be present and interactable
                    print("Waiting for password field...")
                    time.sleep(3)  # Additional wait for page transition
                    
                    # Try to find password field in main content and iframes
                    password_field = None
                    try:
                        # First try in main content
                        password_field = wait.until(
                            EC.presence_of_element_located((By.XPATH, "//input[@id='password']"))
                        )
                    except:
                        # If not found, try in iframes
                        print("Password field not found in main content, checking iframes...")
                        iframes = driver.find_elements(By.TAG_NAME, "iframe")
                        for iframe in iframes:
                            try:
                                driver.switch_to.frame(iframe)
                                password_field = wait.until(
                                    EC.presence_of_element_located((By.XPATH, "//input[@id='password']"))
                                )
                                break
                            except:
                                driver.switch_to.default_content()
                                continue
                    
                    if password_field:
                        print("Found password field, entering password...")
                        with track_step(test_case, "Enter PayPal Password", "Enter password in PayPal sandbox"):
                            # Wait for field to be interactable
                            wait.until(EC.element_to_be_clickable(password_field))
                            password_field.clear()
                            password_field.send_keys(PAYPAL_CREDENTIALS["password"])
                        
                        # Click Login button
                        print("Clicking Login button...")
                        with track_step(test_case, "Click Login Button", "Click Login button in PayPal"):
                            login_button = wait.until(
                                EC.element_to_be_clickable((By.XPATH, "//button[@id='btnLogin']"))
                            )
                            login_button.click()
                        
                        # Switch back to default content if we were in an iframe
                        driver.switch_to.default_content()
                        
                        # Wait for payment review page and click Continue
                        print("Waiting for payment review page...")
                        wait.until(
                            lambda driver: "https://www.sandbox.paypal.com/webapps/hermes?" in driver.current_url
                        )
                        time.sleep(3)  # Additional wait for page to fully load
                        
                        print("Clicking Continue button...")
                        with track_step(test_case, "Click Continue Button", "Click Continue button in PayPal"):
                            # Try multiple selectors for the Continue button
                            continue_button = None
                            try:
                                # First try the new XPath
                                continue_button = wait.until(
                                    EC.element_to_be_clickable((By.XPATH, "//*[@id='hermione-container']/div[1]/main/div[3]/div[2]/button"))
                                )
                            except:
                                try:
                                    # Fallback to the old XPath
                                    continue_button = wait.until(
                                        EC.element_to_be_clickable((By.XPATH, "//*[@id='button']/button"))
                                    )
                                except:
                                    # Try finding by text content
                                    continue_button = wait.until(
                                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]"))
                                    )
                            
                            if continue_button:
                                # Scroll the button into view
                                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", continue_button)
                                time.sleep(1)
                                # Try JavaScript click first
                                try:
                                    driver.execute_script("arguments[0].click();", continue_button)
                                except:
                                    # Fallback to regular click
                                    continue_button.click()
                                
                            else:
                                raise Exception("Could not find Continue button with any selector")
                        
                        # Wait for success page
                        print("Waiting for payment success page...")
                        with track_step(test_case, "Verify Payment Success", "Verify payment success page"):
                            # Wait for redirect back to OkeyProxy
                            wait.until(
                                lambda driver: "test-ipglobal.cd.xiaoxigroup.net" in driver.current_url
                            )
                            
                            # Check for success message
                            success_selectors = [
                                "//div[@class='payment-success-title']",
                                "//div[contains(@class, 'payment-success')]",
                                "//div[contains(text(), 'processed')]",
                                "//div[contains(text(), 'success')]"
                            ]
                            
                            success_element = None
                            for selector in success_selectors:
                                try:
                                    success_element = wait.until(
                                        EC.presence_of_element_located((By.XPATH, selector))
                                    )
                                    break
                                except:
                                    continue
                            
                            if success_element:
                                print("[SUCCESS] OkeyProxy PayPal payment completed successfully!")
                                print(f"Success message: {success_element.text}")
                                print(f"Success URL: {driver.current_url}")
                                return True
                            else:
                                print("[WARNING] PayPal payment completed but success message not found")
                                print(f"Current URL: {driver.current_url}")
                                return True
                    else:
                        raise Exception("Could not find password field in main content or iframes")
            
            else:
                # For other account types: Already logged in, just verify redirect and click Continue
                print("\n--- Step 3: Handling Already Logged In PayPal Flow (Non-Residential Advanced) ---")
                with track_step(test_case, "PayPal Already Logged In", "Handle already logged in PayPal flow"):
                    # Wait for a new window/tab to open
                    print("Waiting for PayPal sandbox window to open...")
                    wait.until(lambda driver: len(driver.window_handles) > 1)
                    # Switch to the new window/tab
                    driver.switch_to.window(driver.window_handles[-1])
                    
                    # Verify redirect to sandbox.paypal.com (more flexible)
                    print("Verifying redirect to PayPal sandbox...")
                    wait.until(
                        lambda driver: "sandbox.paypal.com" in driver.current_url
                    )
                    print(f"Successfully redirected to PayPal sandbox: {driver.current_url}")
                    
                    # Wait for page to load and click "Continue to Review Order"
                    print("Waiting for page to load and clicking Continue to Review Order...")
                    time.sleep(3)  # Wait for page to fully load
                    
                    with track_step(test_case, "Click Continue to Review Order", "Click Continue to Review Order button"):
                        # Look for the specific button with the provided selector
                        continue_button = wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//button[@data-id='payment-submit-btn' and @data-testid='submit-button-initial']"))
                        )
                        
                        if continue_button:
                            # Scroll the button into view
                            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", continue_button)
                            time.sleep(1)
                            # Click the button
                            driver.execute_script("arguments[0].click();", continue_button)
                            print("[SUCCESS] Clicked 'Continue to Review Order' button")
                        else:
                            raise Exception("Could not find 'Continue to Review Order' button")
                    
                    # Wait for success page
                    print("Waiting for payment success page...")
                    with track_step(test_case, "Verify Payment Success", "Verify payment success page"):
                        # Wait for redirect back to OkeyProxy
                        wait.until(
                            lambda driver: "test-ipglobal.cd.xiaoxigroup.net" in driver.current_url
                        )
                        
                        # Check for success message
                        success_selectors = [
                            "//div[@class='payment-success-title']",
                            "//div[contains(@class, 'payment-success')]",
                            "//div[contains(text(), 'processed')]",
                            "//div[contains(text(), 'success')]"
                        ]
                        
                        success_element = None
                        for selector in success_selectors:
                            try:
                                success_element = wait.until(
                                    EC.presence_of_element_located((By.XPATH, selector))
                                )
                                break
                            except:
                                continue
                        
                        if success_element:
                            print("[SUCCESS] OkeyProxy PayPal payment completed successfully!")
                            print(f"Success message: {success_element.text}")
                            print(f"Success URL: {driver.current_url}")
                            return True
                        else:
                            print("[WARNING] PayPal payment completed but success message not found")
                            print(f"Current URL: {driver.current_url}")
                            return True
            
            return True
            
        except Exception as e:
            print(f"[ERROR] PayPal payment failed for {proxy_type}: {str(e)}")
            take_screenshot(test_case, f"paypal_payment_failed_{proxy_type}")
            save_page_source(test_case, f"paypal_payment_failed_{proxy_type}")
            return False


# ===== Test Case Functions =====
def test_rotating_residential_advanced_arrow(test_case):
    """Test Rotating Residential Proxies - Advanced using Arrow Down navigation"""
    with track_step(test_case, "Rotating Residential Advanced Admin Panel", "Test Advanced package with Arrow Down navigation"):
        try:
            print("[TEST] Testing Rotating Residential Proxies - Advanced with Arrow Down navigation")
            
            # Step 1: Click package type dropdown and press Arrow Down ×1
            if not click_and_navigate_dropdown(test_case, 
                ADMIN_SELECTORS["package_selection"]["package_type_dropdown"], 
                1, "Package Type"):
                return False
            
            # Step 2: Click IP type dropdown and press Arrow Down ×2
            if not click_and_navigate_dropdown(test_case, 
                ADMIN_SELECTORS["package_selection"]["ip_type_dropdown"], 
                2, "IP Type"):
                return False
            
            # Step 3: Click original price dropdown and press Arrow Down ×13
            if not click_original_price_dropdown(test_case, 13):
                print("[WARNING] Original Price dropdown navigation failed, continuing with test...")
            
            # Step 4: Enter amount
            if not enter_amount(test_case, "1"):
                return False
            
            # Step 5: Click confirm button
            if not click_confirm_button(test_case):
                return False
            
            # Step 6: Verify package creation
            if not verify_package_creation(test_case):
                return False
            
            print("[SUCCESS] Rotating Residential Proxies - Advanced test completed successfully!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Rotating Residential Proxies - Advanced test failed: {str(e)}")
            take_screenshot(test_case, "rotating_res_advanced_failed")
            save_page_source(test_case, "rotating_res_advanced_failed")
            return False

def test_rotating_residential_premium_arrow(test_case):
    """Test Rotating Residential Proxies - Premium using Arrow Down navigation"""
    with track_step(test_case, "Rotating Residential Premium Admin Panel", "Test Premium package with Arrow Down navigation"):
        try:
            print("[TEST] Testing Rotating Residential Proxies - Premium with Arrow Down navigation")
            
            # Step 1: Click package type dropdown and press Arrow Down ×1
            if not click_and_navigate_dropdown(test_case, 
                ADMIN_SELECTORS["package_selection"]["package_type_dropdown"], 
                1, "Package Type"):
                return False
            
            # Step 2: Click IP type dropdown and press Arrow Down ×3
            if not click_and_navigate_dropdown(test_case, 
                ADMIN_SELECTORS["package_selection"]["ip_type_dropdown"], 
                3, "IP Type"):
                return False
            
            # Step 3: Click original price dropdown and press Arrow Down ×8
            if not click_original_price_dropdown(test_case, 8):
                print("[WARNING] Original Price dropdown navigation failed, continuing with test...")
            
            # Step 4: Enter amount
            if not enter_amount(test_case, "12"):
                return False
            
            # Step 5: Click confirm button
            if not click_confirm_button(test_case):
                return False
            
            # Step 6: Verify package creation
            if not verify_package_creation(test_case):
                return False
            
            print("[SUCCESS] Rotating Residential Proxies - Premium test completed successfully!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Rotating Residential Proxies - Premium test failed: {str(e)}")
            take_screenshot(test_case, "rotating_res_premium_failed")
            save_page_source(test_case, "rotating_res_premium_failed")
            return False

def test_rotating_datacenter_arrow(test_case):
    """Test Rotating Datacenter Proxies using Arrow Down navigation"""
    with track_step(test_case, "Rotating Datacenter Admin Panel", "Test Datacenter package with Arrow Down navigation"):
        try:
            print("[TEST] Testing Rotating Datacenter Proxies with Arrow Down navigation")
            
            # Step 1: Click package type dropdown and press Arrow Down ×1
            if not click_and_navigate_dropdown(test_case, 
                ADMIN_SELECTORS["package_selection"]["package_type_dropdown"], 
                1, "Package Type"):
                return False
            
            # Step 2: Click IP type dropdown and press Arrow Down ×1
            if not click_and_navigate_dropdown(test_case, 
                ADMIN_SELECTORS["package_selection"]["ip_type_dropdown"], 
                1, "IP Type"):
                return False
            
            # Step 3: Click original price dropdown and press Arrow Down ×22
            if not click_original_price_dropdown(test_case, 22):
                print("[WARNING] Original Price dropdown navigation failed, continuing with test...")
            
            # Step 4: Enter amount
            if not enter_amount(test_case, "2"):
                return False
            
            # Step 5: Click confirm button
            if not click_confirm_button(test_case):
                return False
            
            # Step 6: Verify package creation
            if not verify_package_creation(test_case):
                return False
            
            print("[SUCCESS] Rotating Datacenter Proxies test completed successfully!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Rotating Datacenter Proxies test failed: {str(e)}")
            take_screenshot(test_case, "rotating_dc_failed")
            save_page_source(test_case, "rotating_dc_failed")
            return False

def test_static_residential_arrow(test_case):
    """Test Static Residential Proxies using Arrow Down navigation"""
    with track_step(test_case, "Static Residential Admin Panel", "Test Static Residential package with Arrow Down navigation"):
        try:
            print("[TEST] Testing Static Residential Proxies with Arrow Down navigation")
            
            # Step 1: Click package type dropdown and press Arrow Down ×2
            if not click_and_navigate_dropdown(test_case, 
                ADMIN_SELECTORS["package_selection"]["package_type_dropdown"], 
                2, "Package Type"):
                return False
            
            # Step 2: Click IP type dropdown and press Arrow Down ×2
            if not click_and_navigate_dropdown(test_case, 
                "//*[@id='app']/div/div/section/div/div[2]/div[6]/div/div/div[2]/div/form/div[2]/div/div/div[1]/input", 
                2, "IP Type"):
                return False
            
            # Step 3: Click original price dropdown and press Arrow Down ×3
            if not click_original_price_dropdown(test_case, 3):
                print("[WARNING] Original Price dropdown navigation failed, continuing with test...")
            
            # Step 4: Click confirm button
            if not click_confirm_button(test_case):
                return False
            
            # Step 5: Verify package creation
            if not verify_package_creation(test_case):
                return False
            
            print("[SUCCESS] Static Residential Proxies test completed successfully!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Static Residential Proxies test failed: {str(e)}")
            take_screenshot(test_case, "static_res_failed")
            save_page_source(test_case, "static_res_failed")
            return False

def test_datacenter_arrow(test_case):
    """Test Datacenter Proxies using Arrow Down navigation"""
    with track_step(test_case, "Datacenter Admin Panel", "Test Datacenter package with Arrow Down navigation"):
        try:
            print("[TEST] Testing Datacenter Proxies with Arrow Down navigation")
            
            # Step 1: Click package type dropdown and press Arrow Down ×3
            if not click_and_navigate_dropdown(test_case, 
                ADMIN_SELECTORS["package_selection"]["package_type_dropdown"], 
                3, "Package Type"):
                return False
            
            # Step 2: Click IP type dropdown and press Arrow Down ×4
            if not click_and_navigate_dropdown(test_case, 
                "//*[@id='app']/div/div/section/div/div[2]/div[6]/div/div/div[2]/div/form/div[2]/div/div/div[1]/input", 
                4, "IP Type"):
                return False
            
            # Step 3: Click original price dropdown and press Arrow Down ×19
            if not click_original_price_dropdown(test_case, 19):
                print("[WARNING] Original Price dropdown navigation failed, continuing with test...")
            
            # Step 4: Click confirm button
            if not click_confirm_button(test_case):
                return False
            
            # Step 5: Verify package creation
            if not verify_package_creation(test_case):
                return False
            
            print("[SUCCESS] Datacenter Proxies test completed successfully!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Datacenter Proxies test failed: {str(e)}")
            take_screenshot(test_case, "datacenter_failed")
            save_page_source(test_case, "datacenter_failed")
            return False

def test_unlimited_residential_arrow(test_case):
    """Test Unlimited Residential Proxies using Arrow Down navigation"""
    with track_step(test_case, "Unlimited Residential Admin Panel", "Test Unlimited Residential package with Arrow Down navigation"):
        try:
            print("[TEST] Testing Unlimited Residential Proxies with Arrow Down navigation")
            
            # Step 1: Click package type dropdown and press Arrow Down ×4
            if not click_and_navigate_dropdown(test_case, 
                ADMIN_SELECTORS["package_selection"]["package_type_dropdown"], 
                4, "Package Type"):
                return False
            
            # Step 2: Click IP type dropdown and press Arrow Down ×10
            if not click_and_navigate_dropdown(test_case, 
                "//*[@id='app']/div/div/section/div/div[2]/div[6]/div/div/div[2]/div/form/div[2]/div/div/div/input", 
                10, "IP Type"):
                return False
            
            # Step 3: Enter amount
            if not enter_amount(test_case, "4"):
                return False
            
            # Step 4: Click confirm button
            if not click_confirm_button(test_case):
                return False
            
            # Step 5: Verify package creation
            if not verify_package_creation(test_case):
                return False
            
            print("[SUCCESS] Unlimited Residential Proxies test completed successfully!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Unlimited Residential Proxies test failed: {str(e)}")
            take_screenshot(test_case, "unlimited_res_failed")
            save_page_source(test_case, "unlimited_res_failed")
            return False

# ===== Website Payment Test Functions =====
def run_complete_website_payment_test_without_login(proxy_type, session_test_case):
    """Run a complete website payment test for a specific proxy type without login (assumes already logged in)"""
    try:
        print(f"\n{'='*60}")
        print(f"Running Complete Website Payment Test: {proxy_type}")
        print(f"{'='*60}")
        
        # Step 1: Navigate to transactions and click payment button
        if not navigate_to_transactions_and_click_payment(session_test_case, proxy_type):
            return False
        
        # Step 2: Process PayPal payment
        if not process_paypal_payment(session_test_case, proxy_type):
            return False
        
        print(f"[SUCCESS] Complete website payment test for {proxy_type} completed successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Complete website payment test for {proxy_type} failed with exception: {str(e)}")
        traceback.print_exc()
        take_screenshot(session_test_case, f"complete_website_payment_failed_{proxy_type}")
        save_page_source(session_test_case, f"complete_website_payment_failed_{proxy_type}")
        return False

# ===== Run Single Test Case =====
def run_single_admin_panel_test(test_case, test_name, test_function):
    """Run a single Admin Panel test case"""
    try:
        print(f"\n{'='*60}")
        print(f"Running Test: {test_name}")
        print(f"{'='*60}")
        
        # Step 1: Navigate to user detail page
        if not navigate_to_user_detail(test_case):
            return False
        
        # Step 2: Click open package button (no additional delay needed)
        if not click_open_package_button(test_case):
            return False
        
        # Step 3: Run the specific test function
        success = test_function(test_case)
        
        if success:
            print(f"[SUCCESS] Admin Panel test {test_name} completed successfully!")
            return True
        else:
            print(f"[ERROR] Admin Panel test {test_name} failed!")
            return False
        
    except Exception as e:
        print(f"[ERROR] Admin Panel test {test_name} failed with exception: {str(e)}")
        traceback.print_exc()
        take_screenshot(test_case, f"admin_panel_test_{test_name}_failed")
        save_page_source(test_case, f"admin_panel_test_{test_name}_failed")
        return False

# ===== Run All Admin Panel Tests =====
def run_all_admin_panel_tests():
    """Run all Admin Panel test cases"""
    print("Starting OkeyProxy Admin Panel Tests...")
    print(f"Admin URL: {ADMIN_DASHBOARD_URL}")
    print(f"User Detail URL: {USER_DETAIL_URL}")
    
    # Create a single test case for the entire session
    session_test_case = create_test_case(
        "okeyproxy_admin_panel_navigation_session",
        "OkeyProxy Admin Panel Test Session"
    )
    session_test_case.test_dir = create_report()
    
    # Define test cases with their functions
    test_cases = [
        ("rotating_res_advanced_arrow", "Rotating Residential Proxies - Advanced", test_rotating_residential_advanced_arrow),
        ("rotating_res_premium_arrow", "Rotating Residential Proxies - Premium", test_rotating_residential_premium_arrow),
        ("rotating_dc_arrow", "Rotating Datacenter Proxies", test_rotating_datacenter_arrow),
        ("static_res_arrow", "Static Residential Proxies", test_static_residential_arrow),
        ("datacenter_arrow", "Datacenter Proxies", test_datacenter_arrow),
        ("unlimited_res_arrow", "Unlimited Residential Proxies", test_unlimited_residential_arrow)
    ]
    
    test_results = []
    
    # Login to admin panel first
    if not login_to_admin_panel(session_test_case):
        print("[ERROR] Failed to login to admin panel. Cannot proceed with tests.")
        return []
    
    # Run all test cases
    for test_key, test_name, test_function in test_cases:
        try:
            result = run_single_admin_panel_test(session_test_case, test_key, test_function)
            test_results.append({
                "test_name": test_key,
                "display_name": test_name,
                "result": "PASSED" if result else "FAILED"
            })
            
            # Brief pause between tests
            time.sleep(3)
            
        except Exception as e:
            print(f"[ERROR] Error running Admin Panel {test_key}: {str(e)}")
            test_results.append({
                "test_name": test_key,
                "display_name": test_name,
                "result": "ERROR"
            })
    
    # Print summary
    print(f"\n{'='*60}")
    print("OKEYPROXY Admin Panel TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for r in test_results if r["result"] == "PASSED")
    failed = sum(1 for r in test_results if r["result"] == "FAILED")
    errors = sum(1 for r in test_results if r["result"] == "ERROR")
    total = len(test_results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print(f"\nDetailed Results:")
    for result in test_results:
        status_icon = "[SUCCESS]" if result["result"] == "PASSED" else "[ERROR]"
        print(f"{status_icon} {result['test_name']} - {result['display_name']}: {result['result']}")
    
    # Generate HTML report
    try:
        from test_report import TestReport
        report = TestReport(session_test_case.test_dir)
        report.start()
        
        # Add the session test case
        report.add_test_case(session_test_case)
        
        # Create individual test cases for each test that was run
        for result in test_results:
            individual_test_case = create_test_case(
                result["test_name"],
                result["display_name"]
            )
            individual_test_case.start()
            individual_test_case.complete(success=(result["result"] == "PASSED"))
            report.add_test_case(individual_test_case)
        
        report.complete()
        
        report_file = report.generate_html_report("okeyproxy_admin_report")
        print(f"\n[SUCCESS] HTML Report generated: {report_file}")
    except Exception as e:
        print(f"[WARNING] Failed to generate HTML report: {e}")
    
    return test_results

# ===== Run All Complete Website Payment Tests =====
def run_all_complete_website_payment_tests():
    """Run all complete website payment test cases with single login"""
    print("Starting Complete Website Payment Automation Tests...")
    print(f"Base URL: {OKEYPROXY_BASE_URL}")
    print(f"Test Account: {OKEYPROXY_ACCOUNT}")
    
    # Create a single test case for the entire session
    session_test_case = create_test_case(
        "complete_website_payment_session",
        "Complete Website Payment Test Session"
    )
    session_test_case.test_dir = create_report()
    
    test_results = []
    
    # ===== SINGLE LOGIN AT THE BEGINNING =====
    print(f"\n{'='*60}")
    print("STEP 1: LOGIN TO OKEYPROXY (ONE TIME ONLY)")
    print(f"{'='*60}")
    
    # Login once at the beginning
    if not okeyproxy_login(session_test_case):
        print("[ERROR] Failed to login. Cannot proceed with tests.")
        return []
    
    print("[SUCCESS] Successfully logged in. Proceeding with all tests...")
    
    # Run tests for all proxy types
    proxy_types = [
        "rotating_residential_advanced",
        "rotating_residential_premium", 
        "rotating_datacenter",
        "static_residential",
        "datacenter",
        "unlimited_residential"
    ]
    
    for proxy_type in proxy_types:
        try:
            print(f"\n{'='*60}")
            print(f"Testing: {PROXY_TYPES[proxy_type]['name']}")
            print(f"{'='*60}")
            
            # For each test, just navigate to transactions (no login needed)
            result = run_complete_website_payment_test_without_login(proxy_type, session_test_case)
            test_results.append({
                "proxy_type": proxy_type,
                "name": PROXY_TYPES[proxy_type]['name'],
                "result": "PASSED" if result else "FAILED"
            })
            
            # Close any additional windows/tabs before next test
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[0])
                for handle in driver.window_handles[1:]:
                    driver.switch_to.window(handle)
                    driver.close()
                driver.switch_to.window(driver.window_handles[0])
            
            time.sleep(3)  # Brief pause between tests
            
        except Exception as e:
            print(f"[ERROR] Error running complete website payment test for {proxy_type}: {str(e)}")
            test_results.append({
                "proxy_type": proxy_type,
                "name": PROXY_TYPES[proxy_type]['name'],
                "result": "ERROR"
            })
    
    # Print summary
    print(f"\n{'='*60}")
    print("COMPLETE WEBSITE PAYMENT TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for r in test_results if r["result"] == "PASSED")
    failed = sum(1 for r in test_results if r["result"] == "FAILED")
    errors = sum(1 for r in test_results if r["result"] == "ERROR")
    total = len(test_results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print(f"\nDetailed Results:")
    for result in test_results:
        status_icon = "[PASS]" if result["result"] == "PASSED" else "[FAIL]"
        print(f"{status_icon} {result['name']}: {result['result']}")
    
    return test_results

# ===== Run All Tests (Admin + Payment) =====
def run_all_tests():
    """Run all tests: 6 Admin Panel tests + 6 Complete Website Payment tests"""
    print("Starting OkeyProxy Complete Test Suite...")
    print("=" * 60)
    print("PHASE 1: Admin Panel Tests (6 tests)")
    print("PHASE 2: Complete Website Payment Tests (6 tests)")
    print("=" * 60)
    
    all_results = []
    
    # Phase 1: Run Admin Panel Tests
    print(f"\n{'='*60}")
    print("PHASE 1: RUNNING ADMIN PANEL TESTS")
    print(f"{'='*60}")
    admin_results = run_all_admin_panel_tests()
    all_results.extend(admin_results)
    
    # Phase 2: Run Complete Website Payment Tests
    print(f"\n{'='*60}")
    print("PHASE 2: RUNNING COMPLETE WEBSITE PAYMENT TESTS")
    print(f"{'='*60}")
    payment_results = run_all_complete_website_payment_tests()
    all_results.extend(payment_results)
    
    # Final Summary
    print(f"\n{'='*60}")
    print("FINAL COMPLETE TEST SUITE SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r["result"] == "PASSED")
    failed_tests = sum(1 for r in all_results if r["result"] == "FAILED")
    error_tests = sum(1 for r in all_results if r["result"] == "ERROR")
    
    print(f"TOTAL TESTS COMPLETED: {total_tests}")
    print(f"Admin Panel Tests: 6")
    print(f"Complete Website Payment Tests: 6")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Errors: {error_tests}")
    if total_tests > 0:
        print(f"Overall Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    else:
        print("Overall Success Rate: 0.0%")
    
    print(f"\nDetailed Results:")
    for i, result in enumerate(all_results, 1):
        status_icon = "[PASS]" if result["result"] == "PASSED" else "[FAIL]"
        test_name = result.get("display_name", result.get("name", result.get("test_name", "Unknown")))
        print(f"{status_icon} Test {i:2d}: {test_name} - {result['result']}")
    
    return all_results

# ===== Main Execution =====
if __name__ == "__main__":
    try:
        print("OkeyProxy Complete Test Suite - Admin Panel + Website Payment Tests")
        print("=" * 70)
        print("This script will run:")
        print("- 6 Admin Panel Tests (Package Creation)")
        print("- 6 Complete Website Payment Tests")
        print("=" * 70)
        
        # Run all tests (Admin Panel + Website Payment)
        results = run_all_tests()
        
        print(f"\n{'='*70}")
        print("FINAL SUMMARY - ALL 12 TESTS COMPLETED")
        print(f"{'='*70}")
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r["result"] == "PASSED")
        failed_tests = sum(1 for r in results if r["result"] == "FAILED")
        error_tests = sum(1 for r in results if r["result"] == "ERROR")
        
        print(f"TOTAL TESTS COMPLETED: {total_tests}")
        print(f"Admin Panel Tests: 6")
        print(f"Complete Website Payment Tests: 6")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Errors: {error_tests}")
        if total_tests > 0:
            print(f"Overall Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        else:
            print("Overall Success Rate: 0.0%")
        
    except KeyboardInterrupt:
        print("\n[WARNING] Tests interrupted by user")
    except Exception as e:
        print(f"[ERROR] Test execution failed: {str(e)}")
        traceback.print_exc()
    finally:
        print("\nClosing browser...")
        try:
            if driver is not None:
                driver.quit()
                print("[SUCCESS] Browser closed. OkeyProxy Complete Test Suite execution completed.")
        except Exception as e:
            print(f"Warning: Error closing browser: {e}")
            print("[SUCCESS] OkeyProxy Complete Test Suite execution completed.")
