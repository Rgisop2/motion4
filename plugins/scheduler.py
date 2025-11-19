import asyncio
from datetime import datetime, timedelta
import pytz
from plugins.database import db
from plugins.link_changer import link_changer

class Scheduler:
    def __init__(self):
        self.scheduler_task = None
        self.timezone = pytz.timezone('Asia/Kolkata')
        self.scheduled_stops = {}  # Track scheduled stop tasks per channel
        self.scheduled_resumes = {}  # Track scheduled resume tasks per channel

    async def parse_time(self, time_str):
        """Parse time string in HH:MM:SS format"""
        try:
            parts = time_str.split(':')
            if len(parts) != 3:
                return None
            hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
            if not (0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 60):
                return None
            return hours, minutes, seconds
        except:
            return None

    async def get_next_run_time(self, hour, minute, second):
        """Calculate when a scheduled task should run next"""
        now = datetime.now(self.timezone)
        scheduled = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
        
        # If the scheduled time has already passed today, schedule for tomorrow
        if scheduled <= now:
            scheduled += timedelta(days=1)
        
        return scheduled

    async def schedule_channel_task(self, channel_id, user_id, account_id, stop_time, resume_time):
        """Schedule stop and resume tasks for a channel"""
        # Parse times
        stop_parts = await self.parse_time(stop_time)
        resume_parts = await self.parse_time(resume_time)
        
        if not stop_parts or not resume_parts:
            return False, "Invalid time format. Use HH:MM:SS"
        
        channel = await db.get_channel(channel_id)
        if not channel:
            return False, "Channel not found"
        
        # Get account info for rotation details
        account = await db.get_account(account_id)
        if not account:
            return False, "Account not found"
        
        base_username = channel['base_username']
        interval = channel['interval']
        
        async def stop_task():
            """Task to stop channel rotation at scheduled time"""
            while True:
                try:
                    now = datetime.now(self.timezone)
                    next_stop = await self.get_next_run_time(*stop_parts)
                    
                    wait_seconds = (next_stop - now).total_seconds()
                    await asyncio.sleep(wait_seconds)
                    
                    # Stop the rotation
                    success, result = await link_changer.stop_channel_rotation(user_id, account_id, channel_id)
                    if success:
                        print(f"[v0] Scheduled stop: Channel {channel_id} stopped at {stop_time}")
                    else:
                        print(f"[v0] Scheduled stop failed for channel {channel_id}: {result}")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"[v0] Error in stop task for channel {channel_id}: {e}")
                    await asyncio.sleep(60)  # Retry after 1 minute on error

        async def resume_task():
            """Task to resume channel rotation at scheduled time"""
            while True:
                try:
                    now = datetime.now(self.timezone)
                    next_resume = await self.get_next_run_time(*resume_parts)
                    
                    wait_seconds = (next_resume - now).total_seconds()
                    await asyncio.sleep(wait_seconds)
                    
                    # Resume the rotation
                    success, result = await link_changer.resume_channel_rotation(
                        user_id, account_id, channel_id, base_username, interval
                    )
                    if success:
                        print(f"[v0] Scheduled resume: Channel {channel_id} resumed at {resume_time}")
                    else:
                        print(f"[v0] Scheduled resume failed for channel {channel_id}: {result}")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"[v0] Error in resume task for channel {channel_id}: {e}")
                    await asyncio.sleep(60)  # Retry after 1 minute on error

        # Cancel existing tasks for this channel if any
        stop_key = f"stop_{channel_id}"
        resume_key = f"resume_{channel_id}"
        
        if stop_key in self.scheduled_stops:
            self.scheduled_stops[stop_key].cancel()
        if resume_key in self.scheduled_resumes:
            self.scheduled_resumes[resume_key].cancel()
        
        # Create and store new tasks
        self.scheduled_stops[stop_key] = asyncio.create_task(stop_task())
        self.scheduled_resumes[resume_key] = asyncio.create_task(resume_task())
        
        return True, "Schedule set successfully"

    async def remove_schedule(self, channel_id):
        """Remove scheduled tasks for a channel"""
        stop_key = f"stop_{channel_id}"
        resume_key = f"resume_{channel_id}"
        
        if stop_key in self.scheduled_stops:
            self.scheduled_stops[stop_key].cancel()
            del self.scheduled_stops[stop_key]
        
        if resume_key in self.scheduled_resumes:
            self.scheduled_resumes[resume_key].cancel()
            del self.scheduled_resumes[resume_key]
        
        await db.remove_channel_schedule(channel_id)
        return True

    async def restore_all_schedules(self):
        """Restore all scheduled tasks on bot startup"""
        try:
            channels = await db.get_scheduled_channels()
            for channel in channels:
                success, result = await self.schedule_channel_task(
                    channel['channel_id'],
                    channel['user_id'],
                    channel['account_id'],
                    channel['stop_schedule'],
                    channel['resume_schedule']
                )
                if success:
                    print(f"[v0] Restored schedule for channel {channel['channel_id']}")
                else:
                    print(f"[v0] Failed to restore schedule for channel {channel['channel_id']}: {result}")
        except Exception as e:
            print(f"[v0] Error restoring schedules: {e}")

scheduler = Scheduler()
