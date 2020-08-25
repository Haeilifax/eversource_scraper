"""Scrape Eversource Utility account histories"""
# TODO: Fix address loop for addresses with the same name
import os
from functools import partial

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common import exceptions as selexcept
import dotenv


class GoToExcept(Exception):
    """Exception for breaking try-except blocks"""
    pass


def configure_settings():
    """Configure settings based on .env"""
    dotenv.load_dotenv()
    config = {
        "username": os.getenv("EVERSOURCE_USERNAME"),
        "password": os.getenv("EVERSOURCE_PASSWORD"),
        "login_url": os.getenv("EVERSOURCE_LOGINURL"),
        }
    return config


def _selected(driver):
    """Find which accounts are currently selected"""
    selected_account = driver.find_element_by_css_selector("[data-id=Accountddl1]")
    return selected_account.title


def _access_page(account, menu_button, driver, wait):
    """Access a specified billing account through dropdown menu"""
    menu_button.click()
    # Have to use unprimed _get_dropdown due to current scope
    dropdown = _get_dropdown("SelectButton2", driver)
    dropdown.find_element_by_link_text(account).click()
    result_button = wait.until(EC.element_to_be_clickable((By.ID, "SelectButton2")))
    return result_button


def _access_address_page(address, address_button, driver, wait):
    """Access specified address for billing account through dropdown menu"""
    address_button.click()
    # Have to use unprimed _get_dropdown due to current scope
    address_dropdown = _get_dropdown("SelectButton3", driver)
    address_dropdown.find_element_by_link_text(address).click()
    menu_button = wait.until(EC.element_to_be_clickable((By.ID, "SelectButton2")))
    address_button = driver.find_element_by_id("SelectButton3")
    return address_button, menu_button


def _get_dropdown(button_id, driver):
    """Find and return dropdown menu which is labelled by specified button"""
    result = driver.find_element_by_css_selector(f"[aria-labelledby={button_id}]")
    return result

def _scrape_table(driver):
    """Scrape current page for utility table"""
    driver.find_element_by_id("tableTab").click()
    try:
        table = driver.find_element_by_tag_name("table")
        return table.text.split("\n")[2:]
    except selexcept.NoSuchElementException:
        print("table not found")
        return ""


def _find_addresses(driver, wait):
    """Find addresses for current biliing account"""
    try:
        address_button = wait.until(EC.element_to_be_clickable((By.ID, "SelectButton3")))
        address_dropdown = _get_dropdown("SelectButton3", driver)
        address_button.click()
        addresses_raw = address_dropdown.text
        addresses = addresses_raw.split("\n")
        address_button.click()
        if addresses[0] == "13 months":
            raise GoToExcept("Not a list of addresses")
    except (selexcept.NoSuchElementException, GoToExcept):
        addresses = []
    return addresses


def output(info):
    """Generic output method --- Change for production"""
    for k,v in info.items():
        print(f"Key: {k}, Value: {v}\n___________\n")


def main():
    """Main"""
    config = configure_settings()
    USERNAME = config.get("username")
    PASSWORD = config.get("password")
    LOGIN_SITE = config.get("login_url")

    driver = webdriver.Firefox()
    wait = WebDriverWait(driver, 10)

    # Make functions easier to use by priming values
    # selected = partial(_selected, driver=driver)
    access_page = partial(_access_page, driver=driver, wait=wait)
    access_address_page = partial(_access_address_page, driver=driver, wait=wait)
    get_dropdown = partial(_get_dropdown, driver=driver)
    scrape_table = partial(_scrape_table, driver=driver)
    find_addresses = partial(_find_addresses, driver=driver, wait=wait)

    # Login to Eversource
    driver.get(LOGIN_SITE)
    username_box = driver.find_element_by_id("WebId")
    password_box = driver.find_element_by_id("Password")
    submit_button = driver.find_element_by_id("submit")

    username_box.send_keys(USERNAME)
    password_box.send_keys(PASSWORD)
    # Selenium submit function throws error -- going old fashioned
    submit_button.click()

    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "My Account"))).click()
    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "View Usage"))).click()

    # Get full list of accounts
    menu_button = wait.until(EC.element_to_be_clickable((By.ID, "SelectButton2")))
    menu_button.click()
    billing_accounts_raw = get_dropdown("SelectButton2").text
    billing_accounts = billing_accounts_raw.split("\n")
    menu_button.click()

    account_data = {}

    for account in billing_accounts:
        account_data[account] = {}
        menu_button = access_page(account, menu_button)
        addresses = find_addresses()
        if not addresses:
            # Ensure that account_data is nested at the same level throughout
            account_data[account].update({account: scrape_table()})
        else:
            address_button = driver.find_element_by_id("SelectButton3")
            for address in addresses:
                # Breaks for addresses with the same name
                address_button, menu_button = access_address_page(address, address_button)
                account_data[account].update({address: scrape_table()})
        print("______________\n", account_data)
    return account_data


if __name__ == "__main__":
    utility_data = main()
    output(utility_data)
