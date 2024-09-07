import hashlib
import time
import os
import logging
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from fake_useragent import UserAgent
from pyvirtualdisplay import Display
import undetected_chromedriver.v2 as uc  # Use undetected-chromedriver to bypass detection
from bs4 import BeautifulSoup  # For parsing HTML

# Data directory path inside the container (mounted from the host)
DATA_DIR = "/usr/src/app/data"
LOG_FILE = os.path.join(DATA_DIR, "log.txt")
HEADER_JSON_PATH = os.path.join("/usr/src/app", "header.json")
OUTPUT_JSON_PATH = os.path.join(DATA_DIR, "output.json")

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Function to delete all HTML and PNG files and clear log.txt on script start
def clean_up():
    for file_name in os.listdir(DATA_DIR):
        if file_name.endswith(".html") or file_name.endswith(".png"):
            os.remove(os.path.join(DATA_DIR, file_name))
            logging.info(f"Deleted file: {file_name}")
    with open(LOG_FILE, "w") as f:
        f.truncate(0)
    logging.info(f"Cleared log file: {LOG_FILE}")
    if os.path.exists(OUTPUT_JSON_PATH):
        os.remove(OUTPUT_JSON_PATH)
        logging.info(f"Deleted output file: {OUTPUT_JSON_PATH}")

# Load session headers from header.json
def load_session_info():
    if os.path.exists(HEADER_JSON_PATH):
        with open(HEADER_JSON_PATH, 'r') as f:
            session_info = json.load(f)
            print("Loaded header.json content:", json.dumps(session_info, indent=4))
            return session_info
    else:
        print("header.json not found.")
    return {}

# Custom logging formatter to prepend run number
class RunNumberFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, run_number=None):
        super().__init__(fmt, datefmt)
        self.run_number = run_number

    def format(self, record):
        record.run_number = self.run_number
        return super().format(record)

# Initialize the run number from working.txt inside the data directory
def get_run_number():
    filename = os.path.join(DATA_DIR, "working.txt")
    if os.path.exists(filename):
        with open(filename, "r") as f:
            run_number = f.read().strip()
            run_number = int(run_number) if run_number.isdigit() else 0
    else:
        run_number = 0
    run_number += 1
    with open(filename, "w") as f:
        f.write(str(run_number))
    return run_number

# Generate a unique hash for each event
def generate_unique_hash():
    timestamp = str(int(time.time()))
    unique_hash = hashlib.md5(timestamp.encode()).hexdigest()
    return unique_hash

# Custom wait function that adds delay and logs waiting
def wait_before_action(seconds=3):
    logging.info(f"Waiting for {seconds} seconds before next action")
    time.sleep(seconds)

# Save the page source and take a screenshot, logging both with a unique hash
def event_log(step, unique_hash, run_number, driver):
    # Save the page source
    html_filename = os.path.join(DATA_DIR, f"{run_number}_{step}_{unique_hash}.html")
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    logging.info(f"Saved page source to {html_filename}")

    # Wait before taking the screenshot
    wait_before_action()

    # Take a screenshot
    screenshot_filename = os.path.join(DATA_DIR, f"{run_number}_{step}_{unique_hash}.png")
    driver.save_screenshot(screenshot_filename)
    logging.info(f"Saved screenshot to {screenshot_filename}")

