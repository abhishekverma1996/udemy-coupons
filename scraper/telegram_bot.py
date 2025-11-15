import os
import json
import asyncio
import re
from html import unescape
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# -------------------
# CONFIG
# -------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ BOT_TOKEN not set! Add it to GitHub Secrets.")
    exit(1)

CHANNEL_FILE = "scraper/channel_id.txt"
LAST_SENT_FILE = "scraper/last_sent.txt"
COUPONS_FILE = "website/coupons.json"
MAX_CAPTION = 1024  # Telegram caption limit
# -------------------


# Load saved channel
def load_channel():
    if not os.path.exists(CHANNEL_FILE):
        return None
    with open(CHANNEL_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


# Load last sent index safely
def load_last_sent():
    if not os.path.exists(LAST_SENT_FILE):
        return 0
    try:
        with open(LAST_SENT_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return 0
        return int(content)
    except Exception:
        return 0


# Save last sent index
def save_last_sent(i: int):
    os.makedirs(os.path.dirname(LAST_SENT_FILE), exist_ok=True)
    with open(LAST_SENT_FILE, "w", encoding="utf-8") as f:
        f.write(str(i))


# Load JSON data
def load_courses():
    if not os.path.exists(COUPONS_FILE):
        return []
    with open(COUPONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------------
# HELPERS
# -------------------
def html_to_short_text(html: str, limit: int = 200) -> str:
    """Udemy wali HTML description ko plain short text me convert kare."""
    if not html:
        return ""
    # HTML tags remove
    text = re.sub(r"<[^>]+>", " ", html)
    # HTML entities decode
    text = unescape(text)
    # extra spaces
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text


def format_price(p):
    """Price ko $xx.xx format me convert kare."""
    try:
        return f"${float(p):.2f}"
    except Exception:
        return str(p)


# -------------------
# CAPTION BUILDER (UI)
# -------------------
def build_caption(course: dict) -> str:
    name = course.get("name", "No Title")

    # typo handle: shoer_description
    short_desc = (
        course.get("shoer_description")
        or course.get("short_description")
        or ""
    )

    if not short_desc:
        short_desc = html_to_short_text(course.get("description", ""))

    url = course.get("url", "#")

    category = course.get("category")         # e.g. "IT & Software"
    subcategory = course.get("subcategory")   # e.g. "IT Certifications"
    language = course.get("language", "English")
    instructor = course.get("instructor")     # agar ho to use kar lenge
    store = course.get("store", "Udemy")

    price = course.get("price")              # original price
    sale_price = course.get("sale_price")    # free ho to 0 / 0.0

    lines = []

    # Header – FREE COURSE ALERT
    lines.append("🆓🆓🆓 <b>FREE COURSE ALERT</b> 🆓🆓🆓")
    lines.append("")

    # Title
    lines.append(f"📝 <b>{name}</b>")
    lines.append("")

    # Short description
    if short_desc:
        lines.append(f"ℹ️ {short_desc}")

    # Instructor
    if instructor:
        lines.append(f"🧑‍🏫 <b>Instructor:</b> {instructor}")

    # Language
    if language:
        lines.append(f"🌐 <b>Language:</b> {language}")

    # Category / subcategory
    if category or subcategory:
        cat_tag = f"#{str(category).replace(' ', '')}" if category else ""
        extra = f" | {subcategory}" if subcategory else ""
        lines.append(f"📌 <b>Category:</b> {cat_tag}{extra}")

    # Platform
    if store:
        lines.append(f"🏫 <b>Platform:</b> {store}")

    # Price line – original kata hua
    if sale_price == 0 or sale_price == 0.0:
        # original price -> free
        if price is not None:
            orig = format_price(price)
            lines.append(f"💰 <b>Price:</b> <s>{orig}</s> ➡️🆓")
        else:
            lines.append("💰 <b>Price:</b> 🆓")
    else:
        # normal discount case (agar kabhi use karo)
        if price is not None and sale_price is not None:
            orig = format_price(price)
            newp = format_price(sale_price)
            lines.append(f"💰 <b>Price:</b> <s>{orig}</s> ➡️ {newp}")
        elif price is not None:
            orig = format_price(price)
            lines.append(f"💰 <b>Price:</b> {orig}")

    lines.append("🏃 <b>ENROLL NOW - LIMITED ENROLLMENTS ONLY</b>")
    lines.append("━━━━━━━━━━━━━━━")
    lines.append(f"🔗 <a href=\"{url}\">Enroll Now</a>")

    text = "\n".join(lines)

    # Caption limit
    if len(text) > MAX_CAPTION:
        text = text[: MAX_CAPTION - 3] + "..."

    return text


# -------------------
# MAIN SENDING LOGIC
# -------------------
async def main():
    channel = load_channel()
    if not channel:
        print("❌ Channel not set. Add a channel to channel_id.txt")
        return

    last = load_last_sent()
    courses = load_courses()

    if last >= len(courses):
        print("✔ No new courses to send.")
        return

    course = courses[last]
    bot = Bot(token=BOT_TOKEN)

    text = build_caption(course)
    image = course.get("image")
    url = course.get("url", "#")

    # Enroll Now button
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎓 Enroll Now", url=url)]
        ]
    )

    # Send to Telegram
    try:
        if image:
            await bot.send_photo(
                chat_id=channel,
                photo=image,
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        else:
            await bot.send_message(
                chat_id=channel,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )

        print(f"✔ Sent: {course.get('name')}")
        save_last_sent(last + 1)  # Only increment if successfully sent

    except Exception as e:
        print(f"❌ Failed to send course: {e}")
    finally:
        await bot.close()  # Safe close


# -------------------
# RUN
# -------------------
if __name__ == "__main__":
    asyncio.run(main())
