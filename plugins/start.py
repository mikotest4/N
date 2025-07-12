import asyncio
import os
import random
import sys
import re
import string 
import string as rohit
import time
from datetime import datetime, timedelta
from pytz import timezone
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, 
    ReplyKeyboardMarkup, ChatInviteLink, ChatPrivileges
)
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant
from bot import Bot
from config import *
from helper_func import *
from database.database import *
from database.db_premium import *

BAN_SUPPORT = f"{BAN_SUPPORT}"
TUT_VID = f"{TUT_VID}"

#=====================================================================================##

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    id = message.from_user.id
    is_premium = await is_premium_user(id)

    # Check if user is banned
    banned_users = await db.get_ban_users()
    if user_id in banned_users:
        return await message.reply_text(
            "<b>⛔️ You are Bᴀɴɴᴇᴅ from using this bot.</b>\n\n"
            "<i>Contact support if you think this is a mistake.</i>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Contact Support", url=BAN_SUPPORT)]]
            )
        )

    # ✅ Check Force Subscription FIRST (priority check)
    if not await is_subscribed(client, user_id):
        return await not_joined(client, message)

    # Check if user is an admin and treat them as verified
    if user_id in await db.get_all_admins():
        verify_status = {
            'is_verified': True,
            'verify_token': None, 
            'verified_time': time.time(),
            'link': ""
        }
    else:
        verify_status = await db.get_verify_status(id)

        # NOW check token verification (only after force sub is satisfied)
        if SHORTLINK_URL or SHORTLINK_API:
            # Fix: Ensure verified_time is a number before comparison
            verified_time = verify_status.get('verified_time', 0)
            try:
                verified_time = float(verified_time) if verified_time else 0
            except (ValueError, TypeError):
                verified_time = 0

            if verify_status['is_verified'] and VERIFY_EXPIRE < (time.time() - verified_time):
                await db.update_verify_status(user_id, is_verified=False)

            # ===================== Token Verification =====================
            if "verify_" in message.text:
                _, token = message.text.split("_", 1)
                
                # Debug logging
                current_token = verify_status.get('verify_token', '')
                print(f"[DEBUG] User {user_id} verification attempt:")
                print(f"[DEBUG] Received token: '{token}'")
                print(f"[DEBUG] Expected token: '{current_token}'")
                print(f"[DEBUG] Verify status: {verify_status}")
                
                # Check if token exists and matches
                if not current_token:
                    return await message.reply("No verification token found. Please try again by clicking /start.")
                
                if current_token != token:
                    return await client.send_photo(
                        chat_id=message.chat.id,
                        photo="https://telegra.ph/file/a4e279ec76dfb285ef297-0a72f2ad5e693e628f.jpg",
                        caption="<b>❌ Your token is invalid or expired.\nClick /start to try again.</b>",
                        reply_markup=None,
                        protect_content=False
                    )
                
                # Token is valid, update verification status
                await db.update_verify_status(id, is_verified=True, verified_time=time.time())
                
                current = await db.get_verify_count(id)
                await db.set_verify_count(id, current + 1)
                
                reply_markup = None
                if verify_status.get("link", "") != "":
                    reply_markup = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔗 Open Link", url=verify_status["link"])
                    ]])
                
                return await client.send_photo(
                    chat_id=message.chat.id,
                    photo="https://telegra.ph/file/a4e279ec76dfb285ef297-0a72f2ad5e693e628f.jpg",
                    caption=f"<b>✅ Your token has been successfully verified and is valid for {get_exp_time(VERIFY_EXPIRE)}</b>",
                    reply_markup=reply_markup,
                    protect_content=False
                )
            # ===================== END Token Verification =====================

            # ===================== Token Generation =====================
            if not verify_status['is_verified'] and not is_premium:
                token = ''.join(random.choices(rohit.ascii_letters + rohit.digits, k=10))
                
                # Generate shortlink first
                link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, f'https://telegram.dog/{client.username}?start=verify_{token}')
                
                # Update database with both token and link
                await db.update_verify_status(id, verify_token=token, link=link)
                
                # Debug logging
                print(f"[DEBUG] Generated token for user {id}: '{token}'")
                print(f"[DEBUG] Generated link: '{link}'")
                
                btn = [
                    [InlineKeyboardButton("• ᴏᴘᴇɴ ʟɪɴᴋ •", url=link), 
                    InlineKeyboardButton('• ᴛᴜᴛᴏʀɪᴀʟ •', url=TUT_VID)],
                    [InlineKeyboardButton('• ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ •', callback_data='premium')]
                ]
                return await client.send_photo(
                    chat_id=message.chat.id,
                    photo="https://telegra.ph/file/a4e279ec76dfb285ef297-0a72f2ad5e693e628f.jpg",
                    caption=(
                        f"<b>𝗬𝗼𝘂𝗿 𝘁𝗼𝗸𝗲𝗻 𝗵𝗮𝘀 𝗲𝘅𝗽𝗶𝗿𝗲𝗱. 𝗣𝗹𝗲𝗮𝘀𝗲 𝗿𝗲𝗳𝗿𝗲𝘀𝗵 𝘆𝗼𝘂𝗿 𝘁𝗼𝗸𝗲𝗻 𝘁𝗼 𝗰𝗼𝗻𝘁𝗶𝗻𝘂𝗲..</b>\n\n"
                        f"<b>Tᴏᴋᴇɴ Tɪᴍᴇᴏᴜᴛ:</b> {get_exp_time(VERIFY_EXPIRE)}\n\n"
                        f"<b>ᴡʜᴀᴛ ɪs ᴛʜᴇ ᴛᴏᴋᴇɴ??</b>\n"
                        f"<b>ᴛʜɪs ɪs ᴀɴ ᴀᴅs ᴛᴏᴋᴇɴ. ᴘᴀssɪɴɢ ᴏɴᴇ ᴀᴅ ᴀʟʟᴏᴡs ʏᴏᴜ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ ғᴏʀ {get_exp_time(VERIFY_EXPIRE)}</b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn),
                    protect_content=False
                )
            # ===================== END Token Generation =====================

    # File auto-delete time in seconds - Fix: Ensure it's an integer
    try:
        FILE_AUTO_DELETE = await db.get_del_timer()
        FILE_AUTO_DELETE = int(FILE_AUTO_DELETE) if FILE_AUTO_DELETE else 0
    except (ValueError, TypeError):
        FILE_AUTO_DELETE = 0

    # Add user if not already present
    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except:
            pass

    # Handle normal message flow
    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except IndexError:
            return

        string = await decode(base64_string)
        argument = string.split("-")

        ids = []
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                print(f"Error decoding IDs: {e}")
                return

        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                print(f"Error decoding ID: {e}")
                return

        temp_msg = await message.reply("<b>Please wait...</b>")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("Something went wrong!")
            print(f"Error getting messages: {e}")
            return
        finally:
            await temp_msg.delete()

        codeflix_msgs = []
        for msg in messages:
            caption = (CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, 
                                             filename=msg.document.file_name) if bool(CUSTOM_CAPTION) and bool(msg.document)
                       else ("" if not msg.caption else msg.caption.html))

            reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None

            try:
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                codeflix_msgs.append(copied_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                codeflix_msgs.append(copied_msg)
            except Exception as e:
                print(f"Failed to send message: {e}")
                pass

        if FILE_AUTO_DELETE > 0:
            notification_msg = await message.reply(
                f"<b>Tʜɪs Fɪʟᴇ ᴡɪʟʟ ʙᴇ Dᴇʟᴇᴛᴇᴅ ɪɴ  {get_exp_time(FILE_AUTO_DELETE)}. Pʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ғᴏʀᴡᴀʀᴅ ɪᴛ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ʙᴇғᴏʀᴇ ɪᴛ ɢᴇᴛs Dᴇʟᴇᴛᴇᴅ.</b>"
            )

            await asyncio.sleep(FILE_AUTO_DELETE)

            for snt_msg in codeflix_msgs:    
                if snt_msg:
                    try:    
                        await snt_msg.delete()  
                    except Exception as e:
                        print(f"Error deleting message {snt_msg.id}: {e}")

            try:
                parts = message.text.split(maxsplit=1)
                if len(parts) > 1:
                    reload_url = f"https://t.me/{client.username}?start={parts[1]}"
                else:
                    reload_url = f"https://t.me/{client.username}"
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("ɢᴇᴛ ғɪʟᴇ ᴀɢᴀɪɴ!", url=reload_url)]]
                )
                await notification_msg.edit(
                    "<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ 👇</b>",
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Error updating notification with 'Get File Again' button: {e}")
    else:
        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("ᴄᴜᴛᴇ ʜᴇᴀᴠᴇɴ 10 ᴍᴏʀᴇ ᴍᴇᴍʙᴇʀs", url="https://t.me/+S95mGGbWHFRmNjM1")],
                [
                    InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data = "about"),
                    InlineKeyboardButton('ʜᴇʟᴘ •', callback_data = "help")
                ]
            ]
        )
        await client.send_photo(
            chat_id=message.chat.id,
            photo=START_PIC,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            protect_content=False
        )
        return

