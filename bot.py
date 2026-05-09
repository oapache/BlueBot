# ==============================
# 🧩 Imports and Configuration
# ==============================
from telethon import TelegramClient, utils
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


def parse_chat_targets_env() -> list[int | str]:
    multi_value = os.getenv("SOURCE_CHATS", "").strip()
    if multi_value:
        return [
            parse_chat_target(item)
            for item in multi_value.split(",")
            if item.strip()
        ]

    single_value = os.getenv("SOURCE_CHAT", os.getenv("SOURCE_USERNAME", "")).strip()
    if not single_value:
        return []
    return [parse_chat_target(single_value)]


def expand_url(url: str) -> str:
    try:
        response = requests.get(
            url,
            allow_redirects=True,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        return response.url
    except Exception as e:
        print(f"⚠️ Failed to expand URL {url}: {e}")
        return url


def get_all_urls(text: str) -> list[str]:
    return re.findall(r'https?://[^\s]+', text, re.IGNORECASE)

# Telegram source and optional destination groups
SOURCE_CHATS = parse_chat_targets_env()
DESTINATION_CHAT = parse_chat_target(os.getenv("DESTINATION_CHAT", os.getenv("DESTINATION_USERNAME", "")))
ENABLE_TELEGRAM_FORWARD = os.getenv("ENABLE_TELEGRAM_FORWARD", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
ENABLE_MERCADOLIVRE = os.getenv("ENABLE_MERCADOLIVRE", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
ENABLE_SHOPEE = os.getenv("ENABLE_SHOPEE", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
ENABLE_ALIEXPRESS = os.getenv("ENABLE_ALIEXPRESS", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

print(
    "⚙️ Marketplaces enabled:",
    {
        "mercadolivre": ENABLE_MERCADOLIVRE,
        "shopee": ENABLE_SHOPEE,
        "aliexpress": ENABLE_ALIEXPRESS,
    },
)

# Filter keywords to remove from messages
filters = parse_env_list("FILTERS")

# Normalize filters to avoid accent or spacing mismatches
filters = [unicodedata.normalize("NFKD", f) for f in filters]

# Initialize Telegram client
client = TelegramClient("polling_session", api_id, api_hash)
last_ids: dict[str, int] = {}
destination_group = None


async def resolve_chat_entity(target):
    if not isinstance(target, int):
        return await client.get_entity(target)

    real_id, peer_type = utils.resolve_id(target)

    # Warm Telethon's entity cache from the account dialogs before resolving by ID.
    await client.get_dialogs()

    entity = await client.get_entity(peer_type(real_id))
    print(f"✅ Resolved Telegram target {target} -> {type(entity).__name__} ({real_id})")
    return entity


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
    global destination_group

    chat_key = str(getattr(msg.peer_id, "channel_id", None) or getattr(msg.peer_id, "chat_id", None) or getattr(msg.peer_id, "user_id", None) or "unknown")

    # Skip already processed message
    if msg.id == last_ids.get(chat_key):
        return
    last_ids[chat_key] = msg.id

    # Normalize message text
    text = unicodedata.normalize("NFKD", msg.raw_text)
    print(f'\n💬 Message received:\n{text}\n')

    # Skip AliExpress coin campaign and ML coupons
    if any(substr in text for substr in ["Rescue Coins daily on Aliexpress", "Show more"]):
        print("⚠️ Message ignored (contains AliExpress coin campaign or Mercado Livre coupons).")
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
        ml_pattern = r'(https?://(?:www\.)?(?:mercadolivre\.com(?:\.br)?|meli\.la)/[^\s]+|https?://(?:www\.)?mercadolivre\.com(?:\.br)?/sec/[^\s]+)'
        aliexpress_pattern = r'(?:https?://)?(?:www\.)?(?:aliexpress\.com|a\.aliexpress\.com)/[^\s]+'
        all_urls = get_all_urls(text)

        ali_links_raw = re.findall(aliexpress_pattern, text)
        ali_links = [link if link.startswith("http") else "https://" + link for link in ali_links_raw]
        shopee_links = re.findall(shopee_pattern, text)
        ml_links = re.findall(ml_pattern, text)
        print(
            "🧪 DEBUG detected links:",
            {
                "mercadolivre": len(ml_links),
                "shopee": len(shopee_links),
                "aliexpress": len(ali_links),
                "all_urls": len(all_urls),
            },
        )
        if ENABLE_MERCADOLIVRE and not ENABLE_SHOPEE and not ENABLE_ALIEXPRESS:
            non_ml_urls = [url for url in all_urls if url not in ml_links]
            if non_ml_urls and not ml_links:
                print("⚠️ Message ignored (contains only non-Mercado Livre URLs).")
                return

        has_enabled_marketplace_link = (
            (ENABLE_MERCADOLIVRE and bool(ml_links))
            or (ENABLE_ALIEXPRESS and bool(ali_links))
            or (ENABLE_SHOPEE and bool(shopee_links))
        )

        if not has_enabled_marketplace_link:
            print("⚠️ Message ignored (contains no links from enabled marketplaces).")
            return

        # ==============================
        # 💰 Mercado Livre
        # ==============================
        if ENABLE_MERCADOLIVRE:
            for link in ml_links:
                try:
                    expanded_link = expand_url(link)
                    print(f"🔗 Generating Mercado Livre affiliate link for: {link} -> {expanded_link}")
                    affiliate_link = gerar_link_mercadolivre(expanded_link)
                    if affiliate_link and affiliate_link.startswith(("http://", "https://")):
                        text = text.replace(link, affiliate_link)
                        if expanded_link != link:
                            text = text.replace(expanded_link, affiliate_link)
                        print("✅ Mercado Livre link replaced!")
                    else:
                        print(f"⚠️ Ignoring invalid Mercado Livre affiliate link: {affiliate_link}")
                except Exception as e:
                    print(f"❌ Error generating Mercado Livre link: {e}")
        # ==============================
        # 💰 AliExpress
        # ==============================
        if ENABLE_ALIEXPRESS and ali_links:
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
        if ENABLE_SHOPEE:
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
    if not SOURCE_CHATS:
        raise RuntimeError("SOURCE_CHAT or SOURCE_CHATS must be set in the .env file.")

    await client.start()
    if ENABLE_TELEGRAM_FORWARD:
        if not DESTINATION_CHAT:
            raise RuntimeError(
                "DESTINATION_CHAT must be set in the .env file when ENABLE_TELEGRAM_FORWARD is enabled."
            )
        destination_group = await resolve_chat_entity(DESTINATION_CHAT)
    else:
        destination_group = None
    source_chats = [await resolve_chat_entity(target) for target in SOURCE_CHATS]
    print(f"🤖 Bot monitoring via polling for {len(source_chats)} source chat(s)...")

    while True:
        for source_chat in source_chats:
            try:
                async for msg in client.iter_messages(source_chat, limit=1):
                    await process_message(msg)
            except Exception as e:
                print(f"Error fetching messages from {getattr(source_chat, 'id', source_chat)}: {e}")
        await asyncio.sleep(5)


# ==============================
# 🏁 Entry Point
# ==============================
if __name__ == '__main__':
    asyncio.run(main())
