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
    user_id = message.from_user.id
    active_account = await db.get_active_account(user_id)
    
    if active_account is None:
        return await message.reply("<b>You are not logged in.</b>") 
    
    await db.delete_account(active_account['account_id'])
    await message.reply(f"<b>Logged out from {active_account['account_name']} ✓</b>")

@Client.on_message(filters.private & ~filters.forwarded & filters.command(["login"]))
async def main(bot: Client, message: Message):
    user_id = int(message.from_user.id)
    
    name_msg = await bot.ask(chat_id=user_id, text="<b>Enter a name for this account</b>\n\n"
        "Example: Main Account, Work Account, etc.\n\n"
        "Enter /cancel to cancel")
    
    if name_msg.text == '/cancel':
        return await name_msg.reply('<b>Process cancelled !</b>')
    
    account_name = name_msg.text.strip()
    if not account_name:
        return await name_msg.reply('<b>Account name cannot be empty.</b>')
    
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
        
        account_id = await db.add_account(user_id, account_name, string_session)
        
        await bot.send_message(user_id, 
            f"<b>Account Login Successfully ✓</b>\n\n"
            f"<b>Account Name:</b> {account_name}\n"
            f"<b>Telegram Account:</b> {user_info.first_name}\n"
            f"<b>Username:</b> @{user_info.username if user_info.username else 'N/A'}\n\n"
            f"This account is now active. Use /changeid to switch between accounts.")
            
    except Exception as e:
        return await session_input.reply_text(f"<b>ERROR IN LOGIN:</b> <code>{str(e)}</code>\n\n"
            "<b>Please make sure:</b>\n"
            "- Session string is valid and not expired\n"
            "- You're using a USER account session, not a bot token")

# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
