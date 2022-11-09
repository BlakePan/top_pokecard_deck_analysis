from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://www.pokemon-card.com/deck/confirm.html/deckID/kbkFkF-YjaVeS-VVd1kV/")

driver.find_element(By.ID, "deckView01").click()

elem = driver.find_element(By.CLASS_NAME, "Grid_item")
print(elem)

driver.close()

