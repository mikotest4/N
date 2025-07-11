import base64
import re
import asyncio
import time
from datetime import datetime, timedelta, time as dt_time
from pytz import timezone
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from shortzy import Shortzy
from pyrogram.errors import FloodWait
from database.database import *
from database.db_premium import *
import logging

# NEW: Function to check if verification expired due to daily reset
def check_daily_reset_expired(verified_time):
    """Check if verification should expire due to daily 5:30 AM reset"""
    try:
        ist = timezone("Asia/Kolkata")
        current_time = datetime.now(ist)
        current_date = current_time.date()
        
        # Define daily reset time (5:30 AM)
        reset_time = dt_time(5, 30)
        reset_datetime = datetime.combine(current_date, reset_time)
        reset_datetime = ist.localize(reset_datetime)
        
        # Convert verification timestamp to datetime
        verified_datetime = datetime.fromtimestamp(verified_time, ist)
        
        # Check if verification should be expired
        if current_time >= reset_datetime:
            # Past today's 5:30 AM - check if verification was before today's reset
            return verified_datetime < reset_datetime
        else:
            # Before today's 5:30 AM - check if verification was before yesterday's reset
            yesterday_reset = reset_datetime - timedelta(days=1)
            return verified_datetime < yesterday_reset
    except Exception as e:
        print(f"Error in check_daily_reset_expired: {e}")
        return False

# NEW: Enhanced verification check function
async def is_verification_expired(user_id, verify_status):
    """Check if verification is expired (either by individual timer or daily reset)"""
    try:
        if not verify_status['is_verified']:
            return True
        
        verified_time = verify_status.get('verified_time', 0)
        try:
            verified_time = float(verified_time) if verified_time else 0
        except (ValueError, TypeError):
            verified_time = 0
        
        if verified_time == 0:
            return True
        
        # Check individual timer expiry
        individual_expired = VERIFY_EXPIRE < (time.time() - verified_time)
        
        # Check daily reset expiry
        daily_reset_expired = check_daily_reset_expired(verified_time)
        
        # Return True if either condition is met
        return individual_expired or daily_reset_expired
        
    except Exception as e:
        print(f"Error checking verification expiry for user {user_id}: {e}")
        return True

#used for cheking if a user is admin ~Owner also treated as admin level
async def check_admin(filter, client, update):
    try:
        user_id = update.from_user.id       
        return any([user_id == OWNER_ID, await db.admin_exist(user_id)])
    except Exception as e:
        print(f"! Exception in check_admin: {e}")
        return False

# Enhanced premium checking with automatic cleanup
async def is_premium_user_enhanced(user_id):
    """Enhanced premium check with automatic expiry cleanup"""
    try:
        # First check if user exists in premium collection
        user_exists = await is_premium_user(user_id)
        if not user_exists:
            return False
        
        # Check if premium has expired and auto-remove
        from database.db_premium import collection
        user_data = await collection.find_one({"user_id": user_id})
        if user_data:
            from datetime import datetime
            from pytz import timezone
            
            ist = timezone("Asia/Kolkata")
            current_time = datetime.now(ist)
            expiration_time = datetime.fromisoformat(user_data["expiration_timestamp"]).astimezone(ist)
            
            if expiration_time <= current_time:
                # Auto remove expired user
                await remove_premium(user_id)
                logging.info(f"Auto-removed expired premium user: {user_id}")
                return False
        
        return True
    except Exception as e:
        logging.error(f"Error in enhanced premium check for user {user_id}: {e}")
        return False

async def is_subscribed(client, user_id):
    channel_ids = await db.show_channels()

    if not channel_ids:
        return True

    if user_id == OWNER_ID:
        return True

    for cid in channel_ids:
        if not await is_sub(client, user_id, cid):
            # Retry once if join request might be processing
            mode = await db.get_channel_mode(cid)
            if mode == "on":
                await asyncio.sleep(2)  # give time for @on_chat_join_request to process
                if await is_sub(client, user_id, cid):
                    continue
            return False

    return True

async def is_sub(client, user_id, channel_id):
    try:
        member = await client.get_chat_member(channel_id, user_id)
        status = member.status
        #print(f"[SUB] User {user_id} in {channel_id} with status {status}")
        return status in {
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER
        }

    except UserNotParticipant:
        mode = await db.get_channel_mode(channel_id)
        if mode == "on":
            exists = await db.req_user_exist(channel_id, user_id)
            #print(f"[REQ] User {user_id} join request for {channel_id}: {exists}")
            return exists
        return False

    except Exception as e:
        #print(f"[SUB ERROR] {e}")
        return False

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.b64encode(string_bytes)
    base64_string = base64_bytes.decode("ascii")
    return base64_string

async def decode(base64_string):
    base64_bytes = base64_string.encode("ascii")
    string_bytes = base64.b64decode(base64_bytes)
    string = string_bytes.decode("ascii")
    return string

async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages:total_messages+200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except:
            pass
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages

async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = "https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0

def get_readable_time(seconds):
    result = ''
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f'{days}d'
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f'{hours}h'
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f'{minutes}m'
    seconds = int(seconds)
    result += f'{seconds}s'
    return result

def get_exp_time(seconds):
    periods = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1)]
    result = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result.append(f'{int(period_value)}{period_name}')
    return ''.join(result)

def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

# FIXED: Updated get_shortlink function to accept 3 parameters
async def get_shortlink(shortlink_url, shortlink_api, url):
    if not shortlink_url:
        return url
    try:
        shortzy = Shortzy(shortlink_api, shortlink_url)
        link = await shortzy.convert(url)
        return link
    except Exception as e:
        print(f"Error in get_shortlink: {e}")
        return url

async def not_joined(client, message):
    try:
        buttons = []
        channels = await db.show_channels()
        
        for channel_id in channels:
            try:
                chat = await client.get_chat(channel_id)
                invite_link = await client.export_chat_invite_link(channel_id)
                buttons.append([InlineKeyboardButton(chat.title, url=invite_link)])
            except Exception as e:
                print(f"Error getting invite link for {channel_id}: {e}")
                continue
        
        try:
            buttons.append([InlineKeyboardButton("🔄 Reload", callback_data="reload")])
        except:
            pass
        
        text = FORCE_MSG.format(first=message.from_user.first_name)
        
        await message.reply_photo(
            photo=FORCE_PIC,
            caption=text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        print(f"Error in not_joined: {e}")

admin = filters.create(check_admin)
