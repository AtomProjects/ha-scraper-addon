import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_website(url, password):
    """
    Scrape a table from a website that requires password login, specifically a <table> within a <center> tag.
    
    Args:
        url (str): The URL of the website to scrape
        password (str): The password for login
    
    Returns:
        list: List of lists, where each inner list represents a row in the table,
              and each element in the inner list is a cell in that row.
              Returns an empty list if no table is found or if there's an error.
    """
    # Set up Chrome options for headless operation (no GUI)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")

    driver = None
    try:
        # Use webdriver_manager to automatically handle driver installation
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        logger.info(f"Navigating to {url}")
        driver.get(url)

        # Wait for page to load
        time.sleep(5)

        # Log current URL to make sure we're on the correct page
        logger.info(f"Current URL: {driver.current_url}")

        # Check if we need to log in by looking for password field
        if len(driver.find_elements(By.ID, "password")) > 0 or len(driver.find_elements(By.NAME, "password")) > 0:
            logger.info("Login form detected")

            # Wait for password field to be present
            try:
                password_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "password"))
                )
            except:
                password_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "password"))
                )

            logger.info("Entering password")
            password_field.clear()
            password_field.send_keys(password)

            # Wait for submit button to be clickable
            try:
                submit_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
                )
            except:
                try:
                    submit_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
                    )
                except:
                    try:
                        submit_button = WebDriverWait(driver, 10).until(
                           EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Login') or contains(text(), 'Sign in') or contains(text(), 'Submit')]"))
                        )
                    except:
                        submit_button = None
            if submit_button:
                logger.info("Clicking submit button")
                submit_button.click()
            else:
                logger.error("No submit button found!")
                return []
            # Wait for page to load after login
            logger.info("Waiting for page to load after login")
            time.sleep(10)

            logger.info(f"Current URL after login attempt: {driver.current_url}")

        # Get the page source
        logger.info("Getting page content")
        page_source = driver.page_source

        # Parse the HTML content
        soup = BeautifulSoup(page_source, 'html.parser')

        # Find the table inside the center tag
        center_tag = soup.find('center')
        if center_tag:
            table = center_tag.find('table')
        else:
            table = None
            logger.warning("No <center> element found on the page.")

        if table:
            logger.info("Found table within <center> element.")
            table_data = []
            rows = table.find_all('tr')
            for row in rows:
                row_data = []
                cells = row.find_all(['td', 'th']) # Find both td and th elements
                for cell in cells:
                    row_data.append(cell.get_text().strip())
                table_data.append(row_data)
            
            return table_data
        else:
            logger.warning("No table found within <center> element.")
            if driver:
                screenshot_path = "debug_screenshot.png"
                driver.save_screenshot(screenshot_path)
                logger.info(f"Saved debug screenshot to {screenshot_path}")
            return []

    except Exception as e:
        logger.error(f"Error scraping website: {e}", exc_info=True)
        return []

    finally:
        if driver:
            driver.quit()

def main():
    # Configuration
    website_url = os.environ.get("WEBSITE_URL", "https://fws-leipzig.vpo.de/restrictedDayView") # Default value if env var is not set
    password = os.environ.get("PASSWORD", "FWS_LEIPZIG")  # Default value if env var is not set

    logger.info("Starting web scraping process")

    # Scrape the website
    scraped_data = scrape_website(website_url, password)

    if scraped_data:
        # Print the table data to the console
        print("Scraped data from website (table within <center>):")
        for row in scraped_data:
            print(" | ".join(row))

        logger.info(f"Scraped table with {len(scraped_data)} rows. Data printed to console.")
    else:
        logger.warning("No data scraped from the website or no table found.")

if __name__ == "__main__":
    main()