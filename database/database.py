import motor
import asyncio
import motor.motor_asyncio
import time
import pymongo, os
from config import DB_URI, DB_NAME
import logging
from datetime import datetime, timedelta

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]

logging.basicConfig(level=logging.INFO)

default_verify = {
    'is_verified': False,
    'verified_time': 0,
    'verify_token': "",
    'link': ""
}

def new_user(id):
    return {
        '_id': id,
        'verify_status': {
            'is_verified': False,
            'verified_time': "",
            'verify_token': "",
            'link': ""
        }
    }

class Yae_X_Miko:

    def __init__(self, DB_URI, DB_NAME):
        self.dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
        self.database = self.dbclient[DB_NAME]

        self.channel_data = self.database['channels']
        self.admins_data = self.database['admins']
        self.user_data = self.database['users']
        self.sex_data = self.database['sex']
        self.banned_user_data = self.database['banned_user']
        self.autho_user_data = self.database['autho_user']
        self.del_timer_data = self.database['del_timer']
        self.fsub_data = self.database['fsub']   
        self.rqst_fsub_data = self.database['request_forcesub']
        self.rqst_fsub_Channel_data = self.database['request_forcesub_channel']
        

    # USER DATA
    async def present_user(self, user_id: int):
        found = await self.user_data.find_one({'_id': user_id})
        return bool(found)

    async def add_user(self, user_id: int):
        user_data = new_user(user_id)
        await self.user_data.insert_one(user_data)
        return

    async def full_userbase(self):
        user_docs = await self.user_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in user_docs]
        return user_ids

    async def del_user(self, user_id: int):
        await self.user_data.delete_one({'_id': user_id})
        return

    # ADMIN DATA
    async def admin_exist(self, admin_id: int):
        found = await self.admins_data.find_one({'_id': admin_id})
        return bool(found)

    async def add_admin(self, admin_id: int):
        if not await self.admin_exist(admin_id):
            await self.admins_data.insert_one({'_id': admin_id})
            return

    async def del_admin(self, admin_id: int):
        if await self.admin_exist(admin_id):
            await self.admins_data.delete_one({'_id': admin_id})
            return

    async def get_all_admins(self):
        users_docs = await self.admins_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in users_docs]
        return user_ids

    # BAN USER DATA
    async def ban_user_exist(self, user_id: int):
        found = await self.banned_user_data.find_one({'_id': user_id})
        return bool(found)

    async def add_ban_user(self, user_id: int):
        if not await self.ban_user_exist(user_id):
            await self.banned_user_data.insert_one({'_id': user_id})
            return

    async def del_ban_user(self, user_id: int):
        if await self.ban_user_exist(user_id):
            await self.banned_user_data.delete_one({'_id': user_id})
            return

    async def get_ban_users(self):
        users_docs = await self.banned_user_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in users_docs]
        return user_ids

    # AUTO DELETE TIMER SETTINGS
    async def set_del_timer(self, value: int):        
        existing = await self.del_timer_data.find_one({})
        if existing:
            await self.del_timer_data.update_one({}, {'$set': {'value': value}})
        else:
            await self.del_timer_data.insert_one({'value': value})

    async def get_del_timer(self):
        data = await self.del_timer_data.find_one({})
        if data:
            return data.get('value', 600)
        return 0

    # CHANNEL MANAGEMENT
    async def channel_exist(self, channel_id: int):
        found = await self.fsub_data.find_one({'_id': channel_id})
        return bool(found)

    async def add_channel(self, channel_id: int):
        if not await self.channel_exist(channel_id):
            await self.fsub_data.insert_one({'_id': channel_id})
            return

    async def rem_channel(self, channel_id: int):
        if await self.channel_exist(channel_id):
            await self.fsub_data.delete_one({'_id': channel_id})
            return

    async def show_channels(self):
        channel_docs = await self.fsub_data.find().to_list(length=None)
        channel_ids = [doc['_id'] for doc in channel_docs]
        return channel_ids

    # Get current mode of a channel
    async def get_channel_mode(self, channel_id: int):
        data = await self.fsub_data.find_one({'_id': channel_id})
        return data.get("mode", "off") if data else "off"

    # Set mode of a channel
    async def set_channel_mode(self, channel_id: int, mode: str):
        await self.fsub_data.update_one(
            {'_id': channel_id}, 
            {'$set': {'mode': mode}}, 
            upsert=True
        )

    # INVITE LINK MANAGEMENT
    async def get_invite_link(self, channel_id: int):
        """Get stored invite link for a channel"""
        try:
            data = await self.fsub_data.find_one({'_id': channel_id})
            if data:
                return data.get('invite_link', None)
            return None
        except Exception as e:
            print(f"[ERROR] Failed to get invite link for channel {channel_id}: {e}")
            return None

    async def store_invite_link(self, channel_id: int, link: str):
        """Store invite link for a channel"""
        try:
            await self.fsub_data.update_one(
                {'_id': channel_id},
                {'$set': {'invite_link': link}},
                upsert=True
            )
            print(f"[DEBUG] Stored invite link for channel {channel_id}: {link}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to store invite link for channel {channel_id}: {e}")
            return False

    # VERIFICATION SYSTEM - IMPROVED
    async def update_verify_status(self, user_id: int, **kwargs):
        """Update verification status with proper error handling"""
        try:
            user_data = await self.user_data.find_one({'_id': user_id})
            
            if not user_data:
                # Create new user with default verify status
                user_data = new_user(user_id)
                await self.user_data.insert_one(user_data)
            
            # Prepare update data
            update_data = {}
            for key, value in kwargs.items():
                update_data[f'verify_status.{key}'] = value
            
            # Update the user's verify status
            result = await self.user_data.update_one(
                {'_id': user_id}, 
                {'$set': update_data}
            )
            
            print(f"[DEBUG] Updated verify status for user {user_id}: {kwargs}")
            print(f"[DEBUG] Update result: {result.modified_count} documents modified")
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"[ERROR] Failed to update verify status for user {user_id}: {e}")
            return False

    async def get_verify_status(self, user_id: int):
        """Get verification status with proper defaults"""
        try:
            user = await self.user_data.find_one({'_id': user_id})
            
            if not user:
                # Return default verify status for new users
                return default_verify.copy()
            
            verify_status = user.get('verify_status', default_verify.copy())
            
            # Ensure all required fields exist
            for key, default_value in default_verify.items():
                if key not in verify_status:
                    verify_status[key] = default_value
            
            print(f"[DEBUG] Retrieved verify status for user {user_id}: {verify_status}")
            return verify_status
            
        except Exception as e:
            print(f"[ERROR] Failed to get verify status for user {user_id}: {e}")
            return default_verify.copy()

    async def get_verify_count(self, user_id: int):
        """Get verification count for a user"""
        try:
            user = await self.user_data.find_one({'_id': user_id})
            if user:
                return user.get('verify_count', 0)
            return 0
        except Exception as e:
            print(f"[ERROR] Failed to get verify count for user {user_id}: {e}")
            return 0

    async def set_verify_count(self, user_id: int, count: int):
        """Set verification count for a user"""
        try:
            await self.user_data.update_one(
                {'_id': user_id},
                {'$set': {'verify_count': count}},
                upsert=True
            )
            print(f"[DEBUG] Set verify count for user {user_id}: {count}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to set verify count for user {user_id}: {e}")
            return False

    async def reset_all_verify_counts(self):
        """Reset verification counts for all users"""
        try:
            result = await self.user_data.update_many(
                {},
                {'$set': {'verify_count': 0}}
            )
            print(f"[DEBUG] Reset verify counts: {result.modified_count} users updated")
            return result.modified_count
        except Exception as e:
            print(f"[ERROR] Failed to reset verify counts: {e}")
            return 0

    async def get_total_verify_count(self):
        """
        Returns the total number of users who have 'is_verified' set to True.
        """
        try:
            count = await self.user_data.count_documents({'verify_status.is_verified': True})
            print(f"[DEBUG] Total verified users: {count}")
            return count
        except Exception as e:
            print(f"[ERROR] Failed to get total verify count: {e}")
            return 0

    # REQUEST FORCE SUBSCRIPTION METHODS
    async def reqChannel_exist(self, channel_id: int):
        """Check if channel exists in request force sub"""
        found = await self.rqst_fsub_Channel_data.find_one({'_id': channel_id})
        return bool(found)

    async def req_user_exist(self, channel_id: int, user_id: int):
        """Check if user has pending request for channel"""
        found = await self.rqst_fsub_data.find_one({'channel_id': channel_id, 'user_id': user_id})
        return bool(found)

    async def req_user(self, channel_id: int, user_id: int):
        """Add user to request list for channel"""
        if not await self.req_user_exist(channel_id, user_id):
            await self.rqst_fsub_data.insert_one({'channel_id': channel_id, 'user_id': user_id})
            print(f"[DEBUG] Added user {user_id} to request list for channel {channel_id}")

    async def del_req_user(self, channel_id: int, user_id: int):
        """Remove user from request list for channel"""
        if await self.req_user_exist(channel_id, user_id):
            await self.rqst_fsub_data.delete_one({'channel_id': channel_id, 'user_id': user_id})
            print(f"[DEBUG] Removed user {user_id} from request list for channel {channel_id}")

    async def add_req_channel(self, channel_id: int):
        """Add channel to request force sub list"""
        if not await self.reqChannel_exist(channel_id):
            await self.rqst_fsub_Channel_data.insert_one({'_id': channel_id})
            print(f"[DEBUG] Added channel {channel_id} to request force sub list")

    async def del_req_channel(self, channel_id: int):
        """Remove channel from request force sub list"""
        if await self.reqChannel_exist(channel_id):
            await self.rqst_fsub_Channel_data.delete_one({'_id': channel_id})
            # Also remove all user requests for this channel
            await self.rqst_fsub_data.delete_many({'channel_id': channel_id})
            print(f"[DEBUG] Removed channel {channel_id} from request force sub list")

    # UTILITY METHODS
    async def get_user_data(self, user_id: int):
        """Get complete user data"""
        try:
            user = await self.user_data.find_one({'_id': user_id})
            if not user:
                # Create new user if doesn't exist
                user_data = new_user(user_id)
                await self.user_data.insert_one(user_data)
                return user_data
            return user
        except Exception as e:
            print(f"[ERROR] Failed to get user data for {user_id}: {e}")
            return new_user(user_id)

    async def update_user_data(self, user_id: int, update_data: dict):
        """Update user data with arbitrary fields"""
        try:
            result = await self.user_data.update_one(
                {'_id': user_id},
                {'$set': update_data},
                upsert=True
            )
            print(f"[DEBUG] Updated user data for {user_id}: {update_data}")
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            print(f"[ERROR] Failed to update user data for {user_id}: {e}")
            return False

    async def cleanup_expired_verifications(self, expire_time: int):
        """Clean up expired verification tokens"""
        try:
            current_time = time.time()
            cutoff_time = current_time - expire_time
            
            # Find users with expired verification
            expired_users = []
            async for user in self.user_data.find({}):
                verify_status = user.get('verify_status', {})
                verified_time = verify_status.get('verified_time', 0)
                
                try:
                    verified_time = float(verified_time) if verified_time else 0
                except (ValueError, TypeError):
                    verified_time = 0
                
                if verify_status.get('is_verified', False) and verified_time < cutoff_time:
                    expired_users.append(user['_id'])
            
            # Reset verification for expired users
            if expired_users:
                await self.user_data.update_many(
                    {'_id': {'$in': expired_users}},
                    {'$set': {'verify_status.is_verified': False}}
                )
                print(f"[DEBUG] Reset verification for {len(expired_users)} expired users")
            
            return len(expired_users)
            
        except Exception as e:
            print(f"[ERROR] Failed to cleanup expired verifications: {e}")
            return 0

# Create database instance
db = Yae_X_Miko(DB_URI, DB_NAME)
