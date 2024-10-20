import os
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from transformers import BartForConditionalGeneration, BartTokenizer
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from tfidf_similarity import load_ticket_data, vectorize_subjects, find_similar_ticket, compare_ai_response_to_resolution
from selenium.webdriver.common.keys import Keys


#ansi colours declarations
GREEN = "\033[92m"
RESET = "\033[0m"  
YELLOW = "\033[33m"
BRIGHTMAGENTA = "\033[95m"
RED = "\033[91m"



model = OllamaLLM(model="llama3.2")

def load_bart_model():
    model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
    tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
    return model, tokenizer

def summarize_thread(thread_text, model, tokenizer, max_length=130):
    inputs = tokenizer([thread_text], max_length=1024, return_tensors="pt", truncation=True)
    summary_ids = model.generate(inputs["input_ids"], max_length=max_length, min_length=30, length_penalty=2.0, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def type_like_human(driver, element, text, delay=0.01):
    for char in text:
        element.send_keys(char)
        time.sleep(delay)

def generate_reply_with_llama(summarized_thread, similar_resolution):
    prompt = (
        f"You are an IT Assistant. Based on the summarized email thread below, provide a solution to their email response. "
        f"Do not include greetings, sign-offs, analysis, or explanations. "
        f"Respond directly with the solution addressing the issue.\n\n"
        f"Summarized Email Thread:\n{summarized_thread}\n\n"
        f"Similar Past Resolution (if applicable): {similar_resolution}\n"
    )
    result = model.invoke(input=prompt)
    if isinstance(result, dict):
        return result.get("text", "No response generated.")
    else:
        return result

def generate_reply_with_custom_input(user_input, similar_resolution):
    prompt = (
        f"You are an IT Assistant. The user provided the following input: '{user_input}'. "
        f"Please complete the response professionally. Do not include greetings, sign-offs, or explanations. "
        f"Generate a solution to the issue based on the input.\n\n"
        f"Mention things from the email thread to make it related to the topic of conversation: {summarized_thread}\n"
    )
    result = model.invoke(input=prompt)
    if isinstance(result, dict):
        return result.get("text", "No response generated.")
    else:
        return result

def scrape_subject(driver):
    try:
        subject = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='details_inner_title']/div[3]/h1"))
        ).text
        print(f"Scraped Subject: {subject}")
        return subject
    except Exception as e:
        print(f"Error scraping subject: {e}")
        return None

def type_reply_in_iframe(driver, ai_reply):
    try:
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.ze_area"))
        )
        print("Switching to the iframe with class 'ze_area'.")
        driver.switch_to.frame(iframe)

        reply_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[3]"))
        )
        print("Located the div element '/html/body/div[3]' inside the iframe.")

        reply_box.send_keys(Keys.END)
        reply_box.send_keys(Keys.ENTER)
        reply_box.send_keys(Keys.ENTER)
        type_like_human(driver, reply_box, ai_reply)
        print("Successfully input the reply after two line breaks.")

        driver.switch_to.default_content()

    except Exception as e:
        print(f"Could not interact with the div inside the iframe. Error: {e}")
        driver.switch_to.default_content()

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

def open_closed_elements(driver):
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

def click_reply_or_reply_all(driver):
    try:
        reply_all_button = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'new-inc-btn') and .//span[text()='Reply All']]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", reply_all_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", reply_all_button)
        print("Clicked 'Reply All' button.")
    except Exception as e:
        print("Reply All button not found, trying Reply...")

        try:
            reply_button = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'new-inc-btn') and .//span[text()='Reply']]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", reply_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", reply_button)
            print("Clicked 'Reply' button.")
        except Exception as e:
            print(f"Neither 'Reply' nor 'Reply All' button could be found: {e}")

load_dotenv()

current_directory = os.getcwd()
chromedriver_path = os.path.join(current_directory, "chromedriver")
service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service)

driver.get("https://ask2lit.lassonde.yorku.ca/app/itdesk/ui/requests")
time.sleep(5)

email = os.getenv("LOGIN_EMAIL")
password = os.getenv("LOGIN_PASSWORD")

email_input = driver.find_element(By.ID, "login_id")
email_input.send_keys(email)

button = driver.find_element(By.ID, "nextbtn")
button.click()

time.sleep(5)
password_field = driver.find_element(By.ID, "password")
password_field.send_keys(password)
button = driver.find_element(By.ID, "nextbtn")
button.click()

time.sleep(5)

