import os
import json
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ======================
# CONFIG
# ======================
EMAIL = os.environ["TRAINERIZE_EMAIL"]
PASSWORD = os.environ["TRAINERIZE_PASSWORD"]
OUTPUT_PATH = "data/classes.json"


# ======================
# SETUP SELENIUM
# ======================
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(), options=options)
wait = WebDriverWait(driver, 20)


# ======================
# LOGIN
# ======================
driver.get("https://vimandvigor.trainerize.com/app/client/17606051/classFinder")

email_input = wait.until(EC.presence_of_element_located((By.ID, "emailInput")))
email_input.send_keys(EMAIL)

password_input = wait.until(EC.presence_of_element_located((By.ID, "passInput")))
password_input.send_keys(PASSWORD)

sign_in_button = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='signIn-button']"))
)
sign_in_button.click()


# ======================
# GO TO CLASS FINDER
# ======================
find_class_btn = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-testid='find-class']"))
)
find_class_btn.click()


# ======================
# LOAD GRID
# ======================
class_grid = wait.until(EC.presence_of_element_located((By.ID, "classFinderGrid")))
time.sleep(2)


# ======================
# SCROLL TO LOAD ALL DAYS
# ======================
last_height = 0
for _ in range(10):
    driver.execute_script(
        "arguments[0].scrollTop = arguments[0].scrollHeight", class_grid
    )
    time.sleep(1)

    new_height = driver.execute_script(
        "return arguments[0].scrollHeight", class_grid
    )
    if new_height == last_height:
        break
    last_height = new_height


# ======================
# SCRAPE
# ======================
rows = []

day_headers = class_grid.find_elements(By.TAG_NAME, "h3")

for header in day_headers:
    day_label = header.text.strip()

    container = header.find_element(By.XPATH, "following-sibling::div[1]")

    if "nullContainer" in container.get_attribute("class"):
        continue

    try:
        table = container.find_element(By.TAG_NAME, "table")
        trs = table.find_elements(By.TAG_NAME, "tr")

        for tr in trs:
            tds = tr.find_elements(By.TAG_NAME, "td")
            if not tds:
                continue

            rows.append({
                "day": day_label,
                "class_name": tds[0].text.strip(),
                "time": tds[1].text.strip() if len(tds) > 1 else None,
                "trainer": tds[2].text.strip() if len(tds) > 2 else None,
                "location": tds[3].text.strip() if len(tds) > 3 else None,
            })

    except Exception:
        continue


driver.quit()


# ======================
# SAVE JSON
# ======================
os.makedirs("data", exist_ok=True)

with open(OUTPUT_PATH, "w") as f:
    json.dump(rows, f, indent=2)

print(f"Saved {len(rows)} classes to {OUTPUT_PATH}")
