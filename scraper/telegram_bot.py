import os
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# -------------------
# CONFIG
# -------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # GitHub secret
CHANNEL_FILE = "scraper/channel_id.txt"
LAST_SENT_FILE = "scraper/last_sent.txt"
COUPONS_FILE = "website/coupons.json"
SEND_INTERVAL = 300  # 5 minutes
# -------------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Save/load channel
def save_channel(channel_id):
    os.makedirs(os.path.dirname(CHANNEL_FILE), exist_ok=True)
    with open(CHANNEL_FILE, "w") as f:
        f.write(channel_id.strip())

def load_channel():
    if not os.path.exists(CHANNEL_FILE):
        return None
    with open(CHANNEL_FILE, "r") as f:
        return f.read().strip()

# Save/load last sent index
def save_last_sent(idx):
    os.makedirs(os.path.dirname(LAST_SENT_FILE), exist_ok=True)
    with open(LAST_SENT_FILE, "w") as f:
        f.write(str(idx))

def load_last_sent():
    if not os.path.exists(LAST_SENT_FILE):
        return 0
    with open(LAST_SENT_FILE, "r") as f:
        return int(f.read().strip())

# Load courses from JSON
def load_courses():
    if not os.path.exists(COUPONS_FILE):
        return []
    with open(COUPONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------
# Bot Handlers
# -------------------
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    channel = load_channel()
    if channel:
        await message.reply(f"Bot is configured. Current channel: {channel}")
    else:
        await message.reply(
            "Please send the channel username or ID where I should post updates.\n"
            "Example: @yourchannel or -1001234567890"
        )

@dp.message_handler(lambda msg: msg.text.startswith("@") or msg.text.startswith("-100"))
async def set_channel(message: types.Message):
    channel = message.text.strip()
    save_channel(channel)
    await message.reply(
        f"✔ Channel saved: `{channel}`\nMake sure bot is admin in the channel.",
        parse_mode="Markdown"
    )

# -------------------
# Scheduled Sender
# -------------------
async def scheduled_sender():
    await bot.wait_until_ready()
    while True:
        channel = load_channel()
        if not channel:
            print("No channel configured yet. Waiting for user to set it.")
            await asyncio.sleep(10)
            continue

        last_sent = load_last_sent()
        courses = load_courses()

        if last_sent < len(courses):
            course = courses[last_sent]
            text = f"📚 *{course.get('name')}*\n\n"
            text += f"{course.get('description')}\n\n"
            text += f"[Enroll Here]({course.get('url')})"
            image = course.get("image")

            try:
                if image:
                    await bot.send_photo(chat_id=channel, photo=image, caption=text, parse_mode="Markdown")
                else:
                    await bot.send_message(chat_id=channel, text=text, parse_mode="Markdown")
                print(f"Sent: {course.get('name')}")
            except Exception as e:
                print(f"Failed to send course: {e}")

            last_sent += 1
            save_last_sent(last_sent)
        else:
            print("No new courses to send.")

        await asyncio.sleep(SEND_INTERVAL)

# -------------------
# Main
# -------------------
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_sender())
    executor.start_polling(dp, skip_updates=True)
