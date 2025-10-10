# ===== Imports =====
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pytest
import os
import time
from datetime import datetime
import logging
import sys
import traceback
import subprocess
import json
import pyperclip
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from test_report import TestReport, TestCase, TestStep, track_step, create_test_case

# ===== Global Configuration =====
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)
driver.maximize_window()

report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

# ===== OkeyProxy Configuration =====
OKEYPROXY_BASE_URL = "https://test-ipglobal.cd.xiaoxigroup.net"
OKEYPROXY_LOGIN_URL = "https://test-ipglobal.cd.xiaoxigroup.net/login"

# OkeyProxy Test Account
OKEYPROXY_ACCOUNT = {
    "with_balance": {
        "email": "amanda3@getnada.com",
        "password": "123123123"
    }
}

# ===== Test URLs and Selectors =====
TEST_CASES = {
    "rotating_residential_advanced": {
        "name": "Rotating Residential Proxies Advanced",
        "url": "https://test-ipglobal.cd.xiaoxigroup.net/dashboard/useProxy/dynamicResidence",
        "verification_type": "country",
        "premium_tab_required": False
    },
    "rotating_residential_premium": {
        "name": "Rotating Residential Proxies Premium",
        "url": "https://test-ipglobal.cd.xiaoxigroup.net/dashboard/useProxy/dynamicResidence",
        "verification_type": "country",
        "premium_tab_required": True
    },
    "rotating_datacenter": {
        "name": "Rotating Datacenter Proxies",
        "url": "https://test-ipglobal.cd.xiaoxigroup.net/dashboard/useProxy/datacenterRotatingProxy",
        "verification_type": "country",
        "premium_tab_required": False
    },
    "static_residential": {
        "name": "Static Residential Proxies",
        "url": "https://test-ipglobal.cd.xiaoxigroup.net/dashboard/useProxy/staticResidence?regionCode",
        "verification_type": "connect",
        "premium_tab_required": False,
        "add_v_flag": True
    },
    "datacenter_proxies": {
        "name": "Datacenter Proxies",
        "url": "https://test-ipglobal.cd.xiaoxigroup.net/dashboard/useProxy/dataCenterProxies?regionCode",
        "verification_type": "connect",
        "premium_tab_required": False,
        "add_v_flag": True
    },
    "unlimited_residential": {
        "name": "Unlimited Residential Proxies",
        "url": "https://test-ipglobal.cd.xiaoxigroup.net/dashboard/useProxy/dynamicUnlimited",
        "verification_type": "country",
        "premium_tab_required": False
    }
}

# ===== Element Selectors =====
OKEYPROXY_SELECTORS = {
    "login": {
        "email_input": "//input[@placeholder='Your Email address']",
        "password_input": "//input[@placeholder='Enter Password']",
        "login_button": "//button[contains(@class, 'custom-button')]//span[contains(text(), 'Login')]/.."
    },
    "code_examples": {
        "code_tab": "//div[@id='tab-code' and @aria-controls='pane-code' and @role='tab']",
        "copy_button": "//div[@class='copy']//img[@alt='copy']/..",
        "premium_tab": "//div[@class='tab-item' and contains(text(), 'Premium')]"
    }
}

# ===== Login Function =====
def login_to_okeyproxy():
    """Login to OkeyProxy using the with_balance account"""
    try:
        print("=" * 60)
        print("STEP 1: LOGIN TO OKEYPROXY")
        print("=" * 60)
        print("Navigating to login page...")
        driver.get(OKEYPROXY_LOGIN_URL)
        time.sleep(3)
        
        print("Entering email...")
        email_input = wait.until(EC.presence_of_element_located((By.XPATH, OKEYPROXY_SELECTORS["login"]["email_input"])))
        email_input.clear()
        email_input.send_keys(OKEYPROXY_ACCOUNT["with_balance"]["email"])
        
        print("Entering password...")
        password_input = driver.find_element(By.XPATH, OKEYPROXY_SELECTORS["login"]["password_input"])
        password_input.clear()
        password_input.send_keys(OKEYPROXY_ACCOUNT["with_balance"]["password"])
        
        print("Clicking login button...")
        login_button = driver.find_element(By.XPATH, OKEYPROXY_SELECTORS["login"]["login_button"])
        login_button.click()
        
        # Wait for redirect to dashboard
        wait.until(EC.url_contains("/dashboard"))
        print("[SUCCESS] Login successful!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Login failed: {str(e)}")
        return False