#=====================================================================================##

# Create a global dictionary to store chat data
chat_data_cache = {}

async def not_joined(client: Client, message: Message):
    temp = await message.reply("<b><i>Checking Subscription...</i></b>")

    user_id = message.from_user.id
    buttons = []
    count = 0
    join_request_pending = False

    try:
        all_channels = await db.show_channels()
        for total, chat_id in enumerate(all_channels, start=1):
            mode = await db.get_channel_mode(chat_id)

            await message.reply_chat_action(ChatAction.TYPING)

            if not await is_sub(client, user_id, chat_id):
                # Check if user has sent join request (pending approval)
                if mode == "on" and await db.req_user_exist(chat_id, user_id):
                    join_request_pending = True
                    try:
                        if chat_id in chat_data_cache:
                            data = chat_data_cache[chat_id]
                        else:
                            data = await client.get_chat(chat_id)
                            chat_data_cache[chat_id] = data
                        name = data.title
                        link = await db.get_invite_link(chat_id)
                        if not link:
                            if data.username:
                                link = f"https://t.me/{data.username}"
                            else:
                                invite = await client.create_chat_invite_link(chat_id=chat_id, expire_date=None)
                                link = invite.invite_link
                                await db.store_invite_link(chat_id, link)
                        buttons.append([InlineKeyboardButton(text=name, url=link)])
                        count += 1
                        await temp.edit(f"<b>{'! ' * count}</b>")
                    except Exception as e:
                        print(f"Error with chat {chat_id}: {e}")
                        return await temp.edit(
                            f"<b>! Eʀʀᴏʀ</b>\n"
                            f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
                        )

        # Retry Button
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) > 1:
                retry_url = f"https://t.me/{client.username}?start={parts[1]}"
            else:
                retry_url = f"https://t.me/{client.username}"
            buttons.append([
                InlineKeyboardButton(
                    text='♻️ Tʀʏ Aɢᴀɪɴ',
                    url=retry_url
                )
            ])
        except IndexError:
            pass

        await client.send_photo(
            chat_id=message.chat.id,
            photo=FORCE_PIC,
            caption=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            protect_content=False
        )

    except Exception as e:
        print(f"Final Error: {e}")
        await temp.edit(
            f"<b>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @Authorise_Miko</b>\n"
            f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
        )

