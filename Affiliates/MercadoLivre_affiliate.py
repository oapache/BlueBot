"""
mercadolivre_link_generator.py
--------------------------------
Automates the process of generating affiliate links on Mercado Livre using Selenium with Brave browser.

This script:
1. Opens a specified Mercado Livre product URL.
2. Handles potential cookie banners.
3. Navigates through UI elements to access the product page.
4. Clicks the “Share” button.
5. Copies the affiliate link to the clipboard.
6. Returns the copied link as output.

Developed for automation and affiliate marketing purposes.

"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyperclip
import time
import os


def gerar_link_mercadolivre(url: str) -> str | None:
    """
    Generates a Mercado Livre affiliate link using Selenium automation.

    Args:
        url (str): The Mercado Livre product URL.

    Returns:
        str | None: The affiliate link if successful, or None if an error occurs.
    """

    print("[DEBUG] Starting gerar_link_mercadolivre")

    # Paths for Brave browser and ChromeDriver
    brave_path = "/usr/bin/brave-browser"
    chromedriver_path = os.path.join(os.path.dirname(__file__), "chromedriver")
    user_data_dir = "/root/.config/BraveSoftware/Brave-Browser/ProfileBot"

    # Browser configuration
    options = Options()
    options.binary_location = brave_path
    options.add_argument("--no-sandbox")
    options.add_argument("--user-data-dir=/root/.config/BraveSoftware/Brave-Browser")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--start-maximized")

    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        print(f"[DEBUG] Opening URL: {url}")
        driver.get(url)
        wait = WebDriverWait(driver, 20)

        # --- STEP 1: Handle cookie consent banner ---
        try:
            print("[DEBUG] Trying to close cookie banner")
            cookie_banner = wait.until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "cookie-consent-banner-opt-out__container")
                )
            )
            close_button = cookie_banner.find_element(By.TAG_NAME, "button")
            close_button.click()
            print("🍪 Cookie banner closed successfully")
            time.sleep(1)
        except Exception:
            print("🍪 No visible cookie banner found")

        # --- STEP 2: Click “Access Product” ---
        print("[DEBUG] Attempting to click 'Access product'")
        acessar_produto = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "/html/body/main/div/div/div[2]/div[2]/section/section/section/div/ul/div/div[2]",
                )
            )
        )
        acessar_produto.click()
        print("[DEBUG] Clicked 'Access product'")
        time.sleep(5)

        # --- STEP 3: Click “Share” button (with retry logic) ---
        try:
            print("[DEBUG] Trying to click 'Share'")
            compartilhar_btn = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[2]/nav/div/div[3]/div/div/button")
                )
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", compartilhar_btn)
            compartilhar_btn.click()
            print("[DEBUG] Clicked 'Share'")
            time.sleep(2)
        except Exception as e:
            print(f"[ERROR] Failed to click 'Share': {e}")
            print("[DEBUG] Waiting 5 seconds before retry...")
            time.sleep(5)
            compartilhar_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[2]/nav/div/div[3]/div/div/button")
                )
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", compartilhar_btn)
            compartilhar_btn.click()
            print("[DEBUG] Clicked 'Share' on second attempt")
            time.sleep(2)

        # --- STEP 4: Click “Copy Link” ---
        print("[DEBUG] Trying to click 'Copy link'")
        copiar_botao = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "/html/body/div[2]/nav/div/div[3]/div/div[2]/div/div/div/div/div[2]/div/div/div/div[2]/div/div/div/button",
                )
            )
        )
        copiar_botao.click()
        print("[DEBUG] Clicked 'Copy link'")
        time.sleep(2)  # Ensure clipboard data is updated

        # --- STEP 5: Retrieve the affiliate link from clipboard ---
        link_afiliado = pyperclip.paste()
        print(f"[DEBUG] Affiliate link copied: {link_afiliado}")

        return link_afiliado

    except Exception as e:
        print("❌ Error:", e)
        return None

    finally:
        print("[DEBUG] Closing WebDriver session")
        driver.quit()
