import os
import json
import asyncio
from aiogram import Bot

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
    return open(CHANNEL_FILE).read().strip()

# Load last sent index safely
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

# Save last sent index
def save_last_sent(i):
    os.makedirs(os.path.dirname(LAST_SENT_FILE), exist_ok=True)
    with open(LAST_SENT_FILE, "w") as f:
        f.write(str(i))

# Load JSON data
def load_courses():
    if not os.path.exists(COUPONS_FILE):
        return []
    return json.load(open(COUPONS_FILE, "r", encoding="utf-8"))

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

    # Prepare message
    text = f"📚 *{course.get('name', 'No Title')}*\n\n"
    text += f"{course.get('description', '')}\n\n"
    text += f"[Enroll Here]({course.get('url', '#' )})"

    # Truncate caption if too long
    if len(text) > MAX_CAPTION:
        text = text[:MAX_CAPTION-3] + "..."

    image = course.get("image")

    # Send to Telegram
    try:
        if image:
            await bot.send_photo(
                chat_id=channel,
                photo=image,
                caption=text,
                parse_mode="Markdown"
            )
        else:
            await bot.send_message(
                chat_id=channel,
                text=text,
                parse_mode="Markdown"
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
