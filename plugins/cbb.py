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
                    InlineKeyboardButton("1 Year - 999 ₹", callback_data="plan_365_999"),
                    InlineKeyboardButton("Test Plan - 1 ₹", callback_data="plan_test_1")
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
            
            # Show UPI options
            await query.message.edit_text(
                f"Plan: {days} Days - ₹{price}\n\n"
                f"Select Payment Method:",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("UPI 1", callback_data=f"upi1_{days}_{price}"),
                        InlineKeyboardButton("UPI 2", callback_data=f"upi2_{days}_{price}")
                    ],
                    [
                        InlineKeyboardButton("❌ Cancel", callback_data="premium")
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
                            f"Plan: {days} Days - ₹{price}\n"
                            f"Payment Method: UPI 1\n\n"
                            f"📝 Instructions:\n"
                            f"1. Scan the QR code above or pay to UPI ID\n"
                            f"2. Pay exactly ₹{price}.\n"
                            f"3. Click On I Have Paid.\n\n"
                            f"Note: If You Make Payment At Night After 11 Pm Than You Have To Wait For Morning Because Owner Is Sleeping That's Why He Can't Active Your Premium If Owner Is Online Than Your Premium Will Active In A Hour So Pay At Your Own Risk After Night 11 Pm Don't Blame Owner."
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
                            f"Plan: {days} Days - ₹{price}\n"
                            f"Payment Method: UPI 2\n\n"
                            f"📝 Instructions:\n"
                            f"1. Scan the QR code above or pay to UPI ID\n"
                            f"2. Pay exactly ₹{price}.\n"
                            f"3. Click On I Have Paid.\n\n"
                            f"Note: If You Make Payment At Night After 11 Pm Than You Have To Wait For Morning Because Owner Is Sleeping That's Why He Can't Active Your Premium If Owner Is Online Than Your Premium Will Active In A Hour So Pay At Your Own Risk After Night 11 Pm Don't Blame Owner."
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

    # Handle "I Have Paid" button click for both UPI 1 and UPI 2
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
                "📸 Please send your payment screenshot for verification.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Cancel", callback_data="premium")]
                ])
            )

    # Handle Plan Purchase (Direct activation for testing)
    elif data.startswith("buy_"):
        parts = data.split("_")
        if len(parts) == 3:
            days = parts[1]
            price = parts[2]
            
            # Add premium directly (for testing purposes)
            success, expiration_time = await add_premium_user_to_db(query.from_user.id, days)
            
            if success:
                await query.message.edit_text(
                    f"✅ Premium activated successfully!\n\n"
                    f"Plan: {days} Days\n"
                    f"Expires: {expiration_time.strftime('%Y-%m-%d %H:%M:%S')} IST\n\n"
                    f"Enjoy your premium features! 🎉",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🏠 Home", callback_data="start")]
                    ])
                )
            else:
                await query.answer("Failed to activate premium. Please try again.", show_alert=True)

    # Handle Force Sub Channel Toggle
    elif data.startswith("rfs_ch_"):
        channel_id = int(data.split("_")[2])
        current_mode = await db.get_channel_mode(channel_id)
        new_mode = "off" if current_mode == "on" else "on"
        
        await db.set_channel_mode(channel_id, new_mode)
        
        # Update the message
        channels = await db.show_channels()
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

        await query.message.edit_text(
            "<b>⚡ Select a channel to toggle Force-Sub Mode:</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )

    elif data == "close":
        await query.message.delete()

# Handle screenshot uploads
@Bot.on_message(filters.photo & filters.private)
async def handle_screenshot(client: Bot, message: Message):
    user_id = message.from_user.id
    
    # Check if user is waiting for screenshot
    if user_id in waiting_for_screenshot:
        payment_info = waiting_for_screenshot[user_id]
        
        # Get user information
        user = message.from_user
        username = f"@{user.username}" if user.username else "No Username"
        
        # Forward the screenshot with payment information as caption
        await client.send_photo(
            chat_id=OWNER_ID,
            photo=message.photo.file_id,
            caption=(
                f"Payment Information\n\n"
                f"Username: {username}\n"
                f"User ID: `{user_id}`\n"
                f"Payment Selected: {payment_info['days']} Days - {payment_info['price']} ₹\n"
                f"Payment Method: {payment_info['upi_method'].upper()}"
            )
        )
        
        # Confirm to user
        await message.reply(
            "✅ Your payment screenshot has been sent to the owner for verification.\n\n"
            "⏳ Please wait for approval. You will be notified once your premium is activated.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home", callback_data="start")]
            ])
        )
        
        # Remove from waiting list
        del waiting_for_screenshot[user_id]
    
    # If user is not waiting for screenshot, ignore the photo
    else:
        pass
