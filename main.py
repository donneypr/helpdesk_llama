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

# Open the target page
driver.get("https://ask2lit.lassonde.yorku.ca/app/itdesk/ui/requests")

# Allow the page to load
time.sleep(2)

# Login process
email = os.getenv("LOGIN_EMAIL")
password = os.getenv("LOGIN_PASSWORD")

email_input = driver.find_element(By.ID, "login_id")
email_input.send_keys(email)

# Click "Next" button
button = driver.find_element(By.ID, "nextbtn")
button.click()

# Wait and enter password
time.sleep(2)
password_field = driver.find_element(By.ID, "password")
password_field.send_keys(password)
button = driver.find_element(By.ID, "nextbtn")
button.click()

# Wait for the page to load after login
time.sleep(5)

# Wait for the table rows to be visible
try:
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//tr[contains(@class, 'sdpTable requestlistview_row')]"))
    )
    print("Table rows are now visible, proceeding to read the data.")
except Exception as e:
    print(f"Error: The table rows did not load in time. {e}")
    driver.quit()
    exit()

# Get ticket rows
ticket_rows = driver.find_elements(By.XPATH, "//tr[contains(@class, 'sdpTable requestlistview_row')]")

if len(ticket_rows) > 0:
    print(f"Found {len(ticket_rows)} rows.")
    
    for row in ticket_rows:
        try:
            reply_icon = row.find_elements(By.XPATH, ".//div[contains(@class, 'listicon replyicon_REQ_REPLY')]")
            
            if reply_icon:
                ticket_number = row.find_element(By.XPATH, ".//span[@class='listview-display-id']").text
                subject = row.find_element(By.XPATH, ".//td[contains(@class, 'wo-subject')]").text
                technician_or_status = row.find_element(By.XPATH, ".//td[@title]").text
                
                print(f"Ticket Number: {ticket_number}, Subject: {subject}, Technician/Status: {technician_or_status}")
                
        except Exception as e:
            print(f"Error processing row: {e}")
else:
    print("No rows found.")

# Get ticket number input, and ensure a valid input is provided
ticket_to_ans = input("\nEnter the ticket number you would like the AI to reply to: ").strip()

# Ensure the input is not empty
while not ticket_to_ans:
    print("Error: Ticket number cannot be empty. Please try again.")
    ticket_to_ans = input("\nEnter the ticket number you would like the AI to reply to: ").strip()

try:
    # Click on the specified ticket
    ticket_link = driver.find_element(By.XPATH, f"//span[@class='listview-display-id' and text()='{ticket_to_ans}']")
    ticket_link.click()
    
    print(f"Successfully clicked on ticket {ticket_to_ans}.")
    time.sleep(5)

    # Debug: Check if the page changed after the click
    print("Waiting for shadow DOM content...")

    # Try to find the shadow DOM host
    try:
        shadow_host = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "notiDesc_71651000024499425"))  # Ensure this ID is correct
        )
        print("Found shadow DOM host.")
    except Exception as e:
        print(f"Error: Could not find the shadow DOM host: {e}")
        driver.quit()
        exit()

    # Use JavaScript to access the shadow root
    try:
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
        print("Successfully accessed shadow root.")
    except Exception as e:
        print(f"Error: Could not access shadow root: {e}")
        driver.quit()
        exit()

    # Scrape paragraphs with class 'MsoNormal' inside the shadow DOM
    try:
        paragraphs = shadow_root.find_elements(By.CSS_SELECTOR, "p.MsoNormal")
        
        # Print the text content of each paragraph
        if paragraphs:
            print(f"Found {len(paragraphs)} paragraphs.")
            for p in paragraphs:
                print(p.text)
        else:
            print("No paragraphs found inside the shadow DOM.")
    except Exception as e:
        print(f"Error while extracting paragraphs from shadow DOM: {e}")
    
except Exception as e:
    print(f"Error: Could not navigate to ticket {ticket_to_ans} or scrape the data. {e}")

# Wait for a while before quitting (for debugging purposes)
time.sleep(100)
driver.quit()
