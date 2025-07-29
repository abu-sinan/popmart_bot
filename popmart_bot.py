import asyncio
import json
import logging
import os
import random
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import aiohttp
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Load config
with open("config.json", "r") as f:
    CONFIG = json.load(f)

MAX_RETRIES = CONFIG.get("max_retries", 5)
HEADLESS = CONFIG.get("headless", True)

# Logging with rotation
logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("log.txt", maxBytes=512000, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Telegram alerts
async def send_telegram(msg):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        await session.post(url, data={"chat_id": TG_CHAT_ID, "text": msg})

# Safe click with retry
async def retry_click(page, selector, retries=5, delay=1):
    for _ in range(retries):
        try:
            await page.locator(selector).click(timeout=5000)
            return True
        except:
            await asyncio.sleep(delay)
    return False

# Main bot logic
async def run_bot():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="en-US"
        )
        page = await context.new_page()
        await stealth_async(page)

        try:
            await page.goto("https://www.popmart.com/us", timeout=60000)
            await retry_click(page, "text=United States")
            await retry_click(page, ".policy_acceptBtn__ZNU71")

            # Smart login check
            if await page.locator('a[href*="/us/user/login"]').is_visible():
                await send_telegram("🔐 Logging in...")
                await retry_click(page, 'a[href*="/us/user/login"]')
                await page.fill("#email", EMAIL)
                await page.click("text=CONTINUE")
                await page.wait_for_selector("#password", timeout=15000)
                await page.fill("#password", PASSWORD)
                await page.click("text=SIGN IN")
                await page.wait_for_timeout(3000)
                await send_telegram("✅ Login successful")
            else:
                await send_telegram("✅ Already logged in")

            # Monitor loop
            while True:
                for product in CONFIG["products"]:
                    try:
                        await page.goto(product["url"], timeout=60000)

                        if not await page.locator("text=ADD TO BAG").is_visible():
                            msg = f"❌ Out of stock: {product['url']}"
                            logger.warning(msg)
                            await send_telegram(msg)
                            continue

                        await send_telegram(f"🟢 In Stock: {product['url']}")
                        await send_telegram("🛒 Adding to bag...")

                        # Select size
                        size = product["size"].lower()
                        if "single" in size:
                            await retry_click(page, "text=Single box")
                        elif "whole" in size:
                            await retry_click(page, "text=Whole set")

                        # Set quantity
                        for _ in range(product["quantity"] - 1):
                            await retry_click(page, ".index_countButton__mJU5Q >> text=+")

                        # Add to bag
                        await retry_click(page, "text=ADD TO BAG")
                        await page.wait_for_selector("text=Added To Bag", timeout=10000)
                        await send_telegram("✅ Added to bag. Proceeding to checkout...")

                        # Checkout steps
                        await retry_click(page, "text=View Bag")
                        await retry_click(page, "text=Select all")
                        await retry_click(page, "text=CHECK OUT")
                        await retry_click(page, "text=PROCEED TO PAY", delay=2)

                        await page.wait_for_load_state("networkidle")
                        await asyncio.sleep(2)

                        # Handle "Oops"
                        if await page.locator("text=High order volume").is_visible():
                            await page.click("text=OK")
                            raise Exception("Oops! High order volume.")

                        # Select credit card and pay
                        await send_telegram("💳 Paying with credit card...")
                        await retry_click(page, "text=CreditCard")
                        await retry_click(page, 'button:has-text("Pay")')

                        msg = f"🎉 Success! Purchased: {product['url']}"
                        logger.info(msg)
                        await send_telegram(msg)

                    except Exception as e:
                        msg = f"⚠️ Failed: {product['url']} - {str(e)}"
                        logger.error(msg)
                        await send_telegram(msg)
                    await asyncio.sleep(1)

                logger.info("🔁 Sleeping 5 minutes before next round...")
                await asyncio.sleep(300)

        except Exception as e:
            msg = f"❌ Fatal Error: {str(e)}"
            logger.error(msg)
            await send_telegram(msg)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_bot())