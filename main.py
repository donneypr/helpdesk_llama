from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from transformers import BartForConditionalGeneration, BartTokenizer
from dotenv import load_dotenv
import os
import time
import re
from langchain_ollama import OllamaLLM
from tfidf_similarity import load_ticket_data, vectorize_subjects, find_similar_ticket


model = OllamaLLM(model="llama3")

def load_bart_model():
    model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
    tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
    return model, tokenizer

def summarize_thread(thread_text, model, tokenizer, max_length=130):
    inputs = tokenizer([thread_text], max_length=1024, return_tensors="pt", truncation=True)
    summary_ids = model.generate(inputs["input_ids"], max_length=max_length, min_length=30, length_penalty=2.0, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

# Generate a reply with Ollama
def generate_reply_with_llama(summarized_thread, similar_resolution):
    prompt = (
    f"Donato is an IT Assistant. Below is a summarized email thread and a similar past resolution.\n\n"
    f"Task: Analyze the summarized thread and determine who should be addressed in the response based on the context of the last message, while considering the entire conversation. Make sure the response is directed to the right person who is requesting action, and not to those CC'd or merely mentioned. Sign off with Donato's name.\n\n"
    f"Summarized Email Thread:\n{summarized_thread}\n\n"
    f"Similar Past Resolution: {similar_resolution}, if it applies, use it\n\n"
    "Please generate a concise, professional response, addressing the correct recipient and reflecting the context of the last message."
    )

    result = model.invoke(input=prompt)
    if isinstance(result, dict):
        return result.get("text", "No response generated.")
    else:
        return result

def scrape_subject():
    try:
        subject = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='details_inner_title']/div[3]/h1"))
        ).text
        print(f"Scraped Subject: {subject}")
        return subject
    except Exception as e:
        print(f"Error scraping subject: {e}")
        return None

load_dotenv()

current_directory = os.getcwd()
chromedriver_path = os.path.join(current_directory, "chromedriver")
service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service)

driver.get("https://ask2lit.lassonde.yorku.ca/app/itdesk/ui/requests")

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

def clean_text_for_ai(text):
    redundant_texts = [
    "We recognize that many Indigenous Nations have longstanding relationships with the territories",
    "Acknowledges its presence on the traditional territory of many Indigenous Nations",
    "This electronic mail (e-mail), including any attachments, is intended only for the recipient(s)",
    "Any unauthorized use, dissemination or copying is strictly prohibited",
    "If you have received this e-mail in error, or are not named as a recipient",
    "Kind regards,", "Best regards,", "Warm regards,", "Sincerely,",
    "School of Engineering", "Helpdesk Coordinator", "Cross-Campus Capstone Classroom",
    "VACATION NOTICE", "zoom.us", "email@domain.com", "website.domain", "UNIVERSITY", 
    "4700 Keele Street Toronto ON, Canada M3J 1P3", "The area known as Tkaronto has been care taken by the",
    "Mississaugas of the Credit First Nation", "Dish with One Spoon Wampum Belt Covenant", "privileged, confidential and/or exempt from disclosure"
]
    for redundant_text in redundant_texts:
        text = text.replace(redundant_text, "")
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"\s{2,}", " ", text)
    seen_lines = set()
    cleaned_lines = []
    for line in text.splitlines():
        line_lower = line.strip().lower()
        if line_lower and line_lower not in seen_lines:
            seen_lines.add(line_lower)
            cleaned_lines.append(line.strip())
    cleaned_text = "\n".join(cleaned_lines)
    cleaned_text = re.sub(r"(Hello,)+", "Danielle,", cleaned_text)
    cleaned_text = re.sub(r"(Thank you,)+", "Thank you,", cleaned_text)
    return cleaned_text.strip()

