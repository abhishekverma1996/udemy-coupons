import os
import json
from aiogram import Bot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_FILE = "scraper/channel_id.txt"
LAST_SENT_FILE = "scraper/last_sent.txt"
COUPONS_FILE = "website/coupons.json"

# Load channel
def load_channel():
    if not os.path.exists(CHANNEL_FILE):
        return None
    return open(CHANNEL_FILE).read().strip()

# Load last sent index
def load_last_sent():
    if not os.path.exists(LAST_SENT_FILE):
        return 0
    return int(open(LAST_SENT_FILE).read().strip())

# Save last sent index
def save_last_sent(i):
    with open(LAST_SENT_FILE, "w") as f:
        f.write(str(i))

# Load JSON
def load_courses():
    if not os.path.exists(COUPONS_FILE):
        return []
    return json.load(open(COUPONS_FILE, "r", encoding="utf-8"))

async def main():
    channel = load_channel()
    if not channel:
        print("Channel not set")
        return

    last = load_last_sent()
    courses = load_courses()

    if last >= len(courses):
        print("No new courses.")
        return

    course = courses[last]
    bot = Bot(token=BOT_TOKEN)

    text = f"📚 *{course.get('name')}*\n\n{course.get('description')}\n\n[Enroll Here]({course.get('url')})"
    image = course.get("image")

    if image:
        await bot.send_photo(chat_id=channel, photo=image, caption=text, parse_mode="Markdown")
    else:
        await bot.send_message(chat_id=channel, text=text, parse_mode="Markdown")

    print(f"Sent: {course.get('name')}")

    save_last_sent(last + 1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
