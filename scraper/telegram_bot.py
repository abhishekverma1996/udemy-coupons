import os
import json
import re
import asyncio
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

def load_channel():
    if not os.path.exists(CHANNEL_FILE):
        return None
    return open(CHANNEL_FILE).read().strip()

def load_last_sent():
    if not os.path.exists(LAST_SENT_FILE):
        return 0
    try:
        content = open(LAST_SENT_FILE).read().strip()
        if not content:
            return 0
        return int(content)
    except:
        return 0

def save_last_sent(i):
    os.makedirs(os.path.dirname(LAST_SENT_FILE), exist_ok=True)
    with open(LAST_SENT_FILE, "w") as f:
        f.write(str(i))

def load_courses():
    if not os.path.exists(COUPONS_FILE):
        return []
    return json.load(open(COUPONS_FILE, "r", encoding="utf-8"))


# -------------------
# Clean HTML → Short text
# -------------------
def html_to_short_text(html: str, limit: int = 200) -> str:
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[:limit - 3] + "..."
    return text


# -------------------
# CAPTION UI BUILDER
# -------------------
def build_caption(course: dict) -> str:
    name = course.get("name", "No Title")
    url = course.get("url", "#")

    short_desc = (
        course.get("shoer_description")
        or course.get("short_description")
        or ""
    )
    if not short_desc:
        short_desc = html_to_short_text(course.get("description", ""))

    category = course.get("category")
    subcategory = course.get("subcategory")
    language = course.get("language", "English")
    store = course.get("store", "Udemy")
    price = course.get("price")
    sale_price = course.get("sale_price")
    lectures = course.get("lectures")
    views = course.get("views")
    rating = course.get("rating")

    lines = []
    lines.append("🆓 *FREE COURSE ALERT* 🆓")
    lines.append("")
    lines.append(f"🎓 *{name}*")

    if short_desc:
        lines.append(f"_{short_desc}_")

    lines.append("")

    if category or subcategory:
        cat_line = "🏷 *Category:* "
        if category:
            cat_line += f"#{str(category).replace(' ', '')}"
        if subcategory:
            cat_line += f" | {subcategory}"
        lines.append(cat_line)

    lines.append(f"🌐 *Language:* {language}")
    lines.append(f"🏫 *Platform:* {store}")

    meta_bits = []
    if lectures:
        meta_bits.append(f"📚 {lectures} lectures")
    if views:
        meta_bits.append(f"👀 {views} enrolled")
    if rating and float(rating) > 0:
        meta_bits.append(f"⭐ {rating}/5 rating")

    if meta_bits:
        lines.append(" | ".join(meta_bits))

    # PRICE BLOCK
    if sale_price == 0 or sale_price == 0.0:
        if price:
            lines.append(f"💰 *Price:* {price} → *Free* 🔥")
        else:
            lines.append("💰 *Price:* Free 🔥")
    else:
        lines.append(f"💰 *Price:* {price} → {sale_price}")

    lines.append("")
    lines.append("⏰ *ENROLL NOW – LIMITED ENROLLMENTS ONLY*")
    lines.append(f"[🔗 Enroll Here]({url})")

    output = "\n".join(lines)

    if len(output) > MAX_CAPTION:
        output = output[:MAX_CAPTION - 3] + "..."

    return output


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

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎓 Enroll Now", url=url)]
        ]
    )

    try:
        if image:
            await bot.send_photo(
                chat_id=channel,
                photo=image,
                caption=text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        else:
            await bot.send_message(
                chat_id=channel,
                text=text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )

        print(f"✔ Sent: {course.get('name')}")
        save_last_sent(last + 1)

    except Exception as e:
        print(f"❌ Failed to send course: {e}")
    finally:
        await bot.close()


# -------------------
# RUN
# -------------------
if __name__ == "__main__":
    asyncio.run(main())
