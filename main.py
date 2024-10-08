from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
import time
import re

# Load environment variables (for email and password)
load_dotenv()

# Set up Chrome WebDriver
current_directory = os.getcwd()
chromedriver_path = os.path.join(current_directory, "chromedriver")
service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service)

driver.get("https://ask2lit.lassonde.yorku.ca/app/itdesk/ui/requests")

# Shorter wait times for testing
time.sleep(10)

email = os.getenv("LOGIN_EMAIL")
password = os.getenv("LOGIN_PASSWORD")

email_input = driver.find_element(By.ID, "login_id")
email_input.send_keys(email)

button = driver.find_element(By.ID, "nextbtn")
button.click()

time.sleep(10)
password_field = driver.find_element(By.ID, "password")
password_field.send_keys(password)
button = driver.find_element(By.ID, "nextbtn")
button.click()

time.sleep(10)

# Ensure table rows are visible
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

# Define redundant texts and patterns to remove (without specific names)
redundant_texts = [
    "We recognize that many Indigenous Nations have longstanding relationships with the territories",
    "This electronic mail (e-mail), including any attachments, is intended only for the recipient",
    "York University acknowledges its presence on the traditional territory of many Indigenous Nations",
    "If you have received this e-mail in error, or are not named as a recipient, please immediately notify the sender",
    "The area known as Tkaronto has been care taken by the Anishinabek Nation",
    "This territory is subject of the Dish with One Spoon Wampum Belt Covenant",
    "Any unauthorized use, dissemination or copying is strictly prohibited",
    "(s) to whom it is addressed and may contain information that is privileged",
    "Best regards,", "Thank you,", "Kind regards,", "Warm regards,",
    "Lassonde School of Engineering", "Lassonde Information Technology", 
    "Helpdesk Coordinator", "Cross-Campus Capstone Classroom",
    "Please don’t feel obligated to reply outside your normal schedule."
]

# Optionally, define regular expressions to match broader patterns
redundant_patterns = [
    r"York University acknowledges.*?Wampum Belt Covenant.*",  # Matches land acknowledgment
    r"This e-mail, including any attachments.*?",  # Matches disclaimers about the email being privileged
]

# Function to clean the text
def clean_text(text):
    # Remove redundant specific texts
    for redundant_text in redundant_texts:
        text = text.replace(redundant_text, "")
    
    # Use regular expressions to match and remove broader patterns
    for pattern in redundant_patterns:
        text = re.sub(pattern, "", text, flags=re.DOTALL)

    # Remove excess spaces and newlines
    text = " ".join(text.split())
    return text

# Ensure all conversation threads and notes are opened before scraping
def open_closed_elements():
    # Get all conversation heads (excluding the first one as it's already open)
    conversation_heads = driver.find_elements(By.XPATH, "//div[contains(@class, 'conversation-head')]")

    if len(conversation_heads) > 1:
        # Start from the second element as the first is already open
        for idx, conv_head in enumerate(conversation_heads[1:], start=2):
            try:
                print(f"Clicking conversation thread {idx}...")
                conv_head.click()
                time.sleep(2)  # Give time for content to load
            except Exception as e:
                print(f"Error opening conversation thread {idx}: {e}")
    else:
        print("No additional conversation threads to click.")

    # Open any closed notes
    notes = driver.find_elements(By.XPATH, "//div[starts-with(@id, 'notiDesc_') or starts-with(@id, 'note_')]")
    for idx, note in enumerate(notes):
        try:
            # Check if the note is closed (by checking if the style contains 'display: none')
            if "display: none;" in note.get_attribute("style"):
                conversation_head = note.find_element(By.XPATH, ".//preceding-sibling::div[contains(@class, 'conversation-head')]")
                conversation_head.click()  # Click to open the note
                time.sleep(2)  # Allow time for content to load
        except Exception as e:
            print(f"Error opening note {idx + 1}: {e}")

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
    
    time.sleep(10)

    # Open all conversation threads and notes before scraping (starting from the second thread)
    open_closed_elements()

    # Scrape both notiDesc and notes elements together in the order they appear on the page
    elements_to_scrape = driver.find_elements(By.XPATH, "//div[starts-with(@id, 'notiDesc_') or starts-with(@id, 'note_')]")

    if elements_to_scrape:
        print(f"Found {len(elements_to_scrape)} elements (notiDesc or notes).")

        for idx, element in enumerate(elements_to_scrape):
            print(f"Processing element {idx + 1}...")
            
            # Check if the element is a shadow DOM host (notiDesc)
            try:
                shadow_root = driver.execute_script("return arguments[0].shadowRoot", element)

                if shadow_root:
                    print(f"Successfully accessed shadow root for element {idx + 1}.")
                    
                    # Scrape all div, span, and p elements inside the shadow DOM
                    shadow_elements = shadow_root.find_elements(By.CSS_SELECTOR, "div, span, p")
                    
                    if shadow_elements:
                        print(f"Found {len(shadow_elements)} shadow elements.")
                        for shadow_element in shadow_elements:
                            text = clean_text(shadow_element.text.strip())
                            if text:
                                print(f"Shadow Element Text: {text}")
                else:
                    # If it's a regular note element (non-shadow)
                    note_text = clean_text(element.text.strip())
                    if note_text:
                        print(f"Note: {note_text}")
            except Exception as e:
                print(f"Error processing element {idx + 1}: {e}")
    else:
        print("No notiDesc or note elements found.")
    
except Exception as e:
    print(f"Error: Could not navigate to ticket {ticket_to_ans} or scrape the data. {e}")

time.sleep(100)
driver.quit()