def open_closed_elements():
    conversation_heads = driver.find_elements(By.XPATH, "//div[contains(@class, 'conversation-head')]")
    if len(conversation_heads) > 1:
        for idx, conv_head in enumerate(conversation_heads[1:], start=2):
            try:
                print(f"Clicking conversation thread {idx}...")
                conv_head.click()
                time.sleep(2)
            except Exception as e:
                print(f"Error opening conversation thread {idx}: {e}")
    notes = driver.find_elements(By.XPATH, "//div[starts-with(@id, 'notiDesc_') or starts-with(@id, 'note_')]")
    for idx, note in enumerate(notes):
        try:
            if "display: none;" in note.get_attribute("style"):
                conversation_head = note.find_element(By.XPATH, ".//preceding-sibling::div[contains(@class, 'conversation-head')]")
                conversation_head.click()
                time.sleep(2)
        except Exception as e:
            print(f"Error opening note {idx + 1}: {e}")

ticket_to_ans = input("\nEnter the ticket number you would like the AI to reply to: ").strip()

while not ticket_to_ans:
    print("Error: Ticket number cannot be empty. Please try again.")
    ticket_to_ans = input("\nEnter the ticket number you would like the AI to reply to: ").strip()

try:
    ticket_link = driver.find_element(By.XPATH, f"//span[@class='listview-display-id' and text()='{ticket_to_ans}']")
    ticket_link.click()
    print(f"Successfully clicked on ticket {ticket_to_ans}.")
    time.sleep(10)
    
    # Scrape the subject after clicking the ticket
    subject = scrape_subject()
    
    open_closed_elements()
    elements_to_scrape = driver.find_elements(By.XPATH, "//div[starts-with(@id, 'notiDesc_') or starts-with(@id, 'note_')]")

    if elements_to_scrape:
        print(f"Found {len(elements_to_scrape)} elements (notiDesc or notes).")
        email_thread = ""
        unique_texts = set()
        for idx, element in enumerate(elements_to_scrape):
            print(f"Processing element {idx + 1}...")
            is_note = "note_" in element.get_attribute("id")
            if is_note:
                print("\n--- Note ---\n")
            try:
                shadow_root = driver.execute_script("return arguments[0].shadowRoot", element)
                if shadow_root:
                    print(f"Successfully accessed shadow root for element {idx + 1}.")
                    shadow_elements = shadow_root.find_elements(By.CSS_SELECTOR, "div, span, p")
                    if shadow_elements:
                        print(f"Found {len(shadow_elements)} shadow elements.")
                        for shadow_element in shadow_elements:
                            text = shadow_element.text.strip()
                            if text and text not in unique_texts:
                                unique_texts.add(text)
                                email_thread += f"{text}\n"
                else:
                    note_text = element.text.strip()
                    if note_text and note_text not in unique_texts:
                        unique_texts.add(note_text)
                        email_thread += f"{note_text}\n"
            except Exception as e:
                print(f"Error processing element {idx + 1}: {e}")
        
        cleaned_thread = clean_text_for_ai(email_thread)
        print(f"\nCleaned Thread for AI:\n{cleaned_thread}")
        
        bart_model, bart_tokenizer = load_bart_model()
        summarized_thread = summarize_thread(cleaned_thread, bart_model, bart_tokenizer)
        print(f"\nSummarized Email Thread:\n{summarized_thread}")
        
        df = load_ticket_data('resolved_tickets.csv')
        tfidf_matrix, vectorizer = vectorize_subjects(df)
        _, similar_resolution = find_similar_ticket(subject, tfidf_matrix, df, vectorizer)
        
        ai_reply = generate_reply_with_llama(summarized_thread, similar_resolution)
        formatted_reply = f"{ai_reply}\n,\n"
        
        # Print AI response and subject
        print(f"\nAI Response:\n{formatted_reply}")
        print(f"\nTicket Subject: {subject}")
    else:
        print("No notiDesc or note elements found.")
    
except Exception as e:
    print(f"Error: Could not navigate to ticket {ticket_to_ans} or scrape the data. {e}")

##click the reply all button
reply_all_button = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'new-inc-btn') and .//span[text()='Reply All']]"))
)

driver.execute_script("arguments[0].scrollIntoView(true);", reply_all_button)

time.sleep(1)

driver.execute_script("arguments[0].click();", reply_all_button)
time.sleep(100)
driver.quit()