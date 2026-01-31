from pyrogram import filters, enums
from pyrogram.types import ChatMemberUpdated
from Oneforall import app
from logging import getLogger

LOGGER = getLogger(__name__)

POLITE_LEFT = """
⸻⬫⸺〈🌸 𝐆ᴏᴏᴅʙʏᴇ 🌸〉⸺⬫⸻

👤 𝐍ᴀᴍᴇ      » {name}
🆔 𝐈ᴅ        » {id}
🔖 𝐔ꜱᴇʀɴᴀᴍᴇ » {username}

✨ 𝐓ʜᴀɴᴋ 𝐘ᴏᴜ 𝐅ᴏʀ 𝐁ᴇɪɴɢ 𝐖ɪᴛʜ 𝐔ꜱ  
🌷 𝐘ᴏᴜ’ʟʟ 𝐀ʟᴡᴀʏ𝐬 𝐁ᴇ 𝐖ᴇʟᴄᴏᴍᴇ 𝐁ᴀᴄᴋ
"""

MERCIFUL_KICK = """
⸻⬫⸺〈🕊️ 𝐅ᴀʀᴇᴡᴇʟʟ 🕊️〉⸺⬫⸻

👤 𝐍ᴀᴍᴇ      » {name}
🆔 𝐈ᴅ        » {id}
🔖 𝐔ꜱᴇʀɴᴀᴍᴇ » {username}

🤍 𝐘ᴏᴜ 𝐖ᴇʀᴇ 𝐑ᴇᴍᴏᴠᴇᴅ 𝐅ᴏʀ 𝐀 𝐑ᴇᴀꜱᴏɴ  
✨ 𝐌ᴀʏ 𝐘ᴏᴜ 𝐅ɪɴᴅ 𝐀 𝐁ᴇᴛᴛᴇʀ 𝐏ᴀᴛʜ 𝐀ʜᴇᴀᴅ
"""

HARSH_BAN = """
⸻⬫⸺〈⛔ 𝐁ᴀɴɴᴇᴅ ⛔〉⸺⬫⸻

👤 𝐍ᴀᴍᴇ      » {name}
🆔 𝐈ᴅ        » {id}
🔖 𝐔ꜱᴇʀɴᴀᴍᴇ » {username}

⚠️ 𝐘ᴏᴜ 𝐕ɪᴏʟᴀᴛᴇᴅ 𝐆ʀᴏᴜᴘ 𝐑ᴜʟᴇꜱ  
🚫 𝐀ᴄᴄᴇꜱꜱ 𝐏ᴇʀᴍᴀɴᴇɴᴛʟʏ 𝐑ᴇᴠᴏᴋᴇᴅ
"""

@app.on_chat_member_updated(filters.group, group=-3)
async def goodbye_handler(_, member: ChatMemberUpdated):

    if not member.old_chat_member:
        return

    old = member.old_chat_member.status
    new = member.new_chat_member.status if member.new_chat_member else None

    user = member.old_chat_member.user
    chat = member.chat

    name = user.first_name or "Unknown"
    username = f"@{user.username}" if user.username else "None"

    # 1️⃣ User LEFT voluntarily
    if old in {enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.RESTRICTED} and new == enums.ChatMemberStatus.LEFT:
        text = POLITE_LEFT.format(
            name=name,
            id=user.id,
            username=username
        )

    # 2️⃣ User BANNED / KICKED
    elif old in {enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.RESTRICTED} and new == enums.ChatMemberStatus.BANNED:
        # Treat as kick by default, harsher tone for ban
        text = HARSH_BAN.format(
            name=name,
            id=user.id,
            username=username
        )

    else:
        return

    try:
        await app.send_message(chat.id, text, disable_web_page_preview=True)
    except Exception as e:
        LOGGER.error(e)
