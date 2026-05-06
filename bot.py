# ==============================
# 🧩 Imports and Configuration
# ==============================
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import re
import asyncio
import os
import requests
import base64
import unicodedata
from dotenv import load_dotenv

# Affiliate link generators
from Affiliates.shopee_affiliate import gerar_link_afiliado_shopee
from Affiliates.aliexpress_affiliate import gerar_links_afiliado_aliexpress
from Affiliates.MercadoLivre_affiliate import gerar_link_mercadolivre

# Load environment variables
load_dotenv()

# ==============================
# 🔑 Configuration Variables
# ==============================
ALI_APP_KEY = os.getenv("ALIEXPRESS_APP_KEY")
ALI_APP_SECRET = os.getenv("ALIEXPRESS_APP_SECRET")
ALI_TRACKING_ID = os.getenv("ALIEXPRESS_TRACKING_ID")
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")

# Required for headless execution environments (Linux servers)
if os.name != "nt":
    os.environ.setdefault("DISPLAY", ":1")


def parse_env_list(name: str) -> list[str]:
    raw_value = os.getenv(name, "")
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def parse_chat_target(raw_value: str):
    value = raw_value.strip()
    if not value:
        return ""
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value

# Telegram source and optional destination groups
SOURCE_CHAT = parse_chat_target(os.getenv("SOURCE_CHAT", os.getenv("SOURCE_USERNAME", "")))
DESTINATION_CHAT = parse_chat_target(os.getenv("DESTINATION_CHAT", os.getenv("DESTINATION_USERNAME", "")))
ENABLE_TELEGRAM_FORWARD = os.getenv("ENABLE_TELEGRAM_FORWARD", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Filter keywords to remove from messages
filters = parse_env_list("FILTERS")

# Normalize filters to avoid accent or spacing mismatches
filters = [unicodedata.normalize("NFKD", f) for f in filters]

# Initialize Telegram client
client = TelegramClient("polling_session", api_id, api_hash)
last_id = None
destination_group = None


# ==============================
# ⚙️ Message Processing Function
# ==============================
async def process_message(msg):
    """
    Process a new incoming Telegram message.

    Responsibilities:
    - Avoids processing duplicates.
    - Cleans and filters out unwanted content.
    - Detects affiliate-supported URLs and replaces them.
    - Forwards the final message (text/media) to WhatsApp and optionally Telegram.
    """
    global last_id, destination_group

    # Skip already processed message
    if msg.id == last_id:
        return
    last_id = msg.id

    # Normalize message text
    text = unicodedata.normalize("NFKD", msg.raw_text)
    print(f'\n💬 Message received:\n{text}\n')

    # Skip AliExpress coin campaign and ML coupons
    if any(substr in text for substr in ["Rescue Coins daily on Aliexpress", "Show more"]):
        print("⚠️ Message ignored (contains AliExpress coin campaign or Mercado Livre coupons).")
        return

    # Block forbidden stores
    if re.search(r"(amazon\.com(?:\.br)?|amzn\.to|magazineluiza\.com\.br|magazineluiza\.onelink\.me)", text, re.IGNORECASE):
        print("⚠️ Message ignored (contains Amazon or Magazine Luiza link).")
        return

    # Remove custom filters
    for f in filters:
        text = re.sub(re.escape(f), '', text, flags=re.IGNORECASE)

    # Normalize whitespace and line breaks
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()

    # Double-check for blocked snippets
    for blocked_snippet in filters:
        if blocked_snippet.lower() in text.lower():
            print(f"⚠️ Message ignored (contains blocked snippet: {blocked_snippet})")
            return

    if text:
        # ==============================
        # 🔍 URL Pattern Detection
        # ==============================
        shopee_pattern = r'(https?://(?:www\.)?(?:shopee\.com\.br|s\.shopee\.com\.br)/[^\s]+)'
        ml_pattern = r'(https?://(?:www\.)?(?:mercadolivre\.com(?:\.br)?)/[^\s]+|https?://(?:www\.)?mercadolivre\.com(?:\.br)?/sec/[^\s]+)'
        aliexpress_pattern = r'(?:https?://)?(?:www\.)?(?:aliexpress\.com|a\.aliexpress\.com)/[^\s]+'

        ali_links_raw = re.findall(aliexpress_pattern, text)
        ali_links = [link if link.startswith("http") else "https://" + link for link in ali_links_raw]
        shopee_links = re.findall(shopee_pattern, text)
        ml_links = re.findall(ml_pattern, text)

        # ==============================
        # 💰 Mercado Livre
        # ==============================
        for link in ml_links:
            try:
                print(f"🔗 Generating Mercado Livre affiliate link for: {link}")
                affiliate_link = gerar_link_mercadolivre(link)
                if affiliate_link:
                    text = text.replace(link, affiliate_link)
                    print("✅ Mercado Livre link replaced!")
            except Exception as e:
                print(f"❌ Error generating Mercado Livre link: {e}")
        # ==============================
        # 💰 AliExpress
        # ==============================
        if ali_links:
            try:
                print(f"🔗 Generating AliExpress affiliate links for: {ali_links}")
                affiliate_links = gerar_links_afiliado_aliexpress(
                    links=ali_links,
                    app_key=ALI_APP_KEY,
                    app_secret=ALI_APP_SECRET,
                    tracking_id=ALI_TRACKING_ID
                )
                for original_raw, new in zip(ali_links_raw, affiliate_links):
                    if new:
                        if original_raw.startswith("http"):
                            text = text.replace(original_raw, new)
                        else:
                            text = text.replace("https://" + original_raw, new)
                            text = text.replace(original_raw, new)
                        print(f"✅ AliExpress link replaced: {original_raw} -> {new}")
            except Exception as e:
                print(f"❌ Error generating AliExpress links: {e}")

        # ==============================
        # 💰 Shopee
        # ==============================
        for link in shopee_links:
            try:
                print(f"🔗 Generating Shopee link: {link}")
                affiliate_link = await gerar_link_afiliado_shopee(link)
                if affiliate_link:
                    text = text.replace(link, affiliate_link)
                    print(f"✅ Shopee link replaced!")
            except Exception as e:
                print(f"❌ Shopee error: {e}")

        # ==============================
        # 📤 Message Forwarding
        # ==============================
        print(f"✅ Sending filtered message:\n{text}\n")
        payload = {"text": text}
        telegram_image_path = None

        # Download and encode media (if present)
        if msg.media and isinstance(msg.media, (MessageMediaPhoto, MessageMediaDocument)):
            try:
                telegram_image_path = "temp_telegram_image.jpg"
                await msg.download_media(file=telegram_image_path)

                with open(telegram_image_path, "rb") as f:
                    file = f.read()
                    base64_img = base64.b64encode(file).decode("utf-8")
                    mime_type = "image/jpeg" if isinstance(msg.media, MessageMediaPhoto) else "application/octet-stream"
                    payload["base64Image"] = base64_img
                    payload["mimeType"] = mime_type
            except Exception as e:
                print(f"❌ Error downloading image: {e}")

        # Send message to WhatsApp via local API
        try:
            resp = requests.post("http://localhost:4000/send", json=payload)
            if resp.status_code == 200:
                print("✅ Message sent to WhatsApp!")
            else:
                print(f"❌ Failed to send to WhatsApp: {resp.status_code}")
        except Exception as e:
            print(f"❌ Error sending to WhatsApp: {e}")

        # Forward message to Telegram destination group if enabled
        try:
            if ENABLE_TELEGRAM_FORWARD and destination_group:
                if telegram_image_path:
                    await client.send_file(destination_group, telegram_image_path, caption=text)
                else:
                    await client.send_message(destination_group, text)
                print("✅ Message sent to Telegram group!")
        except Exception as e:
            print(f"❌ Error sending message to Telegram: {e}")
        finally:
            if telegram_image_path and os.path.exists(telegram_image_path):
                os.remove(telegram_image_path)

    else:
        print("⚠️ Nothing useful to send after filtering.")


# ==============================
# 🚀 Main Monitoring Loop
# ==============================
async def main():
    """
    Initializes the Telegram client and continuously polls
    the source group/channel for new messages.
    """
    global destination_group
    if not SOURCE_CHAT:
        raise RuntimeError("SOURCE_CHAT must be set in the .env file.")

    await client.start()
    if ENABLE_TELEGRAM_FORWARD:
        if not DESTINATION_CHAT:
            raise RuntimeError(
                "DESTINATION_CHAT must be set in the .env file when ENABLE_TELEGRAM_FORWARD is enabled."
            )
        destination_group = await client.get_entity(DESTINATION_CHAT)
    else:
        destination_group = None
    print("🤖 Bot monitoring via polling...")

    while True:
        try:
            async for msg in client.iter_messages(SOURCE_CHAT, limit=1):
                await process_message(msg)
        except Exception as e:
            print(f"Error fetching messages: {e}")
        await asyncio.sleep(5)


# ==============================
# 🏁 Entry Point
# ==============================
if __name__ == '__main__':
    asyncio.run(main())
