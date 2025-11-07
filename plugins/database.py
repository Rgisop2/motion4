import motor.motor_asyncio
from config import DB_NAME, DB_URI

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.users_col = self.db.users
        self.channels_col = self.db.channels

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            session = None,
        )
    
    def new_channel(self, user_id, channel_id, base_username, interval):
        return dict(
            user_id = user_id,
            channel_id = channel_id,
            base_username = base_username,
            interval = interval,
            is_active = True,
            last_changed = None,
        )
    
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.users_col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.users_col.find_one({'id':int(id)})
        return bool(user)
    
    async def total_users_count(self):
        count = await self.users_col.count_documents({})
        return count

    async def get_all_users(self):
        return self.users_col.find({})

    async def delete_user(self, user_id):
        await self.users_col.delete_many({'id': int(user_id)})

    async def set_session(self, id, session):
        await self.users_col.update_one({'id': int(id)}, {'$set': {'session': session}})

    async def get_session(self, id):
        user = await self.users_col.find_one({'id': int(id)})
        return user['session'] if user else None

    async def add_channel(self, user_id, channel_id, base_username, interval):
        channel = self.new_channel(user_id, channel_id, base_username, interval)
        await self.channels_col.insert_one(channel)

    async def get_user_channels(self, user_id):
        return await self.channels_col.find({'user_id': int(user_id), 'is_active': True}).to_list(None)

    async def get_all_active_channels(self):
        return await self.channels_col.find({'is_active': True}).to_list(None)

    async def stop_channel(self, channel_id):
        await self.channels_col.update_one({'channel_id': int(channel_id)}, {'$set': {'is_active': False}})

    async def resume_channel(self, channel_id):
        await self.channels_col.update_one({'channel_id': int(channel_id)}, {'$set': {'is_active': True}})

    async def delete_channel(self, channel_id):
        await self.channels_col.delete_one({'channel_id': int(channel_id)})

    async def update_last_changed(self, channel_id, timestamp):
        await self.channels_col.update_one({'channel_id': int(channel_id)}, {'$set': {'last_changed': timestamp}})

    async def get_channel(self, channel_id):
        return await self.channels_col.find_one({'channel_id': int(channel_id)})

db = Database(DB_URI, DB_NAME)
  
