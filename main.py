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

# ollama imports
from langchain_ollama import OllamaLLM

# Initialize LLaMA3 model
model = OllamaLLM(model="llama3")

# Function to send the cleaned thread to the LLaMA3 model and get a response
def generate_reply_with_llama(cleaned_thread):
    prompt = (
        f"Donato is an IT Assistant, respond to the following ticket request:\n\n"
        f"Ticket Details:\n{cleaned_thread}\n\n"
        "Please provide a helpful, professional response that is concise."
    )
    
    # Send the prompt to the model
    result = model.invoke(input=prompt)
    
    # Ensure result is a dictionary; return text or fallback
    if isinstance(result, dict):
        return result.get("text", "No response generated.")
    else:
        return result  # In case the result is a plain string

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

# Retrieving email and password from .env file
email = os.getenv("LOGIN_EMAIL")
password = os.getenv("LOGIN_PASSWORD")

# Logging in
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

# Scraping ticket rows
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

# Function to clean up and format the scraped email thread
def clean_text_for_ai(text):
    # Redundant patterns to remove (such as disclaimers, land acknowledgments, and signatures)
    redundant_texts = [
        "We recognize that many Indigenous Nations have longstanding relationships with the territories",
        "York University acknowledges its presence on the traditional territory of many Indigenous Nations",
        "This electronic mail (e-mail), including any attachments, is intended only for the recipient(s)",
        "Any unauthorized use, dissemination or copying is strictly prohibited",
        "If you have received this e-mail in error, or are not named as a recipient",
        "Kind regards,", "Best regards,", "Warm regards,", "Sincerely,",
        "Lassonde School of Engineering", "Helpdesk Coordinator", "Cross-Campus Capstone Classroom",
        "VACATION NOTICE", "Z yorku.zoom.us", "T 416-736-5588", 
        "Sandyjk@yorku.ca", "lassonde.yorku.ca", "YORK UNIVERSITY", 
        "4700 Keele Street Toronto ON, Canada M3J 1P3", "The area known as Tkaronto has been care taken by the",
        "Mississaugas of the Credit First Nation", "Dish with One Spoon Wampum Belt Covenant", "privileged, confidential and/or exempt from disclosure"
    ]

    # Remove redundant specific texts
    for redundant_text in redundant_texts:
        text = text.replace(redundant_text, "")

    # Remove multiple newlines and extra whitespace
    text = re.sub(r"\n+", "\n", text)  # Condense multiple newlines into one
    text = re.sub(r"\s{2,}", " ", text)  # Condense multiple spaces into one

    # Track unique lines using a set (case-insensitive)
    seen_lines = set()
    cleaned_lines = []

    # Process line by line, removing duplicates
    for line in text.splitlines():
        line_lower = line.strip().lower()
        if line_lower and line_lower not in seen_lines:
            seen_lines.add(line_lower)
            cleaned_lines.append(line.strip())

    # Join the cleaned lines back into a full string
    cleaned_text = "\n".join(cleaned_lines)

    # Remove redundant headers like "Hello Danielle" and repeated "Thank you"
    cleaned_text = re.sub(r"(Hello Danielle,)+", "Hello Danielle,", cleaned_text)
    cleaned_text = re.sub(r"(Thank you,)+", "Thank you,", cleaned_text)
    
    # Final cleanup - trim excess whitespace and redundant phrases
    return cleaned_text.strip()

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

        email_thread = ""
        unique_texts = set()  # Set to store unique elements

        for idx, element in enumerate(elements_to_scrape):
            print(f"Processing element {idx + 1}...")

            is_note = "note_" in element.get_attribute("id")

            if is_note:
                print("\n--- Note ---\n")  # Print if it's a note

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
                            text = shadow_element.text.strip()
                            if text and text not in unique_texts:  # Check for uniqueness
                                unique_texts.add(text)
                                email_thread += f"{text}\n"
                else:
                    # If it's a regular note element (non-shadow)
                    note_text = element.text.strip()
                    if note_text and note_text not in unique_texts:
                        unique_texts.add(note_text)
                        email_thread += f"{note_text}\n"
            except Exception as e:
                print(f"Error processing element {idx + 1}: {e}")
        
        # Clean the scraped email thread text for AI
        cleaned_thread = clean_text_for_ai(email_thread)
        print(f"\nCleaned Thread for AI:\n{cleaned_thread}")

        # Generate AI response with the LLaMA model
        ai_reply = generate_reply_with_llama(cleaned_thread)
        
        # Format the AI response as an email with "Regards"
        formatted_reply = f"{ai_reply}\n\nRegards,\n"
        print(f"\nAI Response:\n{formatted_reply}")

    else:
        print("No notiDesc or note elements found.")
    
except Exception as e:
    print(f"Error: Could not navigate to ticket {ticket_to_ans} or scrape the data. {e}")

time.sleep(100)
driver.quit()
