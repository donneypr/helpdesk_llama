from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os
import time

load_dotenv()

current_directory = os.getcwd()

chromedriver_path = os.path.join(current_directory, "chromedriver")

service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service)

driver.get("https://ask2lit.lassonde.yorku.ca/app/itdesk/ui/requests")

time.sleep(2)

email = os.getenv("LOGIN_EMAIL")
password = os.getenv("LOGIN_PASSWORD")

email_input = driver.find_element(By.ID, "login_id")
email_input.send_keys(email)

button = driver.find_element(By.ID, "nextbtn")
button.click()

time.sleep(2)

password_field = driver.find_element(By.ID, "password")
password_field.send_keys(password)

button = driver.find_element(By.ID, "nextbtn")
button.click()

time.sleep(5)

try:
    WebDriverWait(driver, 10).until(
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
            
            if reply_icon:
                ticket_number = row.find_element(By.XPATH, ".//span[@class='listview-display-id']").text
                subject = row.find_element(By.XPATH, ".//td[contains(@class, 'wo-subject')]").text
                technician_or_status = row.find_element(By.XPATH, ".//td[@title]").text
                
                print(f"Ticket Number: {ticket_number}, Subject: {subject}, Technician/Status: {technician_or_status}")
                
        except Exception as e:
            print(f"Error processing row: {e}")
else:
    print("No rows found.")

ticket_to_ans = input("\nEnter the ticket number you would like the AI to reply to: ")

# Adding a 5-second pause after the user input
time.sleep(5)

try:
    ticket_link = driver.find_element(By.XPATH, f"//span[@class='listview-display-id' and text()='{ticket_to_ans}']")
    ticket_link.click()
    
    print(f"Successfully clicked on ticket {ticket_to_ans}.")

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//div[@class='conversation-info']"))
    )
    print(f"Loaded the conversation for ticket {ticket_to_ans}.")

    conversation_blocks = driver.find_elements(By.XPATH, "//div[@class='conversation-info']")

    if len(conversation_blocks) > 0:
        print(f"Found {len(conversation_blocks)} conversation entries.")
        
        for block in conversation_blocks:
            try:
                paragraphs = block.find_elements(By.XPATH, ".//p")
                full_message = "\n".join([p.text for p in paragraphs])
                
                print(f"Message content:\n{full_message}\n")
            except Exception as e:
                print(f"Error processing conversation entry: {e}")
    else:
        print("No conversations found.")

except Exception as e:
    print(f"Error: Could not navigate to ticket {ticket_to_ans} or scrape the data. {e}")

time.sleep(100)
driver.quit()
