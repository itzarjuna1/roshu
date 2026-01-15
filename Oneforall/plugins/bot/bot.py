import os
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.zipper import zip_file, zip_with_password, zip_multiple_files
from utils.unzipper import unzip_file
from utils.password_gen import generate_password

# Load environment variables
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 7487670897

app = Client("MultiBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_files = {}
session_messages = {}
session_tasks = {}
session_timers = {}

# Helper: clear session
async def clear_session(user_id):
    print(f"[CLEAR] Clearing session for {user_id}")
    if user_id in session_messages:
        for msg in session_messages[user_id]:
            try:
                await msg.delete()
            except Exception as e:
                print(f"[CLEAR ERROR] {e}")
        session_messages.pop(user_id, None)
    user_files.pop(user_id, None)
    session_tasks.pop(user_id, None)
    session_timers.pop(user_id, None)

    try:
        await app.send_message(
            user_id,
            "🧹 Your session has been cleared due to timeout.\n"
            "🔐 You can unzip files later using your password.\n"
            "Send /start to begin again."
        )
    except Exception as e:
        print(f"[DM FAILED] {e}")

# Timer
async def schedule_clear(user_id, duration):
    await asyncio.sleep(duration * 60)
    await clear_session(user_id)

async def reset_timer(user_id, duration=15):
    if user_id in session_tasks:
        try:
            session_tasks[user_id].cancel()
        except:
            pass
    task = asyncio.create_task(schedule_clear(user_id, duration))
    session_tasks[user_id] = task
    session_timers[user_id] = duration

# Start
@app.on_message(filters.command("start"))
async def start(_, msg):
    user_id = msg.from_user.id
    reply = await msg.reply(
        "👋 Welcome to Multi-Zip Bot!\n\n"
        "📂 Send files, then use:\n"
        "➔ /zip - Basic zip\n"
        "➔ /zip_pwd <password> - Zip with password\n"
        "➔ /unzip <password> - Unzip file\n"
        "➔ /zip_multi - Zip all uploaded files\n"
        "➔ /genpwd <length> - Generate password\n\n"
        f"⏳ This session will auto-clear in {session_timers.get(user_id,15)} minutes."
    )
    session_messages.setdefault(user_id, []).append(reply)
    await reset_timer(user_id)

# Reset
@app.on_message(filters.command("reset"))
async def reset_session(_, msg):
    user_id = msg.from_user.id
    await clear_session(user_id)

# Extend
@app.on_message(filters.command("extend"))
async def extend(_, msg):
    if msg.from_user.id != OWNER_ID:
        return await msg.reply("❌ You aren't allowed.")
    if len(msg.command) < 2:
        return await msg.reply("❗ Usage: /extend <minutes>")
    try:
        minutes = int(msg.command[1])
        user_id = msg.reply_to_message.from_user.id if msg.reply_to_message else msg.from_user.id
        new_time = session_timers.get(user_id, 15) + minutes
        await reset_timer(user_id, new_time)
        await msg.reply(f"✅ Extended session to {new_time} mins for user {user_id}.")
    except:
        await msg.reply("❗ Invalid time.")

# Reduce
@app.on_message(filters.command("reduce"))
async def reduce(_, msg):
    if msg.from_user.id != OWNER_ID:
        return await msg.reply("❌ You aren't allowed.")
    if len(msg.command) < 2:
        return await msg.reply("❗ Usage: /reduce <minutes>")
    try:
        minutes = int(msg.command[1])
        user_id = msg.reply_to_message.from_user.id if msg.reply_to_message else msg.from_user.id
        current = session_timers.get(user_id, 15)
        new_time = max(1, current - minutes)
        await reset_timer(user_id, new_time)
        await msg.reply(f"✅ Reduced session to {new_time} mins for user {user_id}.")
    except:
        await msg.reply("❗ Invalid time.")

# Password Generator
@app.on_message(filters.command("genpwd"))
async def genpwd(_, msg):
    if len(msg.command) < 2:
        return await msg.reply("❗ Usage: /genpwd <length>")
    try:
        length = int(msg.command[1])
        password = generate_password(length)
        reply = await msg.reply(f"🔐 Password: `{password}`", quote=True)
        session_messages.setdefault(msg.from_user.id, []).append(reply)
    except:
        await msg.reply("❗ Invalid number.")

# Uploads
@app.on_message(filters.document)
async def handle_docs(_, msg):
    user_id = msg.from_user.id
    path = await msg.download()
    user_files.setdefault(user_id, []).append(path)
    reply = await msg.reply("✅ File saved. Now use /zip, /zip_pwd, /zip_multi or /unzip", quote=True)
    session_messages.setdefault(user_id, []).append(reply)
    await reset_timer(user_id)

# /zip
@app.on_message(filters.command("zip"))
async def zip_cmd(_, msg):
    if not msg.reply_to_message or not msg.reply_to_message.document:
        return await msg.reply("❗ Reply to a file with /zip")
    path = await msg.reply_to_message.download()
    zip_path = zip_file(path)
    reply = await msg.reply_document(
        zip_path,
        caption="✅ Zipped file",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📅 Download", url="https://t.me/")]])
    )
    session_messages.setdefault(msg.from_user.id, []).append(reply)
    os.remove(zip_path)
    os.remove(path)
    await reset_timer(msg.from_user.id)

# /zip_pwd
@app.on_message(filters.command("zip_pwd"))
async def zip_pwd(_, msg):
    if len(msg.command) < 2:
        return await msg.reply("❗ Usage: /zip_pwd <password>")
    if not msg.reply_to_message or not msg.reply_to_message.document:
        return await msg.reply("❗ Reply to a file with /zip_pwd <password>")

    password = msg.command[1]
    path = await msg.reply_to_message.download()
    zip_path = zip_with_password(path, password)

    reply = await msg.reply_document(
        zip_path,
        caption="🔐 Password-protected zip created",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📅 Download", url="https://t.me/")]])
    )

    try:
        await app.send_message(msg.from_user.id, f"🔑 Password: `{password}`")
    except:
        await msg.reply("⚠️ Couldn't send DM. Make sure bot is unblocked.")

    session_messages.setdefault(msg.from_user.id, []).append(reply)
    os.remove(zip_path)
    os.remove(path)
    await reset_timer(msg.from_user.id)

# /zip_multi
@app.on_message(filters.command("zip_multi"))
async def zip_multi(_, msg):
    user_id = msg.from_user.id
    if user_id not in user_files or not user_files[user_id]:
        return await msg.reply("❗ No files found. Upload files first.")

    zip_path = zip_multiple_files(user_files[user_id])
    reply = await msg.reply_document(
        zip_path,
        caption="📆 Multi-file zip ready",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📅 Download", url="https://t.me/")]])
    )
    for f in user_files[user_id]:
        os.remove(f)
    os.remove(zip_path)
    user_files[user_id] = []
    session_messages.setdefault(user_id, []).append(reply)
    await reset_timer(user_id)

# /unzip
@app.on_message(filters.command("unzip"))
async def unzip_cmd(_, msg):
    if not msg.reply_to_message or not msg.reply_to_message.document:
        return await msg.reply("❗ Reply to a .zip file with /unzip <password>")

    password = msg.command[1] if len(msg.command) > 1 else None
    zip_path = await msg.reply_to_message.download()

    out_files = unzip_file(zip_path, password)

    if isinstance(out_files, str):
        await msg.reply(out_files)
    else:
        for file in out_files:
            try:
                reply = await msg.reply_document(file, caption="✅ Unzipped File")
                session_messages.setdefault(msg.from_user.id, []).append(reply)
                os.remove(file)
            except Exception as e:
                await msg.reply(f"⚠️ Failed to send file: {e}")

    os.remove(zip_path)
    await reset_timer(msg.from_user.id)

# Run
app.run()