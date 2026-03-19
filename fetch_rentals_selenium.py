import os
import json
import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def fetch_rentals_ca_automated():
    print("Starting automated Rentals.ca fetch via Selenium...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Use a real user agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        url = "https://rentals.ca/vancouver"
        print(f"Navigating to {url}...")
        driver.get(url)
        
        # Wait for content to load and potential Cloudflare challenges to resolve
        time.sleep(10)
        
        # Scroll down to load more content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        source = driver.page_source
        driver.quit()
        
        # Save the source to rentals_raw.json so the main crawler can process it
        with open("rentals_raw.json", "w", encoding="utf-8") as f:
            f.write(source)
            
        print(f"SUCCESS: Captured {len(source)} characters to rentals_raw.json")
        return True
        
    except Exception as e:
        print(f"FAILED to fetch Rentals.ca: {e}")
        return False

if __name__ == "__main__":
    fetch_rentals_ca_automated()
