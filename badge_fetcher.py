from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json

def parse_credly_badge(url):
    """
    Parse Credly badge details from the given URL in headless mode
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(options=options)  # or webdriver.Firefox() for Firefox
    
    try:
        # Navigate to the URL
        print(f"Loading badge page: {url}")
        driver.get(url)
        
        # Wait for page to load (adjust timeout as needed)
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.cr-badges-full-badge__head-group"))
        )
        
        badge_details = {}
        
        # Extract badge name
        try:
            badge_name = driver.find_element(By.CSS_SELECTOR, "div.cr-badges-full-badge__head-group").text
            badge_details['badge_name'] = badge_name
        except NoSuchElementException:
            badge_details['badge_name'] = "N/A"
                
        # Extract cert holder name
        # Present inside a <p> tag with class 'badge-banner-issued-to-text__name-and-celebrator-list'
        try:
            cert_holder = driver.find_element(By.CSS_SELECTOR, "p.badge-banner-issued-to-text__name-and-celebrator-list").text
            badge_details['certificate_holder'] = cert_holder
        except NoSuchElementException:
            badge_details['certificate_holder'] = "N/A"

        # Extract issue date and expiration date
        try:
            detail_items = driver.find_elements(By.CSS_SELECTOR, "span.cr-badge-banner-expires-at-text")

            # Navigate to one sibling previous to detail_items to get issue date which is in a p tag
            # Get the parent <p> element
            p_element = detail_items[0].find_element(By.XPATH, "./ancestor::p")

            # Get all text from the parent <p> and extract the issue date
            full_text = p_element

            # remove newline characters
            full_text = full_text.text.replace("\n", " ")

            badge_details['dates'] = full_text
        except NoSuchElementException:
            badge_details['dates'] = "N/A"

        return badge_details    
    except TimeoutException:
        print("Timeout: Page took too long to load")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://www.credly.com/badges/90ee2ee9-f6cf-4d9b-8a52-f631d8644d58/public_url"
    
    badge_info = parse_credly_badge(url)
    
    if badge_info:
        print("\n=== Badge Details ===")
        for key, value in badge_info.items():
            if key != 'full_page_text':
                print(f"{key}: {value}")
        
        # Save to JSON file
        with open('badge_details.json', 'w') as f:
            # Remove full_page_text before saving to JSON
            details_to_save = {k: v for k, v in badge_info.items() if k != 'full_page_text'}
            json.dump(details_to_save, f, indent=2)
        print("\nDetails saved to badge_details.json")
    else:
        print("Failed to parse badge details")