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
from pathlib import Path


def _resolve_browser_binary() -> str | None:
    configured = os.getenv("BROWSER_BINARY_PATH")
    if configured and Path(configured).exists():
        return configured

    candidates = []
    if os.name == "nt":
        local_app_data = os.getenv("LOCALAPPDATA", "")
        program_files = os.getenv("PROGRAMFILES", r"C:\Program Files")
        program_files_x86 = os.getenv("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
        candidates.extend([
            Path(program_files) / "BraveSoftware/Brave-Browser/Application/brave.exe",
            Path(program_files_x86) / "BraveSoftware/Brave-Browser/Application/brave.exe",
            Path(program_files) / "Google/Chrome/Application/chrome.exe",
            Path(program_files_x86) / "Google/Chrome/Application/chrome.exe",
            Path(local_app_data) / "Google/Chrome/Application/chrome.exe",
        ])
    else:
        candidates.extend([
            Path("/usr/bin/brave-browser"),
            Path("/usr/bin/google-chrome"),
            Path("/usr/bin/chromium-browser"),
        ])

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


def _resolve_chromedriver_path() -> str:
    configured = os.getenv("CHROMEDRIVER_PATH")
    if configured and Path(configured).exists():
        return configured

    repo_root = Path(__file__).resolve().parents[1]
    candidates = [
        repo_root / "chromedriver.exe",
        repo_root / "chromedriver",
        Path(__file__).resolve().parent / "chromedriver.exe",
        Path(__file__).resolve().parent / "chromedriver",
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    raise FileNotFoundError(
        "ChromeDriver not found. Set CHROMEDRIVER_PATH in .env or place chromedriver in the project root."
    )


def gerar_link_mercadolivre(url: str) -> str | None:
    """
    Generates a Mercado Livre affiliate link using Selenium automation.

    Args:
        url (str): The Mercado Livre product URL.

    Returns:
        str | None: The affiliate link if successful, or None if an error occurs.
    """

    print("[DEBUG] Starting gerar_link_mercadolivre")

    browser_binary = _resolve_browser_binary()
    chromedriver_path = _resolve_chromedriver_path()
    browser_profile_dir = os.getenv("BROWSER_PROFILE_DIR", "").strip()

    # Browser configuration
    options = Options()
    if browser_binary:
        options.binary_location = browser_binary
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    if browser_profile_dir:
        options.add_argument(f"--user-data-dir={browser_profile_dir}")
        options.add_argument("--profile-directory=Default")

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