def extract_articles(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    articles = soup.find_all('article')
    articles_data = [article.get_text(strip=True) for article in articles]
    return articles_data

class ChatGPTAutomation:
    def __init__(self, prompt):
        self.run_number = get_run_number()
        self.prompt = prompt

        # Set up logging to log to both console and file
        file_handler = logging.FileHandler(LOG_FILE)
        formatter = RunNumberFormatter(fmt='RUN #: %(run_number)s - %(asctime)s - %(message)s', run_number=self.run_number)

        # Apply the formatter to both file and stream handlers
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)

        # Also set it for the console output
        logging.getLogger().handlers[0].setFormatter(formatter)
        logging.getLogger().setLevel(logging.INFO)  # Set log level

        logging.info(f"Run number: {self.run_number}")
        self.driver = None
        self.init_driver()

        # Clean up before starting the script
        clean_up()

        # Start timer
        self.start_time = time.time()

    def init_driver(self):
        """
        Initialize Chrome WebDriver with undetected-chromedriver to bypass Cloudflare.
        """
        # Start virtual display (optional)
        display = Display(visible=0, size=(800, 800))
        display.start()

        # Use undetected_chromedriver
        options = ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('start-maximized')
        options.add_argument('enable-automation')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument('--disable-gpu')
        options.add_argument("--log-level=3")

        # Generate a fake user agent
        ua = UserAgent()
        fake_ua = ua.random
        options.add_argument(f'user-agent={fake_ua}')
        logging.info(f"Using User Agent: {fake_ua}")

        # Initialize undetected-chromedriver WebDriver
        self.driver = uc.Chrome(options=options)
        logging.info("Initialized Chrome WebDriver with fake user agent and virtual display")

        # Add session token into LocalStorage
        session_info = load_session_info()
        if session_info and 'accessToken' in session_info:
            logging.info("Session info loaded from header.json, injecting into LocalStorage")
            self.driver.get("https://chatgpt.com")  # Load the page first
            # Inject token into LocalStorage
            self.driver.execute_script(f"localStorage.setItem('accessToken', '{session_info['accessToken']}');")

    def inject_cookies(self, cookies):
        """Inject cookies into the browser session"""
        self.driver.get("https://chatgpt.com")  # Ensure the right domain is loaded
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        logging.info("Injected cookies into the browser session.")

    def visit_chatgpt(self):
        """
        Visit ChatGPT, click login button, enter a message, and take screenshots.
        """
        try:
            # Step 1: Navigate to ChatGPT page with injected session
            url = "https://chatgpt.com/"
            logging.info(f"Navigating to {url}")
            self.driver.get(url)
            
            # Wait for the page to load and check if it's logged in
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            logging.info("Page loaded successfully")

            # Generate a unique hash for this event
            unique_hash = generate_unique_hash()

            # Step 2: Save page source and take screenshot
            event_log("chatgpt_homepage", unique_hash, self.run_number, self.driver)

            # Step 3: Find the textarea, enter the message, and submit
            logging.info("Finding the textarea")
            textarea = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea#prompt-textarea"))
            )
            logging.info("Entering message into textarea")
            textarea.send_keys(self.prompt)  # Use the prompt from argument
            textarea.send_keys(Keys.RETURN)  # Press Enter to submit
            logging.info("Submitted message")

            # Wait and take a final screenshot after submitting the message
            wait_before_action(3)
            event_log("post_message_submission", unique_hash, self.run_number, self.driver)

            # Extract content from <article> tags
            articles_data = extract_articles(self.driver)

            # Prepare the JSON object with timing information
            end_time = time.time()
            output_data = {
                "run_number": self.run_number,
                "prompt": self.prompt,
                "start_time": self.start_time,
                "end_time": end_time,
                "articles": articles_data
            }

            # Save to output.json
            with open(OUTPUT_JSON_PATH, "w") as f:
                json.dump(output_data, f, indent=4)
            logging.info(f"Saved output to {OUTPUT_JSON_PATH}")
            print("Output JSON:", json.dumps(output_data, indent=4))

        except TimeoutException:
            logging.error("Timeout while loading the page or waiting for elements")
        except WebDriverException as e:
            logging.error(f"WebDriver error occurred: {e}")

    def quit(self):
        if self.driver:
            wait_before_action(2)
            self.driver.quit()
            logging.info("Browser closed successfully")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        print("PROMPT REQUIRED")
        sys.exit(1)
    
    prompt = sys.argv[1]

    logging.info("Starting ChatGPT Automation")

    try:
        # Initialize the automation class
        automation = ChatGPTAutomation(prompt=prompt)
        
        # Visit ChatGPT with session injected and attempt to log in and submit message
        automation.visit_chatgpt()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        # Always quit the driver and save progress
        automation.quit()
