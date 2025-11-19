import asyncio 
from pyrogram import Client, filters, enums
from config import LOG_CHANNEL, API_ID, API_HASH
from plugins.database import db
from plugins.link_changer import link_changer
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

LOG_TEXT = """<b>#NewUser
    
ID - <code>{}</code>

Nᴀᴍᴇ - {}</b>
"""

@Client.on_message(filters.command('start'))
async def start_message(c, m):
    if not await db.is_user_exist(m.from_user.id):
        await db.add_user(m.from_user.id, m.from_user.first_name)

    
    await m.reply_photo(f"https://te.legra.ph/file/119729ea3cdce4fefb6a1.jpg",
        caption=f"<b>Hello {m.from_user.mention} 👋\n\nI Am Public Link Auto-Changer Bot. I Can Automatically Change Your Channel Public Links.\n\nUse /help to see all commands.</b>",
        reply_markup=InlineKeyboardMarkup(
            [[
                InlineKeyboardButton('💝 sᴜʙsᴄʀɪʙᴇ ʏᴏᴜᴛᴜʙᴇ ᴄʜᴀɴɴᴇʟ', url='https://youtube.com/@Tech_VJ')
            ],[
                InlineKeyboardButton("❣️ ᴅᴇᴠᴇʟᴏᴘᴇʀ", url='https://t.me/Kingvj01'),
                InlineKeyboardButton("🤖 ᴜᴘᴅᴀᴛᴇ", url='https://t.me/VJ_Botz')
            ]]
        )
    )

@Client.on_message(filters.command('help') & filters.private)
async def help_command(client, message):
    help_text = """<b>📚 Available Commands:</b>

<b>/login</b> - Login with your Telegram account
<b>/logout</b> - Logout current account
<b>/logoutall</b> - Logout all accounts
<b>/changeid</b> - Switch between logged-in accounts

<b>/pubchannel</b> - Add channel for auto link rotation
  Usage: /pubchannel <channel_id> <base_username> <interval>
  Example: /pubchannel -1001234567890 mybase 3600

<b>/list</b> - Show all active channels
<b>/status</b> - Check current login status
<b>/showlogin</b> - Show logged in accounts

<b>/stop</b> - Stop link changing for a channel
  Usage: /stop <channel_id>

<b>/resume</b> - Resume link changing for a channel
  Usage: /resume <channel_id>

<b>Parameters:</b>
• channel_id: Your channel's ID (negative number)
• base_username: Base username without suffix (e.g., 'mybase')
• interval: Time in seconds between link changes (e.g., 3600 for 1 hour)
"""
    await message.reply(help_text)

@Client.on_message(filters.command('changeid') & filters.private)
async def change_account(client, message):
    user_id = message.from_user.id
    accounts = await db.get_user_accounts(user_id)
    
    if not accounts:
        await message.reply("<b>You have no logged-in accounts. Use /login to add an account.</b>")
        return
    
    if len(accounts) == 1:
        await message.reply("<b>You only have one account. Nothing to switch.</b>")
        return
    
    # Create inline buttons for each account
    buttons = []
    for i, account in enumerate(accounts, 1):
        buttons.append([InlineKeyboardButton(f"Account {i}: {account['account_name']}", callback_data=f"select_account_{account['account_id']}")])
    
    await message.reply(
        "<b>Select an account to activate:</b>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^select_account_"))
async def handle_account_selection(client, callback_query):
    account_id = callback_query.data.replace("select_account_", "")
    user_id = callback_query.from_user.id
    
    # Verify account belongs to user
    account = await db.get_account(account_id)
    if not account or account['user_id'] != user_id:
        await callback_query.answer("Invalid account!", show_alert=True)
        return
    
    # Set as active account
    await db.set_active_account(user_id, account_id)
    
    await callback_query.answer()
    await callback_query.edit_message_text(f"<b>✅ Switched to account: {account['account_name']}</b>")

@Client.on_message(filters.command('pubchannel') & filters.private)
async def add_pubchannel(client, message):
    try:
        parts = message.command
        if len(parts) < 4:
            await message.reply("<b>Usage: /pubchannel <channel_id> <base_username> <interval>\n\nExample: /pubchannel -1001234567890 mybase 3600</b>")
            return
        
        channel_id = int(parts[1])
        base_username = parts[2]
        interval = int(parts[3])
        
        user_id = message.from_user.id
        
        active_account = await db.get_active_account(user_id)
        
        if not active_account:
            await message.reply("<b>You must /login first before adding channels.</b>")
            return
        
        user_session = active_account['session']
        account_id = active_account['account_id']
        
        # Verify channel access
        try:
            from config import API_ID, API_HASH
            temp_client = Client(":memory:", session_string=user_session, api_id=API_ID, api_hash=API_HASH)
            await temp_client.connect()
            chat = await temp_client.get_chat(channel_id)
            await temp_client.disconnect()
        except Exception as e:
            await message.reply(f"<b>Error accessing channel:</b> {str(e)}\n\n<b>Make sure you're admin in the channel with rights to change username.</b>")
            return
        
        await db.add_channel(user_id, account_id, channel_id, base_username, interval)
        
        # Start rotation
        success, result = await link_changer.start_channel_rotation(user_id, account_id, channel_id, base_username, interval)
        
        if success:
            await message.reply(f"<b>✅ Channel added successfully!\n\nChannel ID: {channel_id}\nBase Username: {base_username}\nInterval: {interval}s\n\nLink rotation started!</b>")
        else:
            await message.reply(f"<b>❌ Error starting rotation:</b> {result}")
    except ValueError:
        await message.reply("<b>Invalid parameters. Make sure channel_id and interval are numbers.</b>")
    except Exception as e:
        await message.reply(f"<b>Error:</b> {str(e)}")

