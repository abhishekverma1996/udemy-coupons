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


# 🔥 Load last sent COURSE URL
def load_last_url():
    if not os.path.exists(LAST_SENT_FILE):
        return None
    with open(LAST_SENT_FILE, "r", encoding="utf-8") as f:
        return f.read().strip() or None


# 🔥 Save last sent course URL
def save_last_url(url: str):
    os.makedirs(os.path.dirname(LAST_SENT_FILE), exist_ok=True)
    with open(LAST_SENT_FILE, "w", encoding="utf-8") as f:
        f.write(url)


# Load JSON courses
def load_courses():
    if not os.path.exists(COUPONS_FILE):
        return []
    with open(COUPONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------------
# HELPERS
# -------------------
def html_to_short_text(html: str, limit: int = 200) -> str:
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[: limit - 3] + "..." if len(text) > limit else text


def format_price(p):
    try:
        return f"${float(p):.2f}"
    except:
        return str(p)


# -------------------
# CAPTION BUILDER
# -------------------
def build_caption(course: dict) -> str:
    name = course.get("name", "No Title")
    short_desc = (
        course.get("shoer_description")
        or course.get("short_description")
        or html_to_short_text(course.get("description", ""))
    )
    url = course.get("url", "#")
    category = course.get("category")
    subcategory = course.get("subcategory")
    language = course.get("language", "English")
    instructor = course.get("instructor")
    store = course.get("store", "Udemy")

    price = course.get("price")
    sale = course.get("sale_price")

    lines = []
    lines.append("🆓🆓🆓 <b>FREE COURSE ALERT</b> 🆓🆓🆓")
    lines.append("")
    lines.append(f"📝 <b>{name}</b>")
    lines.append("")

    if short_desc:
        lines.append(f"ℹ️ {short_desc}")

    if instructor:
        lines.append(f"🧑‍🏫 <b>Instructor:</b> {instructor}")

    if language:
        lines.append(f"🌐 <b>Language:</b> {language}")

    if category or subcategory:
        cat_tag = f"#{category.replace(' ', '')}" if category else ""
        extra = f" | {subcategory}" if subcategory else ""
        lines.append(f"📌 <b>Category:</b> {cat_tag}{extra}")

    if store:
        lines.append(f"🏫 <b>Platform:</b> {store}")

    if sale == 0 or sale == 0.0:
        if price:
            lines.append(f"💰 <b>Price:</b> <s>{format_price(price)}</s> ➡️🆓")
        else:
            lines.append("💰 <b>Price:</b> 🆓")
    else:
        lines.append(f"💰 <b>Price:</b> {format_price(price)}")

    lines.append("🏃 <b>ENROLL NOW - LIMITED ENROLLMENTS ONLY</b>")
    lines.append("━━━━━━━━━━━━━━━")
    lines.append(f"🔗 <a href=\"{url}\">Enroll Now</a>")

    caption = "\n".join(lines)
    return caption[: MAX_CAPTION - 3] + "..." if len(caption) > MAX_CAPTION else caption


# -------------------
# MAIN SENDING LOGIC
# -------------------
async def main():
    channel = load_channel()
    if not channel:
        print("❌ Channel not set in channel_id.txt")
        return

    courses = load_courses()
    if not courses:
        print("❌ No courses found")
        return

    last_url = load_last_url()
    current = courses[0]        # Always send *first* course from JSON
    current_url = current.get("url")

    # 🔥 Duplicate check — Only logic needed
    if last_url == current_url:
        print("✔ Already posted this course — skipping...")
        return

    bot = Bot(token=BOT_TOKEN)
    caption = build_caption(current)
    image = current.get("image")
    url = current.get("url")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🎓 Enroll Now", url=url)]]
    )

    try:
        if image:
            await bot.send_photo(
                chat_id=channel,
                photo=image,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        else:
            await bot.send_message(
                chat_id=channel,
                text=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )

        print(f"✔ Sent: {current.get('name')}")
        save_last_url(current_url)

    except Exception as e:
        print("❌ Error sending:", e)

    finally:
        await bot.close()


# -------------------
# RUN
# -------------------
if __name__ == "__main__":
    asyncio.run(main())
