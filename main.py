import asyncio
import os
import json
import random
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.errors import SessionPasswordNeededError
from telethon.sync import TelegramClient as SyncClient
from telethon.sessions import StringSession
from telebot import TeleBot

# ===== تنظیمات =====
BOT_TOKEN = "توکن_ربات_اینجا"
ADMIN_ID = 5990546826
SESSIONS_DIR = "sessions"

FOSH_FILE = "fosh.json"
ENEMY_FILE = "enemy.json"
SILENT_FILE = "silent.json"

RESPONSE_DELAY = 3  # تاخیر پاسخ به دشمن
last_fosh_index = -1

# ===== پوشه‌ها و فایل‌ها =====
os.makedirs(SESSIONS_DIR, exist_ok=True)

def load_list(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_list(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

fosh_list = load_list(FOSH_FILE)
enemy_list = load_list(ENEMY_FILE)
silent_list = load_list(SILENT_FILE)

# ===== ربات ادمین برای مدیریت اکانت‌ها =====
bot = TeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start"])
def start_cmd(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    bot.reply_to(msg, "📌 سلام رئیس! برای اضافه کردن اکانت دستور /add رو بزن.")

@bot.message_handler(commands=["add"])
def add_account(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    bot.send_message(msg.chat.id, "📱 شماره اکانت رو با کد کشور بده (مثلا +989123456789):")
    bot.register_next_step_handler(msg, process_phone)

def process_phone(msg):
    phone = msg.text.strip()
    bot.send_message(msg.chat.id, "⌛ در حال ارسال کد ورود...")
    asyncio.create_task(login_account(phone))

async def login_account(phone):
    session_name = os.path.join(SESSIONS_DIR, phone.replace("+", ""))
    client = TelegramClient(session_name, api_id=YOUR_API_ID, api_hash="YOUR_API_HASH")
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        bot.send_message(ADMIN_ID, f"📩 کد ورود برای {phone} ارسال شد. کد رو بفرست:")
        code = await wait_for_code()
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            bot.send_message(ADMIN_ID, "🔐 این اکانت تایید دو مرحله‌ای داره. پسورد رو بفرست:")
            password = await wait_for_code()
            await client.sign_in(password=password)
    await client.disconnect()
    bot.send_message(ADMIN_ID, f"✅ اکانت {phone} اضافه شد.")

# منتظر ورودی از ادمین
async def wait_for_code():
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    def code_handler(msg):
        if msg.from_user.id == ADMIN_ID:
            future.set_result(msg.text.strip())
    bot.register_message_handler(code_handler)
    return await future

# ===== سلف برای همه اکانت‌ها =====
clients = []

async def start_self_clients():
    for file in os.listdir(SESSIONS_DIR):
        if file.endswith(".session"):
            session_path = os.path.join(SESSIONS_DIR, file)
            client = TelegramClient(session_path, YOUR_API_ID, "YOUR_API_HASH")
            await client.start()
            register_handlers(client)
            clients.append(client)
    await asyncio.gather(*[c.run_until_disconnected() for c in clients])

def to_fancy_numbers(text):
    fancy_digits = {
        "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
        "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", ":": ":"
    }
    return "".join(fancy_digits.get(ch, ch) for ch in text)

async def update_last_name_with_time(client):
    while True:
        now = datetime.now()
        fancy_time = to_fancy_numbers(now.strftime("%H:%M"))
        try:
            await client(UpdateProfileRequest(last_name=f"ᴹᴿ ⏰{fancy_time}"))
        except:
            pass
        await asyncio.sleep(300)

def register_handlers(client):
    @client.on(events.NewMessage(from_users=ADMIN_ID))
    async def admin_commands(event):
        global last_fosh_index, RESPONSE_DELAY

        text = event.raw_text.strip()
        lower = text.lower()

        if lower == ".دشمن":
            replied = await event.get_reply_message()
            if replied:
                uid = replied.sender_id
                if uid not in enemy_list:
                    enemy_list.append(uid)
                    save_list(ENEMY_FILE, enemy_list)
                    await event.edit("💀 دشمن اضافه شد!")
                else:
                    await event.edit("⚠️ قبلاً دشمن بوده.")
            return

        if lower == ".حذف":
            replied = await event.get_reply_message()
            if replied:
                uid = replied.sender_id
                if uid in enemy_list:
                    enemy_list.remove(uid)
                    save_list(ENEMY_FILE, enemy_list)
                    await event.edit("🗑 دشمن حذف شد!")
                else:
                    await event.edit("🚫 تو لیست دشمن نیست.")
            return

        if lower == ".خفه":
            replied = await event.get_reply_message()
            if replied:
                uid = replied.sender_id
                if uid not in silent_list:
                    silent_list.append(uid)
                    save_list(SILENT_FILE, silent_list)
                    await event.edit("🔇 زیپ دهنش کشیده شد!")
            return

        if lower == ".نوخفه":
            replied = await event.get_reply_message()
            if replied:
                uid = replied.sender_id
                if uid in silent_list:
                    silent_list.remove(uid)
                    save_list(SILENT_FILE, silent_list)
                    await event.edit("🔊 از خفه در اومد!")
            return

        if lower.startswith(".فحش "):
            new_fosh = text[6:].strip()
            if new_fosh and new_fosh not in fosh_list:
                fosh_list.append(new_fosh)
                save_list(FOSH_FILE, fosh_list)
                await event.edit("☑️ فحش اضافه شد!")
            return

        if lower == ".لیست دشمنان":
            msg = "💀 لیست دشمنان:\n" + "\n".join(map(str, enemy_list)) if enemy_list else "❌ خالی"
            await event.edit(msg)
            return

        if lower == ".لیست فحش ها":
            msg = "📝 لیست فحش‌ها:\n" + "\n".join(fosh_list) if fosh_list else "❌ خالی"
            await event.edit(msg)
            return

        if lower.startswith(".بمب "):
            try:
                count = int(text.split()[1])
            except:
                count = 5
            replied = await event.get_reply_message()
            if replied:
                uid = replied.sender_id
                for _ in range(count):
                    await event.respond(random.choice(fosh_list))
            await event.edit(f"💣 بمب {count} تایی ارسال شد!")
            return

        if lower == ".کمک":
            await event.edit(
                ".کمک\n.دشمن\n.حذف\n.خفه\n.نوخفه\n.بمب <تعداد>\n.فحش <متن>\n.لیست دشمنان\n.لیست فحش ها"
            )

    @client.on(events.NewMessage())
    async def auto_reply(event):
        global last_fosh_index
        if event.sender_id in enemy_list and fosh_list:
            last_fosh_index = (last_fosh_index + 1) % len(fosh_list)
            await asyncio.sleep(RESPONSE_DELAY)
            await event.reply(fosh_list[last_fosh_index])

        if event.sender_id in silent_list:
            await event.delete()

    @client.on(events.ChatAction)
    async def welcome(event):
        if event.user_joined or event.user_added:
            user = await event.get_user()
            fancy_time = to_fancy_numbers(datetime.now().strftime("%H:%M"))
            await event.reply(f"🔥 خوش اومدی {user.first_name} ⏰{fancy_time}")

    asyncio.create_task(update_last_name_with_time(client))

# ===== اجرای همه =====
async def main():
    asyncio.create_task(asyncio.to_thread(bot.polling, none_stop=True))
    await start_self_clients()

if __name__ == "__main__":
    asyncio.run(main())