#=====================================================================================##

@Bot.on_message(filters.command('myplan') & filters.private)
async def check_plan(client: Client, message: Message):
    user_id = message.from_user.id
    
    try:
        is_premium = await is_premium_user(user_id)
        
        if is_premium:
            # Get premium user details
            user_data = await get_premium_user_data(user_id)
            if user_data:
                expiry_date = user_data.get("expiration_timestamp", "Unknown")
                status_message = f"<b>✅ Premium Status: Active</b>\n\n<b>Expires:</b> {expiry_date}"
            else:
                status_message = "<b>✅ Premium Status: Active</b>\n\n<b>Expires:</b> Unknown"
        else:
            status_message = "<b>❌ Premium Status: Not Active</b>\n\n<i>Contact @Yae_X_Miko to purchase premium.</i>"
            
    except Exception as e:
        status_message = f"<b>❌ Error checking premium status:</b>\n<code>{str(e)}</code>"
    
    # Ensure message is not empty
    if not status_message or status_message.strip() == "":
        status_message = "<b>❌ Unable to retrieve plan status. Please contact support.</b>"
    
    await message.reply(status_message)

#=====================================================================================##
# Command to add premium user
@Bot.on_message(filters.command('addpremium') & filters.private & admin)
async def add_premium_user_command(client, msg):
    if len(msg.command) != 4:
        await msg.reply_text(
            "Usage: /addpremium <user_id> <time_value> <time_unit>\n\n"
            "Time Units:\n"
            "s - seconds\n"
            "m - minutes\n"
            "h - hours\n"
            "d - days\n"
            "y - years\n\n"
            "Examples:\n"
            "/addpremium 123456789 30 m → 30 minutes\n"
            "/addpremium 123456789 2 h → 2 hours\n"
            "/addpremium 123456789 1 d → 1 day\n"
            "/addpremium 123456789 1 y → 1 year"
        )
        return

    try:
        user_id = int(msg.command[1])
        time_value = int(msg.command[2])
        time_unit = msg.command[3].lower()  # supports: s, m, h, d, y

        # Call add_premium function
        expiration_time = await add_premium(user_id, time_value, time_unit)

        # Notify the admin
        await msg.reply_text(
            f"✅ User `{user_id}` added as a premium user for {time_value} {time_unit}.\n"
            f"Expiration Time: `{expiration_time}`"
        )

        # Notify the user
        await client.send_message(
            chat_id=user_id,
            text=(
                f"🎉 Premium Activated!\n\n"
                f"You have received premium access for `{time_value} {time_unit}`.\n"
                f"Expires on: `{expiration_time}`"
            ),
        )

    except ValueError:
        await msg.reply_text("❌ Invalid input. Please ensure user ID and time value are numbers.")
    except Exception as e:
        await msg.reply_text(f"⚠️ An error occurred: `{str(e)}`")

