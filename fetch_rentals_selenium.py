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
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # Use a real user agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        
        url = "https://rentals.ca/vancouver"
        print(f"Navigating to {url}...")
        driver.get(url)
        
        started = time.time()
        last_source = ""
        while time.time() - started < 45:
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            last_source = driver.page_source or ""
            if ("rentalListingName" in last_source) or ('"__typename": "RentalListing"' in last_source) or ("RentalListing" in last_source):
                break
        
        source = last_source or driver.page_source or ""

        has_data = ("rentalListingName" in source) or ('"__typename": "RentalListing"' in source)
        if not has_data:
            with open("rentals_raw_failed.html", "w", encoding="utf-8") as f:
                f.write(source)
            print(f"WARNING: Rentals.ca fetched but no listing markers found. Keeping existing rentals_raw.json. chars={len(source)}")
            return True

        with open("rentals_raw.json", "w", encoding="utf-8") as f:
            f.write(source)

        print(f"SUCCESS: Captured {len(source)} characters to rentals_raw.json")
        return True
        
    except Exception as e:
        print(f"FAILED to fetch Rentals.ca: {e}")
        return False
    finally:
        try:
            if driver:
                driver.quit()
        except:
            pass

if __name__ == "__main__":
    ok = fetch_rentals_ca_automated()
    raise SystemExit(0 if ok else 1)
