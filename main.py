import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.account import UpdateProfileRequest
from datetime import datetime
import json
import os

# تنظیمات اصلی
api_id = 12701321
api_hash = "83995b97cd109d02c1ead50c9f6f5605"
admin_id = 5990546826
SESSION_NAME = "my_session"

# فایل‌ها
fosh_file = "fosh.json"
enemy_file = "enemy.json"

# تاخیر پیش‌فرض
response_delay = 3

# تبدیل اعداد به فونت بالا
def to_fancy_numbers(text):
    fancy_digits = {
        "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
        "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", ":": ":"
    }
    return "".join(fancy_digits.get(ch, ch) for ch in text)

# لود لیست از فایل (با جلوگیری از خطا)
def load_list(filename):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except (json.JSONDecodeError, OSError):
        pass
    return []

# ذخیره لیست
def save_list(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[خطا ذخیره‌سازی] {filename}: {e}")

# لود اولیه
foshall_list = load_list(fosh_file)
enemyall_list = load_list(enemy_file)

last_fosh_index = -1
client = TelegramClient(SESSION_NAME, api_id, api_hash)

# آپدیت فامیلی هر ۵ دقیقه
async def update_last_name_with_time():
    while True:
        now = datetime.now()
        fancy_time = to_fancy_numbers(now.strftime("%H:%M"))
        new_last_name = f"ᴹᴿ ⏰{fancy_time}"
        try:
            await client(UpdateProfileRequest(last_name=new_last_name))
            print(f"🕒 فامیلی با ساعت {new_last_name} آپدیت شد")
        except Exception as e:
            print(f"❌ خطا در آپدیت فامیلی: {e}")
        await asyncio.sleep(300)

# دستورات ادمین
@client.on(events.NewMessage())
async def handle_commands(event):
    global response_delay, last_fosh_index
    if event.sender_id != admin_id:
        return

    text = event.raw_text.strip()
    lower = text.lower()

    if lower == ".دشمن":
        replied = await event.get_reply_message()
        if not replied:
            await event.edit("❌ لطفا روی پیام کاربر ریپلای کنید.")
            return
        uid = int(replied.sender_id)
        if uid not in enemyall_list:
            enemyall_list.append(uid)
            save_list(enemy_file, enemyall_list)
            await event.edit("✅ دشمن اضافه شد!")
        else:
            await event.edit("⚠️ قبلاً دشمن بوده.")

    elif lower == ".حذف":
        replied = await event.get_reply_message()
        if not replied:
            await event.edit("❌ لطفا روی پیام کاربر ریپلای کنید.")
            return
        uid = int(replied.sender_id)
        if uid in enemyall_list:
            enemyall_list.remove(uid)
            save_list(enemy_file, enemyall_list)
            await event.edit("✅ دشمن حذف شد.")
        else:
            await event.edit("⚠️ این کاربر دشمن نیست.")

    elif lower == ".لیست دشمن":
        if not enemyall_list:
            await event.edit("💀 لیست دشمنان خالی است.")
        else:
            msg = "💀 لیست دشمنان:\n"
            for uid in enemyall_list:
                try:
                    user = await client.get_entity(uid)
                    msg += f"- {user.first_name} (ID: {uid})\n"
                except:
                    msg += f"- [ID: {uid}]\n"
            await event.edit(msg)

    elif lower.startswith(".فحش "):
        new_fosh = text[6:].strip()
        if new_fosh and new_fosh not in foshall_list:
            foshall_list.append(new_fosh)
            save_list(fosh_file, foshall_list)
            await event.edit("☑️ فحش اضافه شد!")
        else:
            await event.edit("⚠️ قبلاً اضافه شده یا نامعتبر.")

    elif lower == ".لیست فحش":
        if not foshall_list:
            await event.edit("📭 لیست فحش‌ها خالی است.")
        else:
            msg = "📝 لیست فحش‌ها:\n" + "\n".join(f"- {f}" for f in foshall_list)
            await event.edit(msg)

    elif lower == ".پاکسازی دشمنان":
        enemyall_list.clear()
        save_list(enemy_file, enemyall_list)
        await event.edit("🧹 لیست دشمنان پاک شد.")

    elif lower == ".پاکسازی فحش":
        foshall_list.clear()
        save_list(fosh_file, foshall_list)
        await event.edit("🧹 لیست فحش‌ها پاک شد.")

    elif lower.startswith(".تاخیر "):
        try:
            sec = int(text.split()[1])
            if sec >= 0:
                response_delay = sec
                await event.edit(f"⌛ تاخیر روی {sec} ثانیه تنظیم شد.")
            else:
                await event.edit("❌ عدد باید مثبت باشد.")
        except:
            await event.edit("❌ عدد نامعتبر.")

    elif lower == ".کمک":
        await event.edit(
            "📜 دستورات:\n"
            ".دشمن (ریپلای)\n.حذف (ریپلای)\n.لیست دشمن\n"
            ".فحش متن\n.لیست فحش\n.پاکسازی دشمنان\n.پاکسازی فحش\n"
            ".تاخیر عدد\n.کمک"
        )

# جواب به دشمن
@client.on(events.NewMessage())
async def check_enemy_and_reply(event):
    global last_fosh_index
    if event.sender_id == admin_id:
        return
    if event.sender_id in enemyall_list and foshall_list:
        last_fosh_index = (last_fosh_index + 1) % len(foshall_list)
        await asyncio.sleep(response_delay)
        await event.reply(foshall_list[last_fosh_index])

# پیام خوش‌آمد
@client.on(events.ChatAction)
async def welcome(event):
    if event.user_joined or event.user_added:
        user = await event.get_user()
        fancy_time = to_fancy_numbers(datetime.now().strftime("%H:%M"))
        name = user.first_name or ""
        welcome_text = f"🔥 خوش آمدی {name} ⏰{fancy_time}\n🔥 توسعه‌دهنده: arshiya_efootball"
        await event.reply(welcome_text)

# شروع
async def main():
    await client.start()
    print("✅ ربات شخصی فعال شد")
    asyncio.create_task(update_last_name_with_time())
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
