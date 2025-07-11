from pyrogram import Client
from bot import Bot
from config import *
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.database import *
from database.db_premium import *
import requests
import urllib.parse
import asyncio
from pyrogram import filters
from datetime import datetime, timedelta
from pytz import timezone

# Dictionary to store payment sessions
payment_sessions = {}

async def add_premium_user_to_db(user_id: int, days: str):
    """
    Add premium user to database and return success status and expiration time
    """
    try:
        # Convert days to appropriate time value and unit
        if days == "test":
            # Test plan - 1 minute
            time_value = 1
            time_unit = "m"
        else:
            time_value = int(days)
            time_unit = "d"

        # Add premium using db_premium function
        expiration_time = await add_premium(user_id, time_value, time_unit)

        if expiration_time:
            # Parse the expiration time string to datetime object
            ist = timezone("Asia/Kolkata")
            expiration_datetime = datetime.fromisoformat(expiration_time).astimezone(ist)
            return True, expiration_datetime
        return False, None

    except Exception as e:
        print(f"Error in add_premium_user_to_db: {e}")
        return False, None

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data

    if data == "help":
        await query.message.edit_text(
            text=HELP_TXT.format(first=query.from_user.first_name),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='start'),
                 InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data='close')]
            ])
        )

    elif data == "about":
        await query.message.edit_text(
            text=ABOUT_TXT.format(first=query.from_user.first_name),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='start'),
                 InlineKeyboardButton('ᴄʟᴏꜱᴇ', callback_data='close')]
            ])
        )

    elif data == "start":
        await query.message.edit_text(
            text=START_MSG.format(first=query.from_user.first_name),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʜᴇʟᴘ", callback_data='help'),
                 InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data='about')]
            ])
        )

    # Premium Message (with image)
    elif data == "premium":
        await query.message.delete()
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo="https://telegra.ph/file/a4e279ec76dfb285ef297-0a72f2ad5e693e628f.jpg",
            caption=(
                f"ʜᴇʟʟᴏ 『𝚈𝚊𝚎 𝙼𝚒𝚔𝚘』❋𝄗⃝🦋 ⌞𝚆𝚊𝚛𝚕𝚘𝚛𝚍𝚜⌝ ㊋ 👋\n\n"
                f"ʜᴇʀᴇ ʏᴏᴜ ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ ᴍᴇᴍʙᴇʀꜱʜɪᴘ ᴏꜰ ᴛʜɪꜱ ʙᴏᴛ.\n"
                f"ꜱᴏᴍᴇ ᴘʟᴀɴ ᴀʀᴇ ɢɪᴠᴇɴ ʙᴇʟᴏᴡ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇᴍ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ."
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("7 Days - 50 ₹", callback_data="plan_7_50"),
                    InlineKeyboardButton("1 Month - 130 ₹", callback_data="plan_30_130")
                ],
                [
                    InlineKeyboardButton("3 Months - 299 ₹", callback_data="plan_90_299"),
                    InlineKeyboardButton("6 Months - 599 ₹", callback_data="plan_180_599")
                ],
                [
                    InlineKeyboardButton("1 Year - 999 ₹", callback_data="plan_365_999")
                ],
                [
                    InlineKeyboardButton("Back", callback_data="start")
                ]
            ])
        )

    elif data.startswith("plan_"):
        # Extract plan details from callback data
        parts = data.split("_")

        if parts[1] == "test":
            # Test plan
            days = "test"
            price = "1"
            plan_name = "Test Plan (1 Min)"
        else:
            days = parts[1]
            price = parts[2]

            # Plan name mapping
            plan_names = {
                "7": "7 Days",
                "30": "1 Month",
                "90": "3 Months",
                "180": "6 Months",
                "365": "1 Year"
            }

            plan_name = plan_names.get(days, f"{days} Days")

        # Generate UPI QR Code
        upi_id = "singhzerotwo@fam"
        amount = price
        note = f"{plan_name} Premium Plan"

        # Create UPI payment URL
        upi_url = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(note)}&am={amount}&cu=INR"

        # Generate QR Code using API
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_url)}"

        try:
            await query.message.delete()
            await client.send_photo(
                chat_id=query.message.chat.id,
                photo=qr_api_url,
                caption=(
                    f"<b>{plan_name} ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ</b>\n\n"
                    f"<b>ᴘʀɪᴄᴇ:</b> {price} ₹\n"
                    f"<b>ᴅᴜʀᴀᴛɪᴏɴ:</b> {plan_name}\n\n"
                    f"<b>ᴘᴀʏᴍᴇɴᴛ ɪɴꜱᴛʀᴜᴄᴛɪᴏɴꜱ:</b>\n"
                    f"<b>ᴘᴀʏ {price} ₹ ᴛᴏ ᴛʜᴇ ɢɪᴠᴇɴ Qʀ ᴄᴏᴅᴇ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ <u>I ʜᴀᴠᴇ ᴘᴀɪᴅ</u>.</b>\n"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("I Have Paid", callback_data=f"paid_{days}_{price}")
                    ],
                    [
                        InlineKeyboardButton("Back to Plans", callback_data="premium"),
                        InlineKeyboardButton("Home", callback_data="start")
                    ]
                ])
            )
        except Exception as e:
            # Fallback if QR generation fails
            await query.message.edit_text(
                text=(
                    f"<b>{plan_name} ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ</b>\n\n"
                    f"<b>ᴘʀɪᴄᴇ:</b> {price} ₹\n"
                    f"<b>ᴅᴜʀᴀᴛɪᴏɴ:</b> {plan_name}\n\n"
                    f"<b>ᴘᴀʏᴍᴇɴᴛ ɪɴꜱᴛʀᴜᴄᴛɪᴏɴꜱ:</b>\n"
                    f"<b>ᴘᴀʏ {price} ₹ ᴛᴏ ᴜᴘɪ ɪᴅ:</b> singhzerotwo@fam\n\n"
                    f"<b>Qʀ ᴄᴏᴅᴇ ɢᴇɴᴇʀᴀᴛɪᴏɴ ꜰᴀɪʟᴇᴅ. ᴘʟᴇᴀꜱᴇ ᴘᴀʏ ᴍᴀɴᴜᴀʟʟʏ.</b>\n"
                    f"<b>ɪꜰ ʏᴏᴜ ᴍᴀᴅᴇ ᴛʜᴇ ᴘᴀʏᴍᴇɴᴛ ᴀꜰᴛᴇʀ 11:00 ᴘᴍ, ᴛʜᴇ ᴏᴡɴᴇʀ ᴡɪʟʟ ᴀᴄᴛɪᴠᴀᴛᴇ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ɪꜰ ʜᴇ ɪꜱ ᴏɴʟɪɴᴇ. ᴏᴛʜᴇʀᴡɪꜱᴇ, ɪᴛ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ɪɴ ᴛʜᴇ ᴍᴏʀɴɪɴɢ.</b>"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("I Have Paid", callback_data=f"paid_{days}_{price}")
                    ],
                    [
                        InlineKeyboardButton("Back to Plans", callback_data="premium"),
                        InlineKeyboardButton("Home", callback_data="start")
                    ]
                ])
            )

    elif data.startswith("paid_"):
        # Extract plan details
        parts = data.split("_")
        days = parts[1]
        price = parts[2]

        # Plan name mapping
        if days == "test":
            plan_name = "Test Plan (1 Min)"
        else:
            plan_names = {
                "7": "7 Days",
                "30": "1 Month",
                "90": "3 Months",
                "180": "6 Months",
                "365": "1 Year"
            }
            plan_name = plan_names.get(days, f"{days} Days")

        # Store payment session
        payment_sessions[query.from_user.id] = {
            "days": days,
            "price": price,
            "plan_name": plan_name
        }

        await query.message.edit_text(
            text=(
                f"<b>ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ ɴᴏᴡ.</b>\n\n"
                f"<b>ʏᴏᴜ ʜᴀᴠᴇ 5 ᴍɪɴᴜᴛᴇꜱ ᴛᴏ ꜱᴇɴᴅ ᴛʜᴇ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ.</b>"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("❌ Cancel", callback_data="premium")
                ]
            ])
        )

    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass

    elif data.startswith("rfs_ch_"):
        cid = int(data.split("_")[2])
        try:
            chat = await client.get_chat(cid)
            mode = await db.get_channel_mode(cid)
            status = "🟢 ᴏɴ" if mode == "on" else "🔴 ᴏғғ"
            new_mode = "ᴏғғ" if mode == "on" else "on"
            buttons = [
                [InlineKeyboardButton(f"ʀᴇǫ ᴍᴏᴅᴇ {'OFF' if mode == 'on' else 'ON'}", callback_data=f"rfs_toggle_{cid}_{new_mode}")],
                [InlineKeyboardButton("‹ ʙᴀᴄᴋ", callback_data="fsub_back")]
            ]
            await query.message.edit_text(
                f"Channel: {chat.title}\nCurrent Force-Sub Mode: {status}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception:
            await query.answer("Failed to fetch channel info", show_alert=True)

    elif data.startswith("rfs_toggle_"):
        cid, action = data.split("_")[2:]
        cid = int(cid)
        mode = "on" if action == "on" else "off"

        await db.set_channel_mode(cid, mode)
        await query.answer(f"Force-Sub set to {'ON' if mode == 'on' else 'OFF'}")

        # Refresh the same channel's mode view
        chat = await client.get_chat(cid)
        status = "🟢 ON" if mode == "on" else "🔴 OFF"
        new_mode = "off" if mode == "on" else "on"
        buttons = [
            [InlineKeyboardButton(f"ʀᴇǫ ᴍᴏᴅᴇ {'OFF' if mode == 'on' else 'ON'}", callback_data=f"rfs_toggle_{cid}_{new_mode}")],
            [InlineKeyboardButton("‹ ʙᴀᴄᴋ", callback_data="fsub_back")]
        ]
        await query.message.edit_text(
            f"Channel: {chat.title}\nCurrent Force-Sub Mode: {status}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "fsub_back":
        temp = await query.message.edit_text("<b><i>ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>")
        channels = await db.show_channels()

        if not channels:
            return await temp.edit("<b>❌ No force-sub channels found.</b>")

        buttons = []
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                mode = await db.get_channel_mode(ch_id)
                status = "🟢" if mode == "on" else "🔴"
                title = f"{status} {chat.title}"
                buttons.append([InlineKeyboardButton(title, callback_data=f"rfs_ch_{ch_id}")])
            except:
                buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Unavailable)", callback_data=f"rfs_ch_{ch_id}")])

        buttons.append([InlineKeyboardButton("Close ✖️", callback_data="close")])

        await temp.edit(
            "<b>⚡ Select a channel to toggle Force-Sub Mode:</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )

# Handler for payment screenshots
@Bot.on_message(filters.photo & filters.private)
async def handle_payment_screenshot(client: Bot, message: Message):
    user_id = message.from_user.id

    # Check if user has an active payment session
    if user_id in payment_sessions:
        session = payment_sessions[user_id]

        # Get user details
        username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
        user_id_mono = f"<code>{user_id}</code>"
        plan_info = f"{session['plan_name']} - {session['price']} ₹"

        # Send confirmation to user
        await message.reply_text(
            text=(
                f"✅ <b>ᴘᴀʏᴍᴇɴᴛ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ ʀᴇᴄᴇɪᴠᴇᴅ!</b>\n\n"
                f"ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ ɪꜱ ʙᴇɪɴɢ ᴠᴇʀɪꜰɪᴇᴅ ʙʏ ᴀᴅᴍɪɴ.\n"
                f"ʏᴏᴜ ᴡɪʟʟ ɢᴇᴛ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ ᴏɴᴄᴇ ᴠᴇʀɪꜰɪᴇᴅ.\n\n"
                f"ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ʏᴏᴜʀ ᴘᴜʀᴄʜᴀꜱᴇ! 🎉\n"
                f"ɪꜰ ʏᴏᴜ ᴍᴀᴅᴇ ᴛʜᴇ ᴘᴀʏᴍᴇɴᴛ ᴀꜰᴛᴇʀ 11:00 ᴘᴍ, ᴛʜᴇ ᴏᴡɴᴇʀ ᴡɪʟʟ ᴀᴄᴛɪᴠᴀᴛᴇ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ɪꜰ ʜᴇ ɪꜱ ᴏɴʟɪɴᴇ. ᴏᴛʜᴇʀᴡɪꜱᴇ, ɪᴛ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ɪɴ ᴛʜᴇ ᴍᴏʀɴɪɴɢ."
            )
        )

        # Forward screenshot to owner with payment info (NO APPROVE/REJECT BUTTONS)
        try:
            await client.send_photo(
                chat_id=OWNER_ID,
                photo=message.photo.file_id,
                caption=(
                    f"<b>Payment Information</b>\n\n"
                    f"<b>Username:</b> {username}\n"
                    f"<b>User ID:</b> {user_id_mono}\n"
                    f"<b>Payment Selected:</b> {plan_info}\n"
                )
                # No reply_markup here!
            )
        except Exception as e:
            await message.reply_text(
                text=(
                    f"⚠️ <b>Error sending to admin!</b>\n\n"
                    f"Please contact admin manually: {OWNER_TAG}"
                )
            )

        # Remove session after processing
        del payment_sessions[user_id]

    else:
        # Regular photo message - ignore or handle as needed
        pass
