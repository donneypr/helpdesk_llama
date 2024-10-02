from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
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

ticket_rows = driver.find_elements(By.XPATH, "//tr[contains(@class, 'sdpTable.requestlistview_row')]")

for row in ticket_rows:
    ticket_number = row.find_element(By.XPATH, ".//td[2]").text  # Assuming ticket number is in the 2nd column
    subject = row.find_element(By.XPATH, ".//td[3]").text  # Assuming subject is in the 3rd column
    technician = row.find_element(By.XPATH, ".//td[4]").text  # Assuming technician is in the 4th column
    print(f"Ticket Number: {ticket_number}, Subject: {subject}, Technician: {technician}")

time.sleep(100)

driver.quit()
