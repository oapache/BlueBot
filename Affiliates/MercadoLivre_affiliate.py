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
from selenium.webdriver.common.action_chains import ActionChains
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

        # Some Mercado Livre short/share pages open an intermediate card before the
        # actual product page. When present, click through it; otherwise continue.
        access_product_selectors = [
            (
                By.XPATH,
                "//*[@id='root-app']/div/div/div[2]/div[2]/section/section/section/div/ul/div/div[2]/div/div[2]/div/div/a",
            ),
            (By.XPATH, "//div[contains(., 'Acessar produto') and @role='button']"),
            (By.XPATH, "//a[contains(., 'Ir para produto')]"),
            (By.XPATH, "//span[contains(., 'Ir para produto')]/ancestor::a[1]"),
            (By.XPATH, "//button[contains(., 'Acessar produto')]"),
            (By.XPATH, "//a[contains(., 'Acessar produto')]"),
        ]
        for selector in access_product_selectors:
            try:
                print("[DEBUG] Attempting to click 'Access product'")
                acessar_produto = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(selector)
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", acessar_produto)
                acessar_produto.click()
                print("[DEBUG] Clicked 'Access product'")
                time.sleep(5)
                break
            except Exception:
                continue

        # --- STEP 3: Click “Share” button (with retry logic) ---
        share_selectors = [
            (By.CSS_SELECTOR, "button[data-testid='generate_link_button']"),
            (By.XPATH, "//button[@data-testid='generate_link_button']"),
            (By.XPATH, "//button[contains(., 'Compartilhar')]"),
            (By.XPATH, "//span[normalize-space()='Compartilhar']/ancestor::button[1]"),
            (By.CSS_SELECTOR, "button.generate_link_button"),
        ]
        last_share_error = None
        compartilhar_btn = None
        for selector in share_selectors:
            try:
                print(f"[DEBUG] Trying to click 'Share' with selector: {selector}")
                compartilhar_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(selector)
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", compartilhar_btn)
                WebDriverWait(driver, 10).until(
                    lambda d: compartilhar_btn.is_displayed() and compartilhar_btn.is_enabled()
                )
                try:
                    compartilhar_btn.click()
                except Exception:
                    try:
                        ActionChains(driver).move_to_element(compartilhar_btn).click().perform()
                    except Exception:
                        driver.execute_script("arguments[0].click();", compartilhar_btn)
                print("[DEBUG] Clicked 'Share'")
                time.sleep(2)
                break
            except Exception as e:
                last_share_error = e
                compartilhar_btn = None
                continue

        if compartilhar_btn is None:
            raise RuntimeError(f"Failed to click 'Share' with known selectors: {last_share_error}")

        # --- STEP 4: Click “Copy Link” ---
        print("[DEBUG] Trying to click 'Copy link'")
        copy_selectors = [
            (By.XPATH, "//button[contains(., 'Copiar link')]"),
            (By.XPATH, "//span[normalize-space()='Copiar link']/ancestor::button[1]"),
            (By.XPATH, "//button[contains(., 'Copiar')]"),
        ]
        copiar_botao = None
        last_copy_error = None
        for selector in copy_selectors:
            try:
                copiar_botao = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(selector)
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", copiar_botao)
                try:
                    copiar_botao.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", copiar_botao)
                break
            except Exception as e:
                last_copy_error = e
                copiar_botao = None
                continue

        if copiar_botao is None:
            raise RuntimeError(f"Failed to click 'Copy link' with known selectors: {last_copy_error}")
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
