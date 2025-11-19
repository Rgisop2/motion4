from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
from plugins.link_changer import link_changer
from plugins.scheduler import scheduler
from plugins.database import db
import asyncio

class Bot(Client):

    def __init__(self):
        super().__init__(
        "vj link changer bot",
         api_id=API_ID,
         api_hash=API_HASH,
         bot_token=BOT_TOKEN,
         plugins=dict(root="plugins"),
         workers=50,
         sleep_threshold=10
        )

      
    async def start(self):
            
        await super().start()
        me = await self.get_me()
        self.username = '@' + me.username
        
        print('Bot Started Powered By @VJ_Botz')
        
        await scheduler.restore_all_schedules()
        await self.resume_all_channels()

    async def resume_all_channels(self):
        """Resume all active channels on bot startup"""
        try:
            channels = await db.get_all_active_channels()
            for channel in channels:
                user_id = channel['user_id']
                account_id = channel['account_id']
                channel_id = channel['channel_id']
                base_username = channel['base_username']
                interval = channel['interval']
                
                success, result = await link_changer.start_channel_rotation(
                    user_id,
                    account_id,
                    channel_id, 
                    base_username, 
                    interval
                )
                if success:
                    print(f"[v0] Resumed channel rotation for {channel_id} (Account: {account_id})")
                else:
                    print(f"[v0] Failed to resume channel {channel_id}: {result}")
        except Exception as e:
            print(f"[v0] Error resuming channels: {e}")

    async def stop(self, *args):

        await super().stop()
        print('Bot Stopped Bye')

Bot().run()
