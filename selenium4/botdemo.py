import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

class DemoBot:
    def __init__(self):
        # Set up the Edge driver options
        self.options = webdriver.EdgeOptions()
        self.options.add_argument("--headless=new")
        self.options.add_argument("--window-size=1320,1080")
        self.options.add_argument("--ignore-certificate-errors")
        self.options.add_argument("--ignore-ssl-errors")
        self.options.add_argument("log-level=2")
        self.options.add_argument("--save-page-as-mhtml")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        )
        # Adding argument to disable the AutomationControlled flag
        self.options.add_argument("--disable-blink-features=AutomationControlled")

        # Exclude the collection of enable-automation switches
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])

        # Turn-off userAutomationExtension
        self.options.add_experimental_option("useAutomationExtension", False)
        
        # Get the directory where the script is located
        self.DIR = os.path.dirname(os.path.abspath(__file__))

        # Initialize the Edge driver
        self.driver = webdriver.Edge(options=self.options)

    def parse_url(self, url):
        id = ""
        # Split the URL by the '/'
        url_parts = url.split("/")

        # Extract the last part of the URL
        last_part = url_parts[-2]

        # Split the last part by '-'
        parts = last_part.split("-")

        topic_number = parts[-4]
        q_number = parts[-2]

        topic_number_formatted = f"{int(topic_number):02d}"
        q_number_formatted = f"{int(q_number):03d}"
        return f"{topic_number_formatted}.{q_number_formatted}{id}.mhtml"

    def get_total_pages(self, url):
        """
        Get the total number of pages on the list page.
        """
        # Navigate to the list page
        self.driver.get(url)

        # Wait for the page to load and find the page select dropdown
        wait = WebDriverWait(self.driver, 10)
        page_select = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".discussion-list-page-select")
            )
        )

        # Get all the options in the dropdown
        options = page_select.find_elements(By.TAG_NAME, "option")

        # Get the value of the last option
        total_pages = int(options[-1].get_attribute("value"))
        return total_pages

    def process_page(self, url, code):
        """
        Take a snapshot of the given URL and save it as an MHTML file.
        """
        self.driver.get(url)

        # Wait for the page to load and click the "Reveal Solution" button
        wait = WebDriverWait(self.driver, 10)
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".reveal-solution"))
        ).click()

        # Remove unwanted elements from the page
        self.driver.execute_script(
            "$('.footer-cert, #rs-footer,.full-width-header,.sec-spacer > .container >.row:nth-child(1), .sec-spacer > .container >.row:nth-child(2),.sec-spacer > .container >.row:nth-child(4), .action-row-container,#unlimNo,.all-questions-link,.discussion-link,.bottom-block,.fa-angle-up').remove()"
        )
        time.sleep(1)

        # Save the page as an MHTML file
        mhtml_file_path = os.path.join(self.DIR, code, self.parse_url(url))
        directory = os.path.dirname(mhtml_file_path)
        os.makedirs(directory, exist_ok=True)
        res = self.driver.execute_cdp_cmd("Page.captureSnapshot", {})
        with open(mhtml_file_path, "w", newline="") as f:
            f.write(res["data"])

    def find_all_records(self, url, code):
        """
        Find all the discussion links related to the given code.
        """
        # Navigate to the URL
        self.driver.get(url)

        # Wait for the page to load
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "discussion-link")))

        # Find all the discussion links
        discussion_links = self.driver.find_elements(By.CLASS_NAME, "discussion-link")

        # Filter the links that are related to the given code
        filtered_links = []
        for link in discussion_links:
            if code.lower() in link.get_attribute("href").lower():
                filtered_links.append(link.get_attribute("href"))

        return filtered_links

    def close(self):
        """
        Close the browser.
        """
        self.driver.quit()
