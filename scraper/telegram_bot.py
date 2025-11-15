import os
import json
import asyncio
from aiogram import Bot

# -------------------
# CONFIG
# -------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_FILE = "scraper/channel_id.txt"
LAST_SENT_FILE = "scraper/last_sent.txt"
COUPONS_FILE = "website/coupons.json"

# -------------------
# HELPER FUNCTIONS
# -------------------

def load_channel():
    if not os.path.exists(CHANNEL_FILE):
        return None
    return open(CHANNEL_FILE, "r", encoding="utf-8").read().strip()

def load_last_sent():
    if not os.path.exists(LAST_SENT_FILE):
        return 0
    try:
        content = open(LAST_SENT_FILE, "r", encoding="utf-8").read().strip()
        return int(content) if content else 0
    except:
        return 0

def save_last_sent(i):
    os.makedirs(os.path.dirname(LAST_SENT_FILE), exist_ok=True)
    with open(LAST_SENT_FILE, "w", encoding="utf-8") as f:
        f.write(str(i))

def load_courses():
    if not os.path.exists(COUPONS_FILE):
        return []
    with open(COUPONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------
# MAIN LOGIC
# -------------------

async def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set! Add it to GitHub Secrets.")
        return

    channel = load_channel()
    if not channel:
        print("❌ Channel not set. Add a channel to channel_id.txt")
        return

    last_sent = load_last_sent()
    courses = load_courses()

    if last_sent >= len(courses):
        print("✔ No new courses to send.")
        return

    course = courses[last_sent]

    try:
        bot = Bot(token=BOT_TOKEN)
    except Exception as e:
        print(f"❌ Failed to create bot: {e}")
        return

    text = f"📚 *{course.get('name', 'No Title')}*\n\n"
    text += f"{course.get('description', '')}\n\n"
    text += f"[Enroll Here]({course.get('url', '#' )})"
    image = course.get("image")

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
        save_last_sent(last_sent + 1)
    except Exception as e:
        print(f"❌ Failed to send course: {e}")
    finally:
        await bot.close()

# -------------------
# RUN
# -------------------
if __name__ == "__main__":
    asyncio.run(main())
