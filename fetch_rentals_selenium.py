import os
import json
import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def fetch_rentals_ca_automated():
    print("Starting automated Rentals.ca fetch via Selenium...")
    
    def has_listing_markers(html):
        s = html or ""
        return (
            ("rentalListingName" in s) or
            ('"__typename": "RentalListing"' in s) or
            ('"__typename":"RentalListing"' in s) or
            ("rentalListingLocation" in s) or
            ("bedsRange" in s) or
            ("rentRange" in s) or
            ("response:" in s)
        )

    def save_debug(city, html):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = re.sub(r"[^a-z0-9_-]+", "_", str(city).lower()).strip("_") or "city"
        html_path = f"rentals_raw_failed_{safe}_{ts}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html or "")
        return html_path

    def try_accept_cookies():
        try:
            btn_xpaths = [
                "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
                "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
                "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow')]",
                "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]",
            ]
            for xp in btn_xpaths:
                els = driver.find_elements(By.XPATH, xp)
                for el in els[:6]:
                    try:
                        if el.is_displayed() and el.is_enabled():
                            try:
                                el.click()
                            except:
                                driver.execute_script("arguments[0].click();", el)
                            time.sleep(0.8)
                            return True
                    except:
                        continue
        except:
            return False
        return False

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
        
        cities_env = (os.getenv("HAVENNEST_RENTALS_CITIES") or "").strip()
        if cities_env:
            cities = [c.strip().strip("/") for c in cities_env.split(",") if c.strip()]
        else:
            cities = [
                "vancouver",
                "richmond",
                "surrey",
                "burnaby",
                "langley",
                "delta",
                "abbotsford",
                "port-coquitlam",
                "coquitlam",
            ]

        try:
            wait_s = int((os.getenv("HAVENNEST_RENTALS_WAIT_SECONDS") or "").strip() or "90")
        except:
            wait_s = 90
        try:
            retries = int((os.getenv("HAVENNEST_RENTALS_MAX_RETRIES") or "").strip() or "2")
        except:
            retries = 2

        combined = []
        for city in cities:
            url = f"https://rentals.ca/{city}"
            print(f"Navigating to {url}...")
            last_source = ""
            ok = False
            for attempt in range(max(retries, 1)):
                try:
                    if attempt == 0:
                        driver.get(url)
                    else:
                        driver.refresh()
                    started = time.time()
                    while time.time() - started < wait_s:
                        time.sleep(1.5)
                        try_accept_cookies()
                        try:
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.25);")
                            time.sleep(0.6)
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.6);")
                            time.sleep(0.6)
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(0.6)
                            driver.execute_script("window.scrollBy(0, -600);")
                            time.sleep(0.3)
                        except:
                            pass
                        last_source = driver.page_source or ""
                        if has_listing_markers(last_source):
                            ok = True
                            break
                except WebDriverException:
                    last_source = driver.page_source or ""
                if ok:
                    break

            source_part = last_source or driver.page_source or ""
            if not has_listing_markers(source_part):
                html_path = save_debug(city, source_part)
                print(f"WARNING: Rentals.ca fetched but no listing markers found for {city}. chars={len(source_part)} saved={html_path}")
                continue
            combined.append(f"\n\nHAVENNEST_RENTALS_CITY={city}\n")
            combined.append(source_part)

        source = "".join(combined)

        if not has_listing_markers(source):
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