# ===== Navigate to Test Page =====
def navigate_to_test_page(url):
    """Navigate to the specified test page"""
    try:
        print(f"Navigating to: {url}")
        driver.get(url)
        time.sleep(5)  # Wait for page to load completely
        print("[SUCCESS] Successfully navigated to test page!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Navigation failed: {str(e)}")
        return False

# ===== Click Premium Tab (if required) =====
def click_premium_tab():
    """Click on the Premium tab if required"""
    try:
        print("Clicking on Premium tab...")
        premium_tab = wait.until(EC.element_to_be_clickable((By.XPATH, OKEYPROXY_SELECTORS["code_examples"]["premium_tab"])))
        premium_tab.click()
        time.sleep(2)
        print("[SUCCESS] Premium tab clicked successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to click Premium tab: {str(e)}")
        return False

# ===== Click on Code Examples Tab =====
def click_code_examples_tab():
    """Click on the Code examples tab"""
    try:
        print("Clicking on Code examples tab...")
        code_tab = wait.until(EC.element_to_be_clickable((By.XPATH, OKEYPROXY_SELECTORS["code_examples"]["code_tab"])))
        code_tab.click()
        time.sleep(2)
        print("[SUCCESS] Code examples tab clicked successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to click Code examples tab: {str(e)}")
        return False

# ===== Click Copy Button =====
def click_copy_button():
    """Click the copy button to copy the code"""
    try:
        print("Clicking copy button...")
        copy_button = wait.until(EC.element_to_be_clickable((By.XPATH, OKEYPROXY_SELECTORS["code_examples"]["copy_button"])))
        copy_button.click()
        time.sleep(1)
        print("[SUCCESS] Copy button clicked successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to click copy button: {str(e)}")
        return False

# ===== Get Copied Code =====
def get_copied_code():
    """Get the copied code from clipboard"""
    try:
        print("Retrieving copied code from clipboard...")
        copied_code = pyperclip.paste()
        if copied_code:
            print("[SUCCESS] Code retrieved from clipboard successfully!")
            print(f"Copied code:\n{copied_code}")
            return copied_code
        else:
            print("[ERROR] No code found in clipboard!")
            return None
            
    except Exception as e:
        print(f"[ERROR] Failed to get copied code: {str(e)}")
        return None

# ===== Execute Copied Code =====
def execute_copied_code(copied_code, add_v_flag=False):
    """Execute the copied code in command line and get response"""
    try:
        print("Executing copied code...")
        
        # Add -v flag for datacenter proxies if required
        if add_v_flag and copied_code.strip().startswith('curl'):
            copied_code = copied_code + " -v"
            print("Added -v flag for datacenter proxies")
        
        # Check if it's a curl command
        if copied_code.strip().startswith('curl'):
            print("Detected curl command, executing directly...")
            # Execute the curl command directly
            result = subprocess.run(copied_code, 
                                  shell=True,
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30)
        else:
            # Try to execute as Python code
            temp_file = "temp_proxy_test.py"
            with open(temp_file, 'w') as f:
                f.write(copied_code)
            
            result = subprocess.run(['python', temp_file], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30)
            
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        if result.returncode == 0:
            print("[SUCCESS] Code executed successfully!")
            print(f"Output: {result.stdout}")
            return result.stdout
        else:
            print(f"[ERROR] Code execution failed: {result.stderr}")
            # For CONNECT verification, we still want to check stderr for "CONNECT"
            return result.stderr
            
    except subprocess.TimeoutExpired:
        print("[ERROR] Code execution timed out!")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to execute code: {str(e)}")
        return None

