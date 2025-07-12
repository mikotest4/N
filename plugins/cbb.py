#
# Copyright (C) 2025 by Codeflix-Bots@Github, < https://github.com/Codeflix-Bots >.
#
# This file is part of < https://github.com/Codeflix-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/Codeflix-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.

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
import io

# Dictionary to store payment sessions
payment_sessions = {}

# Dictionary to store users waiting for screenshot
waiting_for_screenshot = {}

async def generate_upi_qr_external(upi_id, amount, plan_name="Premium"):
    """Generate UPI QR code using external API"""
    try:
        # Create UPI payment URL
        note = f"{plan_name} Premium Plan"
        upi_url = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(note)}&am={amount}&cu=INR&tn={urllib.parse.quote('Premium Payment')}"
        
        # Generate QR Code using external API
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_url)}"
        
        print(f"Generated UPI URL: {upi_url}")
        print(f"QR API URL: {qr_api_url}")
        
        # Download QR code image
        response = requests.get(qr_api_url, timeout=10)
        if response.status_code == 200:
            qr_image = io.BytesIO(response.content)
            qr_image.seek(0)
            return qr_image
        else:
            print(f"Failed to generate QR code: {response.status_code}")
            return None
            
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
        # Clear any pending force-sub mode when starting fresh
        await db.set_force_sub_mode(query.from_user.id, False)
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
                f"ꜱᴏᴍᴇ ᴘʟᴀɴ ᴀʀᴇ ɢɪᴠᴇɴ ʙᴇʟʟᴏᴡ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇᴍ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ.\n"
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
                    InlineKeyboardButton("❌ Cancel", callback_data="start")
                ]
            ])
        )

    # Handle payment plans
    elif data.startswith("plan_"):
        parts = data.split("_")
        if len(parts) == 3:
            days = parts[1]
            price = parts[2]
            
            # Store payment session
            payment_sessions[query.from_user.id] = {
                'days': days,
                'price': price,
                'timestamp': datetime.now()
            }
            
            # Show payment options with Amazon Gift Card as third option
            await query.message.edit_text(
                f"<b>ᴘʟᴀɴ: {days} ᴅᴀʏs - ₹{price}</b>\n\n"
                f"<b>sᴇʟᴇᴄᴛ ᴘᴀʏᴍᴇɴᴛ ᴍᴇᴛʜᴏᴅ</b>",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("ᴜᴘɪ 1", callback_data=f"upi1_{days}_{price}"),
                        InlineKeyboardButton("ᴜᴘɪ 2", callback_data=f"upi2_{days}_{price}")
                    ],
                    [
                        InlineKeyboardButton("ᴀᴍᴀᴢᴏɴ ɢɪғᴛ ᴄᴀʀᴅ", callback_data=f"amazon_{days}_{price}")
                    ],
                    [
                        InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="premium")
                    ]
                ])
            )

    # Handle UPI 1 selection
    elif data.startswith("upi1_"):
        parts = data.split("_")
        if len(parts) == 3:
            days = parts[1]
            price = parts[2]
            
            # Generate UPI QR Code for UPI 1
            upi_id = "singhzerotwo@fam"
            amount = price
            plan_name = f"{days} Days"
            
            qr_image = await generate_upi_qr_external(upi_id, amount, plan_name)
            
            if qr_image:
                try:
                    await query.message.delete()
                    await client.send_photo(
                        chat_id=query.message.chat.id,
                        photo=qr_image,
                        caption=(
                            f"<b>ᴘʟᴀɴ: {days} ᴅᴀʏs - ₹{price}</b>\n"
                            f"<b>ᴘᴀʏᴍᴇɴᴛ ᴍᴇᴛʜᴏᴅ: ᴜᴘɪ 1</b>\n\n"
                            f"<b>📝 ɪɴsᴛʀᴜᴄᴛɪᴏɴs:</b>\n"
                            f"1. <b>sᴄᴀɴ ᴛʜᴇ Qʀ ᴄᴏᴅᴇ ᴀʙᴏᴠᴇ ᴏʀ ᴘᴀʏ ᴛᴏ ᴜᴘɪ ɪᴅ</b>\n"
                            f"2. <b>ᴘᴀʏ ᴇxᴀᴄᴛʟʏ ₹{price}.</b>\n"
                            f"3. <b>ᴄʟɪᴄᴋ ᴏɴ ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ.</b>\n\n"
                            f"<b>ɴᴏᴛᴇ: ɪғ ʏᴏᴜ ᴍᴀᴋᴇ ᴘᴀʏᴍᴇɴᴛ ᴀᴛ ɴɪɢʜᴛ ᴀғᴛᴇʀ 11 ᴘᴍ ᴛʜᴀɴ ʏᴏᴜ ʜᴀᴠᴇ ᴛᴏ ᴡᴀɪᴛ ғᴏʀ ᴍᴏʀɴɪɴɢ ʙᴇᴄᴀᴜsᴇ ᴏᴡɴᴇʀ ɪs sʟᴇᴇᴘɪɴɢ ᴛʜᴀᴛ's ᴡʜʏ ʜᴇ ᴄᴀɴ'ᴛ ᴀᴄᴛɪᴠᴇ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ɪғ ᴏᴡɴᴇʀ ɪs ᴏɴʟɪɴᴇ ᴛʜᴀɴ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ᴀᴄᴛɪᴠᴇ ɪɴ ᴀ ʜᴏᴜʀ sᴏ ᴘᴀʏ ᴀᴛ ʏᴏᴜʀ ᴏᴡɴ ʀɪsᴋ ᴀғᴛᴇʀ ɴɪɢʜᴛ 11 ᴘᴍ ᴅᴏɴ'ᴛ ʙʟᴀᴍᴇ ᴏᴡɴᴇʀ.</b>"
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton("I Have Paid", callback_data=f"paid_upi1_{days}_{price}"),
                                InlineKeyboardButton("❌ Cancel", callback_data="premium")
                            ]
                        ])
                    )
                except Exception as e:
                    print(f"Error sending photo: {e}")
                    await query.answer("Failed to send QR code. Please try again.", show_alert=True)
            else:
                await query.answer("Failed to generate QR code. Please try again.", show_alert=True)

    # Handle UPI 2 selection
    elif data.startswith("upi2_"):
        parts = data.split("_")
        if len(parts) == 3:
            days = parts[1]
            price = parts[2]
            
            # Generate UPI QR Code for UPI 2
            upi_id = "7348433876@mbk"
            amount = price
            plan_name = f"{days} Days"
            
            qr_image = await generate_upi_qr_external(upi_id, amount, plan_name)
            
            if qr_image:
                try:
                    await query.message.delete()
                    await client.send_photo(
                        chat_id=query.message.chat.id,
                        photo=qr_image,
                        caption=(
                            f"<b>ᴘʟᴀɴ: {days} ᴅᴀʏs - ₹{price}</b>\n"
                            f"<b>ᴘᴀʏᴍᴇɴᴛ ᴍᴇᴛʜᴏᴅ: ᴜᴘɪ 2</b>\n\n"
                            f"<b>📝 ɪɴsᴛʀᴜᴄᴛɪᴏɴs:</b>\n"
                            f"1. <b>sᴄᴀɴ ᴛʜᴇ Qʀ ᴄᴏᴅᴇ ᴀʙᴏᴠᴇ ᴏʀ ᴘᴀʏ ᴛᴏ ᴜᴘɪ ɪᴅ</b>\n"
                            f"2. <b>ᴘᴀʏ ᴇxᴀᴄᴛʟʏ ₹{price}.</b>\n"
                            f"3. <b>ᴄʟɪᴄᴋ ᴏɴ ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ.</b>\n\n"
                            f"<b>ɴᴏᴛᴇ: ɪғ ʏᴏᴜ ᴍᴀᴋᴇ ᴘᴀʏᴍᴇɴᴛ ᴀᴛ ɴɪɢʜᴛ ᴀғᴛᴇʀ 11 ᴘᴍ ᴛʜᴀɴ ʏᴏᴜ ʜᴀᴠᴇ ᴛᴏ ᴡᴀɪᴛ ғᴏʀ ᴍᴏʀɴɪɴɢ ʙᴇᴄᴀᴜsᴇ ᴏᴡɴᴇʀ ɪs sʟᴇᴇᴘɪɴɢ ᴛʜᴀᴛ's ᴡʜʏ ʜᴇ ᴄᴀɴ'ᴛ ᴀᴄᴛɪᴠᴇ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ɪғ ᴏᴡɴᴇʀ ɪs ᴏɴʟɪɴᴇ ᴛʜᴀɴ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ᴀᴄᴛɪᴠᴇ ɪɴ ᴀ ʜᴏᴜʀ sᴏ ᴘᴀʏ ᴀᴛ ʏᴏᴜʀ ᴏᴡɴ ʀɪsᴋ ᴀғᴛᴇʀ ɴɪɢʜᴛ 11 ᴘᴍ ᴅᴏɴ'ᴛ ʙʟᴀᴍᴇ ᴏᴡɴᴇʀ.</b>"
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton("I Have Paid", callback_data=f"paid_upi2_{days}_{price}"),
                                InlineKeyboardButton("❌ Cancel", callback_data="premium")
                            ]
                        ])
                    )
                except Exception as e:
                    print(f"Error sending photo: {e}")
                    await query.answer("Failed to send QR code. Please try again.", show_alert=True)
            else:
                await query.answer("Failed to generate QR code. Please try again.", show_alert=True)

    # Handle Amazon Gift Card selection
    elif data.startswith("amazon_"):
        parts = data.split("_")
        if len(parts) == 3:
            days = parts[1]
            price = parts[2]
            
            await query.message.edit_text(
                f"<b>ᴘʟᴀɴ: {days} ᴅᴀʏs - ₹{price}</b>\n"
                f"<b>ᴘᴀʏᴍᴇɴᴛ ᴍᴇᴛʜᴏᴅ: ᴀᴍᴀᴢᴏɴ ɢɪғᴛ ᴄᴀʀᴅ</b>\n\n"
                f"<b>📝 ɪɴsᴛʀᴜᴄᴛɪᴏɴs:</b>\n"
                f"1. <b>ᴘᴜʀᴄʜᴀsᴇ ᴀɴ ᴀᴍᴀᴢᴏɴ ɢɪғᴛ ᴄᴀʀᴅ ғᴏʀ ᴇxᴀᴄᴛʟʏ ₹{price}</b>\n"
                f"2. <b>ʏᴏᴜ ᴄᴀɴ sᴇɴᴅ ᴇɪᴛʜᴇʀ:</b>\n"
                f"   - <b>sᴄʀᴇᴇɴsʜᴏᴛ ᴏғ ᴛʜᴇ ɢɪғᴛ ᴄᴀʀᴅ</b>\n"
                f"   - <b>ɢɪғᴛ ᴄᴀʀᴅ ᴄʟᴀɪᴍ ᴄᴏᴅᴇ</b>\n"
                f"   - <b>ᴏʀ ᴀ ᴅɪʀᴇᴄᴛ ʟɪɴᴋ ʟɪᴋᴇ: https://www.amazon.in/g/GBA1CP04C2947E8O?ref=gc_utyp</b>\n\n"
                f"3. <b>ᴄʟɪᴄᴋ 'sᴇɴᴛ ɢɪғᴛ ᴄᴀʀᴅ' ʙᴇʟᴏᴡ ᴡʜᴇɴ ʀᴇᴀᴅʏ</b>\n\n"
                f"<b>ɴᴏᴛᴇ: ɪғ ʏᴏᴜ ᴍᴀᴋᴇ ᴘᴀʏᴍᴇɴᴛ ᴀᴛ ɴɪɢʜᴛ ᴀғᴛᴇʀ 11 ᴘᴍ ᴛʜᴀɴ ʏᴏᴜ ʜᴀᴠᴇ ᴛᴏ ᴡᴀɪᴛ ғᴏʀ ᴍᴏʀɴɪɴɢ ʙᴇᴄᴀᴜsᴇ ᴏᴡɴᴇʀ ɪs sʟᴇᴇᴘɪɴɢ ᴛʜᴀᴛ's ᴡʜʏ ʜᴇ ᴄᴀɴ'ᴛ ᴀᴄᴛɪᴠᴇ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ɪғ ᴏᴡɴᴇʀ ɪs ᴏɴʟɪɴᴇ ᴛʜᴀɴ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ᴀᴄᴛɪᴠᴇ ɪɴ ᴀ ʜᴏᴜʀ sᴏ ᴘᴀʏ ᴀᴛ ʏᴏᴜʀ ᴏᴡɴ ʀɪsᴋ ᴀғᴛᴇʀ ɴɪɢʜᴛ 11 ᴘᴍ ᴅᴏɴ'ᴛ ʙʟᴀᴍᴇ ᴏᴡɴᴇʀ.</b>",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Send Gift Card", callback_data=f"paid_amazon_{days}_{price}"),
                        InlineKeyboardButton("Back", callback_data=f"plan_{days}_{price}")
                    ]
                ])
            )

    # Handle "I Have Paid" button click for UPI methods
    elif data.startswith("paid_upi1_") or data.startswith("paid_upi2_"):
        parts = data.split("_")
        if len(parts) == 4:
            upi_method = parts[1]  # upi1 or upi2
            days = parts[2]
            price = parts[3]
            
            # Store user in waiting list
            waiting_for_screenshot[query.from_user.id] = {
                'days': days,
                'price': price,
                'upi_method': upi_method,
                'timestamp': datetime.now()
            }
            
            await query.message.edit_text(
                "<b>📸 ᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ ғᴏʀ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ.</b>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Cancel", callback_data="premium")]
                ])
            )

    # Handle "Send Gift Card" button click for Amazon
    elif data.startswith("paid_amazon_"):
        parts = data.split("_")
        if len(parts) == 4:
            days = parts[2]
            price = parts[3]
            
            # Store user in waiting list
            waiting_for_screenshot[query.from_user.id] = {
                'days': days,
                'price': price,
                'upi_method': 'amazon',
                'timestamp': datetime.now()
            }
            
            await query.message.edit_text(
                "<b>📸 ᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ ᴀᴍᴀᴢᴏɴ ɢɪғᴛ ᴄᴀʀᴅ (sᴄʀᴇᴇɴsʜᴏᴛ, ᴄʟᴀɪᴍ ᴄᴏᴅᴇ, ᴏʀ ʟɪɴᴋ).</b>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Cancel", callback_data="premium")]
                ])
            )

    # Handle request completion
    elif data == "request_completed":
        await query.message.edit_text(
            "<b>✅ Your request has been submitted successfully!</b>\n\n"
            "<b>You can now continue using the bot.</b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home", callback_data="start")]
            ])
        )

    # Handle Force Sub Channel Toggle
    elif data.startswith("rfs_ch_"):
        cid = int(data.split("_")[2])
        try:
            chat = await client.get_chat(cid)
            mode = await db.get_channel_mode(cid)
            status = "🟢 ON" if mode == "on" else "🔴 OFF"
            new_mode = "off" if mode == "on" else "on"
            buttons = [
                [InlineKeyboardButton(f"ʀᴇǫ ᴍᴏᴅᴇ {'OFF' if mode == 'on' else 'ON'}", callback_data=f"rfs_toggle_{cid}_{new_mode}")],
                [InlineKeyboardButton("‹ ʙᴀᴄᴋ", callback_data="fsub_back")]
            ]
            await query.message.edit_text(
                f"Channel: {chat.title}\nCurrent Force-Sub Mode: {status}",
                reply_markup=InlineKeyboardMarkup(buttons)
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
            reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "fsub_back":
        channels = await db.show_channels()
        buttons = []
        for cid in channels:
            try:
                chat = await client.get_chat(cid)
                mode = await db.get_channel_mode(cid)
                status = "🟢" if mode == "on" else "🔴"
                buttons.append([InlineKeyboardButton(f"{status} {chat.title}", callback_data=f"rfs_ch_{cid}")])
            except:
                continue

        await query.message.edit_text(
            "sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴛᴏɢɢʟᴇ ɪᴛs ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ:",
            reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass

# Handle screenshot and text messages for payment verification
@Bot.on_message((filters.photo | filters.text) & filters.private)
async def handle_payment_proof(client: Bot, message: Message):
    user_id = message.from_user.id
    
    # Check if user is waiting for payment proof
    if user_id in waiting_for_screenshot:
        payment_info = waiting_for_screenshot[user_id]
        
        # Get user information
        user = message.from_user
        username = f"@{user.username}" if user.username else "No Username"
        
        # Prepare caption based on payment method
        if payment_info['upi_method'] == 'amazon':
            caption = (
                f"<b>ᴘᴀʏᴍᴇɴᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>\n\n"
                f"<b>ᴜsᴇʀɴᴀᴍᴇ:</b> {username}\n"
                f"<b>ᴜsᴇʀ ɪᴅ:</b> <code>{user_id}</code>\n"
                f"<b>ᴘᴀʏᴍᴇɴᴛ sᴇʟᴇᴄᴛᴇᴅ:</b> {payment_info['days']} ᴅᴀʏs - {payment_info['price']} ₹\n"
                f"<b>ᴘᴀʏᴍᴇɴᴛ ᴍᴇᴛʜᴏᴅ:</b> ᴀᴍᴀᴢᴏɴ ɢɪғᴛ ᴄᴀʀᴅ\n"
                f"<b>ᴘᴀʏᴍᴇɴᴛ ᴘʀᴏᴏғ:</b> {'Screenshot' if message.photo else 'Text/Code/Link'}"
            )
        else:
            caption = (
                f"<b>ᴘᴀʏᴍᴇɴᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>\n\n"
                f"<b>ᴜsᴇʀɴᴀᴍᴇ:</b> {username}\n"
                f"<b>ᴜsᴇʀ ɪᴅ:</b> <code>{user_id}</code>\n"
                f"<b>ᴘᴀʏᴍᴇɴᴛ sᴇʟᴇᴄᴛᴇᴅ:</b> {payment_info['days']} ᴅᴀʏs - {payment_info['price']} ₹\n"
                f"<b>ᴘᴀʏᴍᴇɴᴛ ᴍᴇᴛʜᴏᴅ:</b> {payment_info['upi_method'].upper()}"
            )
        
        # Forward the payment proof to owner
        if message.photo:
            await client.send_photo(
                chat_id=OWNER_ID,
                photo=message.photo.file_id,
                caption=caption
            )
        else:
            await client.send_message(
                chat_id=OWNER_ID,
                text=f"{caption}\n\n<b>Payment Proof:</b>\n{message.text}"
            )
        
        # Confirm to user
        await message.reply(
            "<b>✅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ ᴘʀᴏᴏғ ʜᴀs ʙᴇᴇɴ sᴇɴᴛ ᴛᴏ ᴛʜᴇ ᴏᴡɴᴇʀ ғᴏʀ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ.</b>\n\n"
            "<b>⏳ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ғᴏʀ ᴀᴘᴘʀᴏᴠᴀʟ. ʏᴏᴜ ᴡɪʟʟ ʙᴇ ɴᴏᴛɪғɪᴇᴅ ᴏɴᴄᴇ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ɪs ᴀᴄᴛɪᴠᴀᴛᴇᴅ. ɪᴛ ᴡɪʟʟ ᴛᴀᴋᴇ ᴏɴᴇ ʜᴏᴜʀ ᴀᴘᴘʀᴏx ɪɴ ᴅᴀʏ ᴛɪᴍᴇ.\n"
            "ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ɢɪᴠᴇɴ ʙᴇʟʟᴏᴡ ʙᴇᴄᴀᴜsᴇ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ ʏᴏᴜ ᴄᴀɴ ᴡᴀᴛᴄʜ ᴏᴜʀ ᴄᴏɴᴛᴇɴᴛ. ᴀɴᴅ ᴛʜᴀɴᴋ ʏᴏᴜ ғᴏʀ ᴘᴜʀᴄʜᴀsɪɴɢ ᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ.</b>",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🏠 Home", callback_data="start"),
                    InlineKeyboardButton("Channel Link", url="https://t.me/+f4n8nwqVzFhiMmUx")
                ]
            ])
        )
        
        # Remove from waiting list
        del waiting_for_screenshot[user_id]
    
    # Check if user is in force-sub mode
    elif await db.is_force_sub_enabled(user_id):
        # Handle request submission
        await client.send_message(
            chat_id=OWNER_ID,
            text=f"<b>New Request from User</b>\n\n"
                 f"<b>User ID:</b> <code>{user_id}</code>\n"
                 f"<b>Username:</b> @{message.from_user.username if message.from_user.username else 'N/A'}\n"
                 f"<b>Request:</b>\n{message.text}"
        )
        
        # Clear force-sub mode for this user
        await db.set_force_sub_mode(user_id, False)
        
        # Confirm to user
        await message.reply(
            "<b>✅ Your request has been submitted successfully!</b>\n\n"
            "<b>You can now continue using the bot.</b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home", callback_data="start")]
            ])
        )
    
    # If user is not waiting for anything, send default message
    else:
        await message.reply(
            "<b>ʜᴇʟʟᴏ! ᴘʟᴇᴀsᴇ ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ᴛᴏ ɴᴀᴠɪɢᴀᴛᴇ ᴛʜᴇ ʙᴏᴛ.</b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Start", callback_data="start")]
            ])
        )