@Client.on_message(filters.command('list') & filters.private)
async def list_channels(client, message):
    user_id = message.from_user.id
    active_account = await db.get_active_account(user_id)
    
    if not active_account:
        await message.reply("<b>You must login first.</b>")
        return
    
    channels = await db.get_user_channels(user_id, active_account['account_id'])
    
    if not channels:
        await message.reply("<b>You have no active channels. Use /pubchannel to add one.</b>")
        return
    
    text = f"<b>📋 Your Active Channels ({active_account['account_name']}):\n\n</b>"
    for i, ch in enumerate(channels, 1):
        text += f"<b>{i}. Channel ID:</b> <code>{ch['channel_id']}</code>\n"
        text += f"   <b>Base Username:</b> {ch['base_username']}\n"
        text += f"   <b>Interval:</b> {ch['interval']}s\n"
        text += f"   <b>Status:</b> {'🟢 Active' if ch['is_active'] else '🔴 Stopped'}\n\n"
    
    await message.reply(text)

@Client.on_message(filters.command('status') & filters.private)
async def status_command(client, message):
    user_id = message.from_user.id
    active_account = await db.get_active_account(user_id)
    
    if active_account:
        await message.reply(f"<b>✅ You are logged in as: {active_account['account_name']}\n\nReady to use the bot.</b>")
    else:
        await message.reply("<b>❌ You are not logged in. Use /login to get started.</b>")

@Client.on_message(filters.command('showlogin') & filters.private)
async def show_login(client, message):
    user_id = message.from_user.id
    accounts = await db.get_user_accounts(user_id)
    
    if not accounts:
        await message.reply("<b>No logged-in accounts.</b>")
        return
    
    active_account = await db.get_active_account(user_id)
    text = f"<b>👥 Your Logged In Accounts ({len(accounts)}):\n\n</b>"
    
    for i, account in enumerate(accounts, 1):
        marker = "✅" if active_account and account['account_id'] == active_account['account_id'] else "  "
        text += f"{marker} {i}. {account['account_name']}\n"
    
    await message.reply(text)

@Client.on_message(filters.command('stop') & filters.private)
async def stop_channel(client, message):
    try:
        parts = message.command
        if len(parts) < 2:
            await message.reply("<b>Usage: /stop <channel_id></b>")
            return
        
        channel_id = int(parts[1])
        user_id = message.from_user.id
        active_account = await db.get_active_account(user_id)
        
        if not active_account:
            await message.reply("<b>You must login first.</b>")
            return
        
        success, result = await link_changer.stop_channel_rotation(user_id, active_account['account_id'], channel_id)
        
        if success:
            await db.stop_channel(channel_id)
            await message.reply(f"<b>✅ Link rotation stopped for channel {channel_id}</b>")
        else:
            await message.reply(f"<b>❌ Error:</b> {result}")
    except ValueError:
        await message.reply("<b>Invalid channel ID.</b>")
    except Exception as e:
        await message.reply(f"<b>Error:</b> {str(e)}")

@Client.on_message(filters.command('resume') & filters.private)
async def resume_channel(client, message):
    try:
        parts = message.command
        if len(parts) < 2:
            await message.reply("<b>Usage: /resume <channel_id></b>")
            return
        
        channel_id = int(parts[1])
        user_id = message.from_user.id
        active_account = await db.get_active_account(user_id)
        
        if not active_account:
            await message.reply("<b>You must login first.</b>")
            return
        
        channel = await db.get_channel(channel_id)
        if not channel:
            await message.reply("<b>Channel not found.</b>")
            return
        
        success, result = await link_changer.resume_channel_rotation(
            user_id, 
            active_account['account_id'],
            channel_id, 
            channel['base_username'], 
            channel['interval']
        )
        
        if success:
            await db.resume_channel(channel_id)
            await message.reply(f"<b>✅ Link rotation resumed for channel {channel_id}</b>")
        else:
            await message.reply(f"<b>❌ Error:</b> {result}")
    except ValueError:
        await message.reply("<b>Invalid channel ID.</b>")
    except Exception as e:
        await message.reply(f"<b>Error:</b> {str(e)}")

@Client.on_message(filters.command('logoutall') & filters.private)
async def logout_all(client, message):
    user_id = message.from_user.id
    accounts = await db.get_user_accounts(user_id)
    count = len(accounts)
    
    for account in accounts:
        await db.delete_account(account['account_id'])
    
    await message.reply(f"<b>✅ Logged out {count} accounts.</b>")
