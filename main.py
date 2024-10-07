from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
import time

# Load environment variables (for email and password)
load_dotenv()

# Set up Chrome WebDriver
current_directory = os.getcwd()
chromedriver_path = os.path.join(current_directory, "chromedriver")
service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service)

driver.get("https://ask2lit.lassonde.yorku.ca/app/itdesk/ui/requests")

# Change to 20 seconds
time.sleep(20)

email = os.getenv("LOGIN_EMAIL")
password = os.getenv("LOGIN_PASSWORD")

email_input = driver.find_element(By.ID, "login_id")
email_input.send_keys(email)

button = driver.find_element(By.ID, "nextbtn")
button.click()

# Change to 20 seconds
time.sleep(20)
password_field = driver.find_element(By.ID, "password")
password_field.send_keys(password)
button = driver.find_element(By.ID, "nextbtn")
button.click()

# Change to 20 seconds
time.sleep(20)

# Ensure table rows are visible, with 20-second wait
try:
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//tr[contains(@class, 'sdpTable requestlistview_row')]"))
    )
    print("Table rows are now visible, proceeding to read the data.")
except Exception as e:
    print(f"Error: The table rows did not load in time. {e}")
    driver.quit()
    exit()

ticket_rows = driver.find_elements(By.XPATH, "//tr[contains(@class, 'sdpTable requestlistview_row')]")

if len(ticket_rows) > 0:
    print(f"Found {len(ticket_rows)} rows.")
    
    for row in ticket_rows:
        try:
            reply_icon = row.find_elements(By.XPATH, ".//div[contains(@class, 'listicon replyicon_REQ_REPLY')]")
            resolved_or_closed = row.find_elements(By.XPATH, ".//td[contains(@class, 'evenRow')]//span[text()='Resolved' or text()='Closed']")

            if reply_icon and not resolved_or_closed:
                ticket_number = row.find_element(By.XPATH, ".//span[@class='listview-display-id']").text
                subject = row.find_element(By.XPATH, ".//td[contains(@class, 'wo-subject')]").text
                technician_or_status = row.find_element(By.XPATH, ".//td[@title]").text
                
                print(f"Ticket Number: {ticket_number}, Subject: {subject}, Technician/Status: {technician_or_status}")
                
        except Exception as e:
            print(f"Error processing row: {e}")
else:
    print("No rows found.")

# Get ticket number input
ticket_to_ans = input("\nEnter the ticket number you would like the AI to reply to: ").strip()

while not ticket_to_ans:
    print("Error: Ticket number cannot be empty. Please try again.")
    ticket_to_ans = input("\nEnter the ticket number you would like the AI to reply to: ").strip()

try:
    # Click on the specified ticket
    ticket_link = driver.find_element(By.XPATH, f"//span[@class='listview-display-id' and text()='{ticket_to_ans}']")
    ticket_link.click()
    
    print(f"Successfully clicked on ticket {ticket_to_ans}.")
    
    # Change to 20 seconds
    time.sleep(20)

    # Dynamically locate all the shadow DOM hosts
    shadow_hosts = driver.find_elements(By.XPATH, ".//div[starts-with(@id, 'notiDesc_')]")
    
    if shadow_hosts:
        print(f"Found {len(shadow_hosts)} shadow DOM host(s).")

        for idx, shadow_host in enumerate(shadow_hosts):
            print(f"Processing shadow DOM host {idx + 1}...")
            
            # Access each shadow root
            shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)

            if shadow_root:
                print(f"Successfully accessed shadow root {idx + 1}.")
                
                # Scrape all div, span, and p elements inside the shadow DOM
                elements = shadow_root.find_elements(By.CSS_SELECTOR, "div, span, p")
                
                if elements:
                    print(f"Found {len(elements)} elements in shadow DOM host {idx + 1}.")
                    for element in elements:
                        text = element.text.strip()
                        if text:
                            print(text)
                else:
                    print(f"No elements found in shadow DOM host {idx + 1}.")
            else:
                print(f"Failed to access shadow root {idx + 1}.")
    else:
        print("No shadow DOM hosts found.")
    
except Exception as e:
    print(f"Error: Could not navigate to ticket {ticket_to_ans} or scrape the data. {e}")

# Change to 20 seconds
time.sleep(20)
driver.quit()
