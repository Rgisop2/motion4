import motor.motor_asyncio
import asyncio
from config import DB_NAME, DB_URI

_db_write_lock = asyncio.Lock()

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri, maxPoolSize=100, minPoolSize=10, connectTimeoutMS=5000)
        self.db = self._client[database_name]
        self.users_col = self.db.users
        self.accounts_col = self.db.accounts
        self.channels_col = self.db.channels

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            active_account_id = None,  # Track which account user is currently using
            accounts = []  # List of account IDs for this user
        )
    
    def new_account(self, user_id, account_name, session):
        """Create a new account entry"""
        import uuid
        return dict(
            account_id = str(uuid.uuid4()),
            user_id = user_id,
            account_name = account_name,
            session = session,
            created_at = None,
        )
    
    def new_channel(self, user_id, account_id, channel_id, base_username, interval):
        return dict(
            user_id = user_id,
            account_id = account_id,  # Now tied to specific account
            channel_id = channel_id,
            base_username = base_username,
            interval = interval,
            is_active = True,
            last_changed = None,
            stop_schedule = None,  # Format: "HH:MM:SS"
            resume_schedule = None,  # Format: "HH:MM:SS"
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

    async def add_account(self, user_id, account_name, session):
        """Add a new account for a user"""
        account = self.new_account(user_id, account_name, session)
        await self.accounts_col.insert_one(account)
        
        # Add account_id to user's accounts list
        await self.users_col.update_one(
            {'id': int(user_id)},
            {'$push': {'accounts': account['account_id']}}
        )
        
        # If this is the first account, set it as active
        user = await self.users_col.find_one({'id': int(user_id)})
        if not user.get('active_account_id'):
            await self.users_col.update_one(
                {'id': int(user_id)},
                {'$set': {'active_account_id': account['account_id']}}
            )
        
        return account['account_id']
    
    async def get_user_accounts(self, user_id):
        """Get all accounts for a user"""
        return await self.accounts_col.find({'user_id': int(user_id)}).to_list(None)
    
    async def get_account(self, account_id):
        """Get account by ID"""
        return await self.accounts_col.find_one({'account_id': account_id})
    
    async def set_active_account(self, user_id, account_id):
        """Set the active account for a user"""
        await self.users_col.update_one(
            {'id': int(user_id)},
            {'$set': {'active_account_id': account_id}}
        )
    
    async def get_active_account(self, user_id):
        """Get the currently active account for a user"""
        user = await self.users_col.find_one({'id': int(user_id)})
        if not user or not user.get('active_account_id'):
            return None
        return await self.get_account(user['active_account_id'])
    
    async def get_active_account_session(self, user_id):
        """Get session string of active account"""
        account = await self.get_active_account(user_id)
        return account['session'] if account else None
    
    async def delete_account(self, account_id):
        """Delete an account and its channels"""
        account = await self.get_account(account_id)
        if not account:
            return
        
        user_id = account['user_id']
        
        # Delete all channels for this account
        await self.channels_col.delete_many({'account_id': account_id})
        
        # Remove account from user's accounts list
        await self.users_col.update_one(
            {'id': int(user_id)},
            {'$pull': {'accounts': account_id}}
        )
        
        # If deleted account was active, set next account as active
        user = await self.users_col.find_one({'id': int(user_id)})
        if user.get('active_account_id') == account_id:
            accounts = await self.get_user_accounts(user_id)
            if accounts:
                await self.set_active_account(user_id, accounts[0]['account_id'])
            else:
                await self.users_col.update_one(
                    {'id': int(user_id)},
                    {'$set': {'active_account_id': None}}
                )
        
        # Delete the account
        await self.accounts_col.delete_one({'account_id': account_id})

    async def set_session(self, id, session):
        """Deprecated: use add_account instead"""
        account = await self.get_active_account(id)
        if account:
            await self.accounts_col.update_one(
                {'account_id': account['account_id']},
                {'$set': {'session': session}}
            )

    async def get_session(self, id):
        """Deprecated: use get_active_account_session instead"""
        return await self.get_active_account_session(id)

    async def add_channel(self, user_id, account_id, channel_id, base_username, interval):
        async with _db_write_lock:
            channel = self.new_channel(user_id, account_id, channel_id, base_username, interval)
            await self.channels_col.insert_one(channel)

    async def get_user_channels(self, user_id, account_id=None):
        """Get channels for a user, optionally filtered by account"""
        if account_id:
            return await self.channels_col.find({'user_id': int(user_id), 'account_id': account_id, 'is_active': True}).to_list(None)
        else:
            return await self.channels_col.find({'user_id': int(user_id), 'is_active': True}).to_list(None)

    async def get_all_active_channels(self):
        return await self.channels_col.find({'is_active': True}).to_list(None)

    async def stop_channel(self, channel_id):
        async with _db_write_lock:
            await self.channels_col.update_one({'channel_id': int(channel_id)}, {'$set': {'is_active': False}})

    async def resume_channel(self, channel_id):
        async with _db_write_lock:
            await self.channels_col.update_one({'channel_id': int(channel_id)}, {'$set': {'is_active': True}})

    async def delete_channel(self, channel_id):
        async with _db_write_lock:
            await self.channels_col.delete_one({'channel_id': int(channel_id)})

    async def update_last_changed(self, channel_id, timestamp):
        for attempt in range(3):
            try:
                async with _db_write_lock:
                    await self.channels_col.update_one({'channel_id': int(channel_id)}, {'$set': {'last_changed': timestamp}})
                break
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
                else:
                    raise

    async def get_channel(self, channel_id):
        return await self.channels_col.find_one({'channel_id': int(channel_id)})

    async def set_channel_schedule(self, channel_id, stop_time, resume_time):
        async with _db_write_lock:
            await self.channels_col.update_one(
                {'channel_id': int(channel_id)},
                {'$set': {'stop_schedule': stop_time, 'resume_schedule': resume_time}}
            )

    async def remove_channel_schedule(self, channel_id):
        async with _db_write_lock:
            await self.channels_col.update_one(
                {'channel_id': int(channel_id)},
                {'$set': {'stop_schedule': None, 'resume_schedule': None}}
            )

db = Database(DB_URI, DB_NAME)