# Command to remove premium user
@Bot.on_message(filters.command('remove_premium') & filters.private & admin)
async def pre_remove_user(client: Client, msg: Message):
    if len(msg.command) != 2:
        await msg.reply_text("Usage: /remove_premium user_id")
        return
    try:
        user_id = int(msg.command[1])
        await remove_premium(user_id)
        await msg.reply_text(f"User {user_id} has been removed.")
    except ValueError:
        await msg.reply_text("user_id must be an integer or not available in database.")

# Command to list active premium users
@Bot.on_message(filters.command('premium_users') & filters.private & admin)
async def list_premium_users_command(client, message):
    # Define IST timezone
    ist = timezone("Asia/Kolkata")

    # Retrieve all users from the collection
    premium_users_cursor = collection.find({})
    premium_user_list = ['Active Premium Users in database:']
    current_time = datetime.now(ist)  # Get current time in IST

    # Use async for to iterate over the async cursor
    async for user in premium_users_cursor:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]

        try:
            # Convert expiration_timestamp to a timezone-aware datetime object in IST
            expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)

            # Calculate remaining time
            remaining_time = expiration_time - current_time

            if remaining_time.total_seconds() <= 0:
                # Remove expired users from the database
                await collection.delete_one({"user_id": user_id})
                continue  # Skip to the next user if this one is expired

            # If not expired, retrieve user info
            user_info = await client.get_users(user_id)
            username = user_info.username if user_info.username else "No Username"
            first_name = user_info.first_name
            mention = user_info.mention

            # Calculate days, hours, minutes, seconds left
            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )
            expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"

            # Add user details to the list
            premium_user_list.append(
                f"UserID: <code>{user_id}</code>\n"
                f"User: @{username}\n"
                f"Name: {mention}\n"
                f"Expiry: {expiry_info}"
            )
        except Exception as e:
            premium_user_list.append(
                f"UserID: <code>{user_id}</code>\n"
                f"Error: Unable to fetch user details ({str(e)})"
            )

    if len(premium_user_list) == 1:  # No active users found
        await message.reply_text("I found 0 active premium users in my DB")
    else:
        await message.reply_text("\n\n".join(premium_user_list), parse_mode=None)

#=====================================================================================##

@Bot.on_message(filters.command("count") & filters.private & admin)
async def total_verify_count_cmd(client, message: Message):
    total = await db.get_total_verify_count()
    await message.reply_text(f"Tᴏᴛᴀʟ ᴠɪғɪᴇᴇᴅ ᴛᴏᴋᴇɴs ᴛᴏᴅᴀʏ: <b>{total}</b>")

#=====================================================================================##

@Bot.on_message(filters.command('commands') & filters.private & admin)
async def bcmd(bot: Bot, message: Message):        
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data = "close")]])
    await message.reply(text=CMD_TXT, reply_markup = reply_markup, quote= True)

#=====================================================================================##
