import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.account import UpdateProfileRequest
from datetime import datetime
import json
import os

# --- تنظیمات ---
api_id = 12701321
api_hash = "83995b97cd109d02c1ead50c9f6f5605"
admin_id = 5990546826
SESSION_NAME = "my_session"

# فایل‌ها
fosh_file = "fosh.json"
enemy_file = "enemy.json"
mute_file = "mute.json"

response_delay = 3

# --- مدیریت فایل‌ها ---
def load_list(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_list(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

foshall_list = load_list(fosh_file)
enemyall_list = load_list(enemy_file)
mute_list = load_list(mute_file)

last_fosh_index = -1

client = TelegramClient(SESSION_NAME, api_id, api_hash)

# --- آپدیت فامیلی با ساعت ---
async def update_last_name_with_time():
    while True:
        now = datetime.now().strftime("%H:%M")
        try:
            await client(UpdateProfileRequest(last_name=f"ᴹᴿ ⏰{now}"))
        except Exception as e:
            print(f"❌ خطا در آپدیت فامیلی: {e}")
        await asyncio.sleep(300)

# --- دستورات ---
@client.on(events.NewMessage())
async def handle_commands(event):
    global response_delay, last_fosh_index
    if event.sender_id != admin_id:
        return

    text = event.raw_text.strip()
    lower = text.lower()

    # حالت خفه
    if lower == ".خفه":
        replied = await event.get_reply_message()
        if not replied:
            await event.edit("❌ روی پیام کسی ریپلای کن.")
            return
        user_id = replied.sender_id
        if user_id in mute_list:
            await event.edit("⚠️ این کاربر از قبل خفه بود.")
        else:
            mute_list.append(user_id)
            save_list(mute_file, mute_list)
            await event.edit("✅ کاربر خفه شد.")

    elif lower == ".باز":
        replied = await event.get_reply_message()
        if not replied:
            await event.edit("❌ روی پیام کسی ریپلای کن.")
            return
        user_id = replied.sender_id
        if user_id not in mute_list:
            await event.edit("⚠️ این کاربر خفه نیست.")
        else:
            mute_list.remove(user_id)
            save_list(mute_file, mute_list)
            await event.edit("✅ کاربر آزاد شد.")

    # حالت بمب سرعتی
    elif lower.startswith(".بمب "):
        try:
            parts = text.split(maxsplit=2)
            count = int(parts[1])
            if count <= 0:
                await event.edit("❌ عدد باید مثبت باشه.")
                return
            if len(parts) < 3:
                await event.edit("❌ متن رو بعد از عدد بنویس.")
                return
            spam_text = parts[2]
            replied = await event.get_reply_message()
            await event.edit(f"💣 در حال ارسال {count} پیام...")

            tasks = []
            for _ in range(count):
                if replied:
                    tasks.append(asyncio.create_task(event.respond(spam_text, reply_to=replied.id)))
                else:
                    tasks.append(asyncio.create_task(event.respond(spam_text)))

            await asyncio.gather(*tasks)
        except Exception as e:
            await event.edit(f"❌ خطا: {e}")

    # دشمن و فحش‌ها
    elif lower == ".دشمن":
        replied = await event.get_reply_message()
        if not replied:
            await event.edit("❌ روی پیام کسی ریپلای کن.")
            return
        user_id = replied.sender_id
        if user_id in enemyall_list:
            await event.edit("⚠️ این کاربر از قبل دشمن بود.")
        else:
            enemyall_list.append(user_id)
            save_list(enemy_file, enemyall_list)
            await event.edit("✅ دشمن اضافه شد.")

    elif lower == ".حذف":
        replied = await event.get_reply_message()
        if not replied:
            await event.edit("❌ روی پیام کسی ریپلای کن.")
            return
        user_id = replied.sender_id
        if user_id not in enemyall_list:
            await event.edit("⚠️ این کاربر دشمن نیست.")
        else:
            enemyall_list.remove(user_id)
            save_list(enemy_file, enemyall_list)
            await event.edit("✅ دشمن حذف شد.")

    elif lower == ".لیست دشمن":
        if not enemyall_list:
            await event.edit("لیست دشمن خالیه.")
        else:
            try:
                await event.delete()
                await client.send_file(event.chat_id, enemy_file, caption="💀 لیست دشمن‌ها")
            except Exception as e:
                await event.respond(f"❌ خطا در ارسال فایل: {e}")

    elif lower.startswith(".فحش "):
        new_fosh = text[6:].strip()
        if not new_fosh:
            await event.edit("❌ فحش معتبر وارد کن.")
            return
        if new_fosh in foshall_list:
            await event.edit("⚠️ این فحش قبلا ثبت شده.")
        else:
            foshall_list.append(new_fosh)
            save_list(fosh_file, foshall_list)
            await event.edit(f"✅ '{new_fosh}' اضافه شد.")

    elif lower == ".لیست فحش":
        if not foshall_list:
            await event.edit("لیست فحش خالیه.")
        else:
            try:
                await event.delete()
                await client.send_file(event.chat_id, fosh_file, caption="📝 لیست فحش‌ها")
            except Exception as e:
                await event.respond(f"❌ خطا در ارسال فایل: {e}")

    elif lower == ".لیست خفه":
        if not mute_list:
            await event.edit("لیست خفه خالیه.")
        else:
            try:
                await event.delete()
                await client.send_file(event.chat_id, mute_file, caption="🔇 لیست خفه‌ها")
            except Exception as e:
                await event.respond(f"❌ خطا در ارسال فایل: {e}")

    elif lower.startswith(".تاخیر "):
        try:
            sec = int(text.split()[1])
            response_delay = sec
            await event.edit(f"⌛ تاخیر روی {sec} ثانیه تنظیم شد.")
        except:
            await event.edit("❌ عدد معتبر وارد کن.")

    elif lower == ".کمک":
        help_text = (
            "📜 دستورات:\n"
            ".خفه (ریپلای) - خفه کردن کاربر\n"
            ".باز (ریپلای) - آزاد کردن کاربر\n"
            ".بمب تعداد متن - اسپم سرعتی\n"
            ".دشمن (ریپلای) - اضافه کردن دشمن\n"
            ".حذف (ریپلای) - حذف دشمن\n"
            ".لیست دشمن - ارسال فایل دشمن‌ها\n"
            ".فحش متن - افزودن فحش\n"
            ".لیست فحش - ارسال فایل فحش‌ها\n"
            ".لیست خفه - ارسال فایل لیست خفه\n"
            ".تاخیر عدد - تنظیم تاخیر\n"
            ".کمک - این پیام\n"
        )
        await event.edit(help_text)

# --- حذف پیام‌های افراد خفه ---
@client.on(events.NewMessage())
async def mute_handler(event):
    if event.sender_id in mute_list:
        try:
            await event.delete()
        except:
            pass

# --- دشمن و فحش ---
@client.on(events.NewMessage())
async def check_enemy_and_reply(event):
    global last_fosh_index
    if event.sender_id == admin_id:
        return
    if event.sender_id in enemyall_list and foshall_list:
        last_fosh_index += 1
        if last_fosh_index >= len(foshall_list):
            last_fosh_index = 0
        reply_text = foshall_list[last_fosh_index]
        await asyncio.sleep(response_delay)
        await event.reply(reply_text)

# --- ران اصلی ---
async def main():
    await client.start()
    print("🦹‍♂️ بات روشن شد...")
    asyncio.create_task(update_last_name_with_time())
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
