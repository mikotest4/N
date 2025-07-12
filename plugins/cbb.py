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
import qrcode
import io
import base64

# Dictionary to store payment sessions
payment_sessions = {}

async def generate_upi_qr(upi_id, amount, name="Premium Plan"):
    """Generate UPI QR code for payment"""
    try:
        # Create UPI payment URL
        upi_url = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR"
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(upi_url)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return img_byte_arr.getvalue()
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None

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
                f"ʜᴇʟʟᴏ {query.from_user.first_name} 👋\n\n"
                f"ʜᴇʀᴇ ʏᴏᴜ ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ ᴍᴇᴍʙᴇʀꜱʜɪᴘ ᴏꜰ ᴛʜɪꜱ ʙᴏᴛ.\n"
                f"ꜱᴏᴍᴇ ᴘʟᴀɴ ᴀʀᴇ ɢɪᴠᴇɴ ʙᴇʟᴏᴡ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇᴍ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ.\n"
                f"ɪꜰ ʏᴏᴜ ᴍᴀᴅᴇ ᴛʜᴇ ᴘᴀʏᴍᴇɴᴛ ᴀꜰᴛᴇʀ 11:00 ᴘᴍ, ᴛʜᴇ ᴏᴡɴᴇʀ ᴡɪʟʟ ᴀᴄᴛɪᴠᴀᴛᴇ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ɪꜰ ʜᴇ ɪꜱ ᴏɴʟɪɴᴇ. ᴏᴛʜᴇʀᴡɪꜱᴇ, ɪᴛ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ɪɴ ᴛʜᴇ ᴍᴏʀɴɪɴɢ."
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

        # Show UPI selection instead of direct payment
        await query.message.edit_text(
            text=(
                f"📋 <b>Plan Selected:</b> {plan_name} - ₹{price}\n\n"
                f"💳 <b>Choose Your Payment Method:</b>\n\n"
                f"Select UPI ID to proceed with payment:"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("UPI 1 (singhzerotwo@fam)", callback_data=f"upi1_{days}_{price}")
                ],
                [
                    InlineKeyboardButton("UPI 2 (7348433876@mbk)", callback_data=f"upi2_{days}_{price}")
                ],
                [
                    InlineKeyboardButton("Back", callback_data="premium")
                ]
            ])
        )

    elif data.startswith("upi1_"):
        # Extract plan details from callback data
        parts = data.split("_")
        days = parts[1]
        price = parts[2]

        # Plan name mapping
        plan_names = {
            "7": "7 Days",
            "30": "1 Month",
            "90": "3 Months",
            "180": "6 Months",
            "365": "1 Year",
            "test": "Test Plan (1 Min)"
        }

        plan_name = plan_names.get(days, f"{days} Days")

        # Generate QR code for UPI 1
        qr_data = await generate_upi_qr(UPI_1, price, plan_name)
        
        if qr_data:
            # Send QR code image with payment details
            await query.message.delete()
            await client.send_photo(
                chat_id=query.message.chat.id,
                photo=io.BytesIO(qr_data),
                caption=(
                    f"📋 <b>Plan:</b> {plan_name} - ₹{price}\n"
                    f"💳 <b>Payment Method:</b> UPI 1\n\n"
                    f"<b>UPI ID:</b> <code>{UPI_1}</code>\n\n"
                    f"📝 <b>Instructions:</b>\n"
                    f"1. Scan the QR code above or pay to UPI ID\n"
                    f"2. Pay exactly ₹{price}\n"
                    f"3. Send payment screenshot to this chat\n"
                    f"4. Wait for admin approval\n\n"
                    f"<b>Note:</b> After payment, send screenshot for verification."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Back to Plans", callback_data="premium")
                    ]
                ])
            )
        else:
            # Fallback without QR code
            await query.message.edit_text(
                text=(
                    f"📋 <b>Plan:</b> {plan_name} - ₹{price}\n"
                    f"💳 <b>Payment Method:</b> UPI 1\n\n"
                    f"<b>UPI ID:</b> <code>{UPI_1}</code>\n\n"
                    f"📝 <b>Instructions:</b>\n"
                    f"1. Pay to UPI ID: {UPI_1}\n"
                    f"2. Pay exactly ₹{price}\n"
                    f"3. Send payment screenshot to this chat\n"
                    f"4. Wait for admin approval\n\n"
                    f"<b>Note:</b> After payment, send screenshot for verification."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Back to Plans", callback_data="premium")
                    ]
                ])
            )

    elif data.startswith("upi2_"):
        # Extract plan details from callback data
        parts = data.split("_")
        days = parts[1]
        price = parts[2]

        # Plan name mapping
        plan_names = {
            "7": "7 Days",
            "30": "1 Month",
            "90": "3 Months",
            "180": "6 Months",
            "365": "1 Year",
            "test": "Test Plan (1 Min)"
        }

        plan_name = plan_names.get(days, f"{days} Days")

        # Generate QR code for UPI 2
        qr_data = await generate_upi_qr(UPI_2, price, plan_name)
        
        if qr_data:
            # Send QR code image with payment details
            await query.message.delete()
            await client.send_photo(
                chat_id=query.message.chat.id,
                photo=io.BytesIO(qr_data),
                caption=(
                    f"📋 <b>Plan:</b> {plan_name} - ₹{price}\n"
                    f"💳 <b>Payment Method:</b> UPI 2\n\n"
                    f"<b>UPI ID:</b> <code>{UPI_2}</code>\n\n"
                    f"📝 <b>Instructions:</b>\n"
                    f"1. Scan the QR code above or pay to UPI ID\n"
                    f"2. Pay exactly ₹{price}\n"
                    f"3. Send payment screenshot to this chat\n"
                    f"4. Wait for admin approval\n\n"
                    f"<b>Note:</b> After payment, send screenshot for verification."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Back to Plans", callback_data="premium")
                    ]
                ])
            )
        else:
            # Fallback without QR code
            await query.message.edit_text(
                text=(
                    f"📋 <b>Plan:</b> {plan_name} - ₹{price}\n"
                    f"💳 <b>Payment Method:</b> UPI 2\n\n"
                    f"<b>UPI ID:</b> <code>{UPI_2}</code>\n\n"
                    f"📝 <b>Instructions:</b>\n"
                    f"1. Pay to UPI ID: {UPI_2}\n"
                    f"2. Pay exactly ₹{price}\n"
                    f"3. Send payment screenshot to this chat\n"
                    f"4. Wait for admin approval\n\n"
                    f"<b>Note:</b> After payment, send screenshot for verification."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Back to Plans", callback_data="premium")
                    ]
                ])
            )

    elif data == "close":
        await query.message.delete()

    elif data.startswith("rfs_ch_"):
        # Handle force sub channel toggle
        ch_id = int(data.split("_")[-1])
        
        # Toggle channel mode
        current_mode = await db.get_channel_mode(ch_id)
        new_mode = "off" if current_mode == "on" else "on"
        await db.set_channel_mode(ch_id, new_mode)
        
        # Update the display
        channels = await db.show_channels()
        if not channels:
            return await query.message.edit("<b>❌ No force-sub channels found.</b>")

        buttons = []
        for channel_id in channels:
            try:
                chat = await client.get_chat(channel_id)
                mode = await db.get_channel_mode(channel_id)
                status = "🟢" if mode == "on" else "🔴"
                title = f"{status} {chat.title}"
                buttons.append([InlineKeyboardButton(title, callback_data=f"rfs_ch_{channel_id}")])
            except:
                buttons.append([InlineKeyboardButton(f"⚠️ {channel_id} (Unavailable)", callback_data=f"rfs_ch_{channel_id}")])

        buttons.append([InlineKeyboardButton("Close ✖️", callback_data="close")])

        await query.message.edit(
            "<b>⚡ Select a channel to toggle Force-Sub Mode:</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
