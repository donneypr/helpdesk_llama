from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import time


current_directory = os.getcwd()

chromedriver_path = os.path.join(current_directory, "chromedriver")

service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service)

driver.get("https://ask2lit.lassonde.yorku.ca/app/itdesk/ui/requests/71651000024451425/details")

time.sleep(10)

driver.quit()