def scrape_tickets(driver):
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.XPATH, "//tr[contains(@class, 'sdpTable requestlistview_row')]"))
    )
    print("Table rows are now visible, proceeding to read the data.")
    ticket_rows = driver.find_elements(By.XPATH, "//tr[contains(@class, 'sdpTable requestlistview_row')]")
    return ticket_rows

while True:
    try:
        ticket_rows = scrape_tickets(driver)
    except Exception as e:
        print(f"Error: The table rows did not load in time. {e}")
        driver.quit()
        exit()

    if len(ticket_rows) > 0:
        for row in ticket_rows:
            try:
                reply_icon = row.find_elements(By.XPATH, ".//div[contains(@class, 'listicon replyicon_REQ_REPLY')]")
                resolved_or_closed = row.find_elements(By.XPATH, ".//td[contains(@class, 'evenRow')]//span[text()='Resolved' or text()='Closed']")
                reply_icon_null = row.find_elements(By.XPATH, ".//div[@class='listicon replyicon_null']")

                if (reply_icon or reply_icon_null) and not resolved_or_closed:
                    ticket_number = row.find_element(By.XPATH, ".//span[@class='listview-display-id']").text
                    subject = row.find_element(By.XPATH, ".//td[contains(@class, 'wo-subject')]").text
                    technician_or_status = row.find_element(By.XPATH, ".//td[@title]").text
                    
                    print(f"Ticket Number: {ticket_number}, Subject: {subject}, Technician/Status: {technician_or_status}")
                    
            except Exception as e:
                print(f"Error processing row: {e}")
    else:
        print("No rows found.")

    ticket_to_ans = input(f"\n{YELLOW}Enter the ticket number you would like the AI to reply to or type 'exit' to quit: {RESET}").strip()

    if ticket_to_ans.lower() == "exit":
        print("Exiting the ticket answering system.")
        driver.quit()
        break

    try:
        ticket_link = driver.find_element(By.XPATH, f"//span[@class='listview-display-id' and text()='{ticket_to_ans}']")
        ticket_link.click()
        print(f"Successfully clicked on ticket {ticket_to_ans}.")
        time.sleep(5)

        subject = scrape_subject(driver)
        open_closed_elements(driver)
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
                        shadow_elements = shadow_root.find_elements(By.CSS_SELECTOR, "div, span, p")
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
            bart_model, bart_tokenizer = load_bart_model()
            summarized_thread = summarize_thread(cleaned_thread, bart_model, bart_tokenizer)

            # Load ticket data for similarity check
            df = load_ticket_data('resolved_tickets.csv')
            tfidf_matrix, vectorizer = vectorize_subjects(df)
            
            _, similar_resolution = find_similar_ticket(subject, tfidf_matrix, df, vectorizer)

            # Generate AI response
            ai_reply = generate_reply_with_llama(summarized_thread, similar_resolution)
            print(f"\nAI Response:\n{ai_reply}")
            similarity_score = compare_ai_response_to_resolution(ai_reply, similar_resolution, df)
            print(f"{GREEN}AI Response Similarity Score: {similarity_score:.2f}%{RESET}")

            # Ask user if they want to use the AI-generated response
            user_choice = input(f"{BRIGHTMAGENTA}Do you want to use the AI-generated response? (yes/no): {RESET}").strip().lower()

            if user_choice == 'yes':
                similarity_score = compare_ai_response_to_resolution(ai_reply, similar_resolution, df)
                print(f"{GREEN}AI Response Similarity Score: {similarity_score:.2f}%{RESET}")
            elif user_choice == 'no':
                # If no, allow the user to input a sentence or keywords, and AI completes the response
                user_input = input(f"{YELLOW}Please enter your input, and the AI will complete it: {RESET}").strip()
                ai_reply = generate_reply_with_custom_input(user_input, similar_resolution)
                print(f"\nAI Response with User Input:\n{ai_reply}")

            # Proceed to type the final response into the ticket system
            click_reply_or_reply_all(driver)
            type_reply_in_iframe(driver, ai_reply)

            exit_after_reply = input(f"Type '{RED}exit{RESET}' to return to the requests page or '{RED}quit{RESET}' to end the session: ").strip()

            if exit_after_reply.lower() == 'quit':
                print("Exiting the system.")
                driver.quit()
                break
            elif exit_after_reply.lower() == 'exit':
                driver.get("https://ask2lit.lassonde.yorku.ca/app/itdesk/ui/requests")
                ticket_rows = scrape_tickets(driver)  

    except Exception as e:
        print(f"Error: Could not navigate to ticket {ticket_to_ans} or scrape the data. {e}")
