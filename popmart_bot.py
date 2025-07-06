import time
import yaml
import random
import logging
import sys
import os
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from playwright.sync_api import sync_playwright

# Load .env credentials
load_dotenv()

# Logging setup
def setup_logging(log_level="INFO"):
    handler = RotatingFileHandler("popmart_bot.log", maxBytes=2 * 1024 * 1024, backupCount=3)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.addHandler(handler)

# Load and validate config
def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def validate_config(config):
    if "login_url" not in config or "products" not in config:
        raise ValueError("❌ 'login_url' and 'products' are required in config.yaml")
    if not isinstance(config["products"], list) or not config["products"]:
        raise ValueError("❌ 'products' must be a non-empty list.")
    for p in config["products"]:
        if "url" not in p or "quantity" not in p:
            raise ValueError("❌ Each product must have 'url' and 'quantity'.")

# Login
def login(page):
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    if not email or not password:
        raise Exception("❌ EMAIL and PASSWORD must be set in .env")

    page.goto(config["login_url"])
    page.wait_for_load_state("networkidle")
    time.sleep(random.uniform(1, 2))

    page.fill('input[placeholder="Enter your e-mail address"]', email)
    page.click('button:has-text("CONTINUE")')
    page.wait_for_timeout(2000)
    page.fill('input[placeholder="Enter your password"]', password)
    page.click('button:has-text("SIGN IN")')
    page.wait_for_load_state("networkidle")
    logging.info("✅ Logged in")

# Quantity handling
def set_quantity(page, quantity):
    try:
        qty_input = page.locator('input[type="number"]')
        if qty_input.is_visible():
            qty_input.fill(str(quantity))
            logging.info(f"🔢 Quantity set to {quantity}")
            return
        plus_button = page.locator('button[aria-label="Increase quantity"]')
        for _ in range(quantity - 1):
            if plus_button.is_disabled():
                break
            plus_button.click()
            time.sleep(0.2)
        logging.info("🔢 Quantity set using + button")
    except Exception as e:
        logging.warning(f"⚠️ Quantity error: {e}")

# Simulate scroll
def simulate_human_behavior(page):
    page.mouse.wheel(0, random.randint(300, 800))
    time.sleep(random.uniform(0.5, 1.5))

# Add to bag and open cart
def add_to_bag(page):
    if page.locator('button:has-text("Add to Bag")').is_visible():
        page.click('button:has-text("Add to Bag")')
        logging.info("🛒 Added to Bag")
        time.sleep(2)
        if page.locator('button:has-text("VIEW")').is_visible():
            page.click('button:has-text("VIEW")')
            logging.info("👁️ Viewing Bag")
            page.wait_for_load_state("networkidle")
        else:
            logging.warning("⚠️ VIEW button not found")
    else:
        logging.warning("❌ Add to Bag not found")

# Checkout steps
def proceed_to_checkout(page):
    if page.locator('button:has-text("CHECKOUT")').is_visible():
        page.click('button:has-text("CHECKOUT")')
        logging.info("💳 Checkout clicked")
        page.wait_for_load_state("networkidle")
    else:
        raise Exception("❌ CHECKOUT not found")

def proceed_to_payment(page):
    if page.locator('button:has-text("PROCEED TO PAY")').is_visible():
        page.click('button:has-text("PROCEED TO PAY")')
        logging.info("📦 Proceed to Pay")
        page.wait_for_load_state("networkidle")
    else:
        raise Exception("❌ PROCEED TO PAY not found")

def submit_payment(page):
    if page.locator('button:has-text("Pay")').is_visible():
        page.click('button:has-text("Pay")')
        logging.info("💰 Payment submitted")
    else:
        raise Exception("❌ Pay button not found")

# Core product logic
def check_and_buy(page, product, max_retries):
    url = product["url"]
    quantity = product.get("quantity", 1)

    for attempt in range(max_retries):
        try:
            logging.info(f"🔍 Checking: {url} | Qty: {quantity} | Try: {attempt+1}")
            page.goto(url)
            page.wait_for_load_state("networkidle")
            simulate_human_behavior(page)

            if page.locator("text=Out of Stock").is_visible():
                logging.info("❌ Out of Stock")
                return False

            if page.locator('button:has-text("Whole Set")').is_visible():
                page.click('button:has-text("Whole Set")')
                logging.info("📦 Whole Set Selected")

            set_quantity(page, quantity)
            add_to_bag(page)
            proceed_to_checkout(page)
            proceed_to_payment(page)
            submit_payment(page)
            return True
        except Exception as e:
            logging.error(f"❌ Error on attempt {attempt+1}: {e}")
            time.sleep(5)
    return False

# Main loop
def main():
    global config
    config = load_config()
    validate_config(config)
    setup_logging(config.get("log_level", "INFO"))

    if "--debug" in sys.argv:
        config["headless"] = False
        logging.info("🐞 Debug mode: browser visible")

    products = config["products"]
    remaining = products.copy()
    delay_min, delay_max = config.get("delay_range", [60, 180])
    max_retries = config.get("max_retries", 3)
    headless = config.get("headless", True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        login(page)

        while remaining:
            for product in remaining[:]:
                try:
                    if check_and_buy(page, product, max_retries):
                        remaining.remove(product)
                        logging.info(f"✅ Purchased: {product['url']}")
                    else:
                        logging.info(f"🔁 Retry later: {product['url']}")
                except Exception as e:
                    logging.error(f"⚠️ Product check failed: {e}")
                time.sleep(random.uniform(5, 15))

            if remaining:
                wait_time = random.uniform(delay_min, delay_max)
                logging.info(f"⏳ Waiting {int(wait_time)}s")
                time.sleep(wait_time)

        logging.info("🎉 All products purchased")
        browser.close()

# Safe restart loop
if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            logging.error(f"🔁 Bot crashed: {e}")
            time.sleep(10)
