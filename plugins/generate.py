# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import traceback
from pyrogram.types import Message
from pyrogram import Client, filters
from asyncio.exceptions import TimeoutError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
from config import API_ID, API_HASH
from plugins.database import db

SESSION_STRING_SIZE = 351

@Client.on_message(filters.private & ~filters.forwarded & filters.command(["logout"]))
async def logout(client, message):
    user_data = await db.get_session(message.from_user.id)  
    if user_data is None:
        return 
    await db.set_session(message.from_user.id, session=None)  
    await message.reply("**Logout Successfully** ♦")

@Client.on_message(filters.private & ~filters.forwarded & filters.command(["login"]))
async def main(bot: Client, message: Message):
    user_data = await db.get_session(message.from_user.id)
    if user_data is not None:
        await message.reply("**Your Are Already Logged In. First /logout Your Old Session. Then Do Login.**")
        return 
    user_id = int(message.from_user.id)
    
    # Instead, prompt user to provide session string or authenticate separately
    session_input = await bot.ask(chat_id=user_id, text="<b>Send your Telegram session string</b>\n\n"
        "<b>How to get session string:</b>\n"
        "1. Run a user client (not bot) with your account\n"
        "2. Export the session string using <code>client.export_session_string()</code>\n"
        "3. Paste it here\n\n"
        "<b>Example:</b> <code>AQA...</code> (351+ characters)\n\n"
        "Enter /cancel to cancel")
    
    if session_input.text == '/cancel':
        return await session_input.reply('<b>Process cancelled !</b>')
    
    string_session = session_input.text.strip()
    
    # Validate session string format
    if len(string_session) < SESSION_STRING_SIZE:
        return await session_input.reply(f'<b>Invalid session string. It must be at least {SESSION_STRING_SIZE} characters long.</b>')
    
    try:
        uclient = Client(":memory:", session_string=string_session, api_id=API_ID, api_hash=API_HASH)
        await uclient.connect()
        
        # Get user info to verify session is valid
        user_info = await uclient.get_me()
        await uclient.disconnect()
        
        # Store the verified session
        user_data = await db.get_session(message.from_user.id)
        if user_data is None:
            await db.set_session(message.from_user.id, session=string_session)
        
        await bot.send_message(message.from_user.id, 
            f"<b>Account Login Successfully ✓</b>\n\n"
            f"<b>Account:</b> {user_info.first_name}\n"
            f"<b>Username:</b> @{user_info.username if user_info.username else 'N/A'}\n\n"
            f"If you get any error related to AUTH KEY, /logout first and /login again")
            
    except Exception as e:
        return await session_input.reply_text(f"<b>ERROR IN LOGIN:</b> <code>{str(e)}</code>\n\n"
            "<b>Please make sure:</b>\n"
            "- Session string is valid and not expired\n"
            "- You're using a USER account session, not a bot token")

# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