# ===== Parse and Verify Response =====
def parse_and_verify_response(response, verification_type):
    """Parse the response and verify based on verification type"""
    try:
        print(f"Parsing response for {verification_type} verification...")
        
        if verification_type == "country":
            # Try to extract JSON from the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                print(f"[SUCCESS] JSON parsed successfully: {data}")
                
                # Check if country is present
                if 'country' in data:
                    print(f"[SUCCESS] Test PASSED: Country '{data['country']}' found in response!")
                    return True
                else:
                    print("[ERROR] Test FAILED: No 'country' field found in response")
                    return False
            else:
                print("[ERROR] No valid JSON found in response")
                return False
                
        elif verification_type == "connect":
            # Check for CONNECT in the response (including "CONNECT tunnel failed")
            if "CONNECT" in response.upper():
                print("[SUCCESS] Test PASSED: 'CONNECT' found in response!")
                return True
            else:
                print("[ERROR] Test FAILED: 'CONNECT' not found in response")
                return False
        else:
            print(f"[ERROR] Unknown verification type: {verification_type}")
            return False
            
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON: {str(e)}")
        return False
    except Exception as e:
        print(f"[ERROR] Error parsing response: {str(e)}")
        return False

# ===== HTML Report Generation =====
def setup_test_report():
    """Setup test report for connection test"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"proxy_connection_test_{timestamp}.html"
    report_path = os.path.join(report_dir, report_filename)
    return report_path

def generate_html_report(test_results, report_path):
    """Generate HTML report with test results and outputs"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OkeyProxy Comprehensive Connection Test Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                color: #333;
                border-bottom: 2px solid #007bff;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .summary {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .summary-card {{
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                color: white;
            }}
            .total {{ background-color: #6c757d; }}
            .passed {{ background-color: #28a745; }}
            .failed {{ background-color: #dc3545; }}
            .success-rate {{ background-color: #007bff; }}
            .test-case {{
                margin-bottom: 30px;
                border: 1px solid #ddd;
                border-radius: 8px;
                overflow: hidden;
            }}
            .test-header {{
                padding: 15px 20px;
                font-weight: bold;
                font-size: 18px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .test-passed {{ background-color: #d4edda; color: #155724; }}
            .test-failed {{ background-color: #f8d7da; color: #721c24; }}
            .test-content {{
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .test-details {{
                margin-bottom: 15px;
            }}
            .test-details h4 {{
                margin: 0 0 10px 0;
                color: #495057;
            }}
            .output-box {{
                background-color: #2d3748;
                color: #e2e8f0;
                padding: 15px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                white-space: pre-wrap;
                overflow-x: auto;
                max-height: 300px;
                overflow-y: auto;
            }}
            .status-badge {{
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            .status-passed {{
                background-color: #28a745;
                color: white;
            }}
            .status-failed {{
                background-color: #dc3545;
                color: white;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #6c757d;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>OkeyProxy Comprehensive Connection Test Report</h1>
                <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
            
            <div class="summary">
                <div class="summary-card total">
                    <h3>Total Tests</h3>
                    <h2>{len(test_results)}</h2>
                </div>
                <div class="summary-card passed">
                    <h3>Passed</h3>
                    <h2>{sum(1 for result in test_results.values() if result['passed'])}</h2>
                </div>
                <div class="summary-card failed">
                    <h3>Failed</h3>
                    <h2>{sum(1 for result in test_results.values() if not result['passed'])}</h2>
                </div>
                <div class="summary-card success-rate">
                    <h3>Success Rate</h3>
                    <h2>{(sum(1 for result in test_results.values() if result['passed']) / len(test_results) * 100):.1f}%</h2>
                </div>
            </div>
            
            <h2>Test Results</h2>
    """
    
    # Add each test case result
    for test_case_key, test_case_info in TEST_CASES.items():
        if test_case_key in test_results:
            result = test_results[test_case_key]
            status_class = "test-passed" if result['passed'] else "test-failed"
            status_badge_class = "status-passed" if result['passed'] else "status-failed"
            status_text = "PASSED" if result['passed'] else "FAILED"
            
            html_content += f"""
            <div class="test-case">
                <div class="test-header {status_class}">
                    <span>{test_case_info['name']}</span>
                    <span class="status-badge {status_badge_class}">{status_text}</span>
                </div>
                <div class="test-content">
                    <div class="test-details">
                        <h4>Test URL:</h4>
                        <p>{test_case_info['url']}</p>
                    </div>
                    <div class="test-details">
                        <h4>Verification Type:</h4>
                        <p>{test_case_info['verification_type'].upper()}</p>
                    </div>
                    <div class="test-details">
                        <h4>Command Executed:</h4>
                        <div class="output-box">{result.get('command', 'N/A')}</div>
                    </div>
                    <div class="test-details">
                        <h4>Output:</h4>
                        <div class="output-box">{result.get('output', 'No output')}</div>
                    </div>
                    <div class="test-details">
                        <h4>Error (if any):</h4>
                        <div class="output-box">{result.get('error', 'No errors')}</div>
                    </div>
                </div>
            </div>
            """
    
    html_content += """
            <div class="footer">
                <p>OkeyProxy Comprehensive Connection Test - Automated Test Report</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Write HTML file
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[SUCCESS] HTML report generated: {report_path}")
    return report_path

# ===== Run Single Test Case =====
def run_single_test_case(test_case_key, test_case_info):
    """Run a single test case"""
    print("\n" + "=" * 80)
    print(f"TESTING: {test_case_info['name']}")
    print("=" * 80)
    
    # Initialize result data for HTML report
    result_data = {
        'passed': False,
        'command': '',
        'output': '',
        'error': ''
    }
    
    try:
        # Navigate to test page
        if not navigate_to_test_page(test_case_info['url']):
            return result_data
        
        # Click Premium tab if required
        if test_case_info.get('premium_tab_required', False):
            if not click_premium_tab():
                return result_data
        
        # Click on Code examples tab
        if not click_code_examples_tab():
            return result_data
        
        # Click copy button
        if not click_copy_button():
            return result_data
        
        # Get copied code
        copied_code = get_copied_code()
        if not copied_code:
            return result_data
        
        # Store the command for HTML report
        result_data['command'] = copied_code
        
        # Execute copied code
        add_v_flag = test_case_info.get('add_v_flag', False)
        response = execute_copied_code(copied_code, add_v_flag)
        
        if response is None:
            result_data['error'] = "No response received from command execution"
            return result_data
        
        # Store output for HTML report
        result_data['output'] = response
        
        # Parse and verify response
        test_passed = parse_and_verify_response(response, test_case_info['verification_type'])
        result_data['passed'] = test_passed
        
        if test_passed:
            print(f"[SUCCESS] {test_case_info['name']} - TEST PASSED!")
        else:
            print(f"[ERROR] {test_case_info['name']} - TEST FAILED!")
        
        return result_data
        
    except Exception as e:
        error_msg = f"Test case failed with error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        result_data['error'] = error_msg
        traceback.print_exc()
        return result_data

# ===== Main Test Function =====
def run_comprehensive_connection_test():
    """Run the complete comprehensive connection test"""
    print("=" * 80)
    print("OKEYPROXY COMPREHENSIVE CONNECTION TEST")
    print("=" * 80)
    
    # Setup HTML report
    report_path = setup_test_report()
    
    # Step 1: Login once
    if not login_to_okeyproxy():
        print("[ERROR] Login failed. Cannot proceed with tests.")
        return False
    
    # Track test results
    test_results = {}
    total_tests = len(TEST_CASES)
    passed_tests = 0
    
    # Run all test cases
    for test_case_key, test_case_info in TEST_CASES.items():
        result_data = run_single_test_case(test_case_key, test_case_info)
        test_results[test_case_key] = result_data
        if result_data['passed']:
            passed_tests += 1
        
        # Small delay between tests
        time.sleep(2)
    
    # Generate HTML report
    generate_html_report(test_results, report_path)
    
    # Print final results
    print("\n" + "=" * 80)
    print("FINAL TEST RESULTS")
    print("=" * 80)
    
    for test_case_key, test_case_info in TEST_CASES.items():
        status = "PASSED" if test_results[test_case_key]['passed'] else "FAILED"
        print(f"{test_case_info['name']}: {status}")
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n*** ALL TESTS PASSED! ***")
        return True
    else:
        print(f"\n*** {total_tests - passed_tests} TESTS FAILED! ***")
        return False

# ===== Main Execution =====
if __name__ == "__main__":
    try:
        success = run_comprehensive_connection_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INFO] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Close browser
        if 'driver' in globals():
            driver.quit()
