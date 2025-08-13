import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.account import UpdateProfileRequest
from datetime import datetime
import json
import os
import random

api_id = 12701321
api_hash = "83995b97cd109d02c1ead50c9f6f5605"
admin_id = 5990546826
SESSION_NAME = "my_session"

# فایل‌ها برای ذخیره لیست‌ها
fosh_file = "fosh.json"
enemy_file = "enemy.json"

# تاخیر پیش‌فرض پاسخ به دشمن (ثانیه)
response_delay = 3

# تبدیل اعداد به فونت بالا
def to_fancy_numbers(text):
    fancy_digits = {
        "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
        "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", ":": ":"
    }
    return "".join(fancy_digits.get(ch, ch) for ch in text)

# لود لیست از فایل
def load_list(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# ذخیره لیست در فایل
def save_list(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# لود اولیه لیست‌ها
foshall_list = load_list(fosh_file)
enemyall_list = load_list(enemy_file)

# ایندکس آخرین فحش ارسال شده به دشمن (برای جلوگیری از تکرار)
last_fosh_index = -1

client = TelegramClient(SESSION_NAME, api_id, api_hash)

# آپدیت فامیلی با ساعت هر ۵ دقیقه
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
        await asyncio.sleep(300)  # ۵ دقیقه

@client.on(events.NewMessage())
async def handle_commands(event):
    global response_delay, last_fosh_index
    # فقط ادمین مجاز
    if event.sender_id != admin_id:
        return

    text = event.raw_text.strip()
    lower = text.lower()

    # اضافه کردن دشمن (ریپلای شده به کاربر)
    if lower == ".دشمن":
        replied = await event.get_reply_message()
        if not replied:
            await event.edit("❌ لطفا روی پیام کاربر ریپلای کنید.")
            return
        user_id = replied.sender_id
        if user_id in enemyall_list:
            await event.edit("⚠️ این کاربر قبلا دشمن ثبت شده بود.")
        else:
            enemyall_list.append(user_id)
            save_list(enemy_file, enemyall_list)
            await event.edit("✅ دشمن با موفقیت اضافه شد.")

    # حذف دشمن (ریپلای)
    elif lower == ".حذف":
        replied = await event.get_reply_message()
        if not replied:
            await event.edit("❌ لطفا روی پیام کاربر ریپلای کنید.")
            return
        user_id = replied.sender_id
        if user_id not in enemyall_list:
            await event.edit("⚠️ این کاربر در لیست دشمنان نیست.")
        else:
            enemyall_list.remove(user_id)
            save_list(enemy_file, enemyall_list)
            await event.edit("✅ دشمن با موفقیت حذف شد.")

    # نمایش لیست دشمنان
    elif lower == ".لیست دشمن":
        if not enemyall_list:
            await event.edit("لیست دشمنان خالی است.")
        else:
            msg = "💀 لیست دشمنان:\n"
            for uid in enemyall_list:
                try:
                    user = await client.get_entity(uid)
                    msg += f"- {user.first_name} (ID: {uid})\n"
                except:
                    msg += f"- [ID: {uid}] (حذف شده یا نامشخص)\n"
            await event.edit(msg)

    # افزودن فحش جدید
    elif lower.startswith(".فحش "):
        new_fosh = text[6:].strip()
        if not new_fosh:
            await event.edit("❌ لطفا یک فحش معتبر بعد از دستور وارد کنید.")
            return
        if new_fosh in foshall_list:
            await event.edit("⚠️ این فحش قبلا ثبت شده است.")
        else:
            foshall_list.append(new_fosh)
            save_list(fosh_file, foshall_list)
            await event.edit(f"✅ فحش '{new_fosh}' با موفقیت اضافه شد.")

    # نمایش لیست فحش‌ها
    elif lower == ".لیست فحش":
        if not foshall_list:
            await event.edit("لیست فحش‌ها خالی است.")
        else:
            msg = "📝 لیست فحش‌ها:\n"
            for fosh in foshall_list:
                msg += f"- {fosh}\n"
            await event.edit(msg)

    # پاک کردن کل لیست دشمنان
    elif lower == ".پاکسازی دشمنان":
        enemyall_list.clear()
        save_list(enemy_file, enemyall_list)
        await event.edit("لیست دشمنان پاکسازی شد.")

    # پاک کردن کل فحش‌ها
    elif lower == ".پاکسازی فحش":
        foshall_list.clear()
        save_list(fosh_file, foshall_list)
        await event.edit("لیست فحش‌ها پاکسازی شد.")

    # تغییر تاخیر پاسخ
    elif lower.startswith(".تاخیر "):
        try:
            sec = int(text.split()[1])
            if sec < 0:
                await event.edit("❌ عدد وارد شده باید مثبت باشد.")
                return
            response_delay = sec
            await event.edit(f"⌛️ تاخیر پاسخ به {sec} ثانیه تنظیم شد.")
        except:
            await event.edit("❌ لطفا یک عدد صحیح بعد از دستور وارد کنید.")

    # کمک (دستورات)
    elif lower == ".کمک":
        help_text = (
            "📜 دستورات شیطانی 🔥:\n"
            ".دشمن (ریپلای) - اضافه کردن دشمن\n"
            ".حذف (ریپلای) - حذف دشمن\n"
            ".لیست دشمن - نمایش لیست دشمنان\n"
            ".فحش متن - افزودن فحش جدید\n"
            ".لیست فحش - نمایش فحش‌ها\n"
            ".پاکسازی دشمنان - حذف کل دشمنان\n"
            ".پاکسازی فحش - حذف کل فحش‌ها\n"
            ".تاخیر عدد - تنظیم تاخیر پاسخ (ثانیه)\n"
            ".کمک - دیدن این پیام\n"
        )
        await event.edit(help_text)

@client.on(events.NewMessage())
async def check_enemy_and_reply(event):
    global last_fosh_index, response_delay
    # نادیده گرفتن پیام‌های ادمین
    if event.sender_id == admin_id:
        return

    # اگر فرستنده دشمن باشه و فحش داریم
    if event.sender_id in enemyall_list and foshall_list:
        # انتخاب فحش بعدی بدون تکرار
        last_fosh_index += 1
        if last_fosh_index >= len(foshall_list):
            last_fosh_index = 0
        reply_text = foshall_list[last_fosh_index]

        # تایمر تاخیر پاسخ (مقدارش قابل تنظیم است)
        await asyncio.sleep(response_delay)
        await event.reply(reply_text)

@client.on(events.ChatAction)
async def welcome(event):
    if event.user_joined or event.user_added:
        user = await event.get_user()
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        fancy_time = to_fancy_numbers(time_str)

        first = user.first_name or ""
        last = user.last_name or ""

        if last:
            last = f"{last} ⏰{fancy_time}"
        else:
            last = ""

        welcome_text = f"🔥 خوش آمدی {first} {last}\n🔥 توسعه‌دهنده: arshiya_efootball"
        await event.reply(welcome_text)

async def main():
    await client.start()
    print("🦹‍♂️ اکانت شخصی شروع شد، در خدمتت هستم...")
    asyncio.create_task(update_last_name_with_time())
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
