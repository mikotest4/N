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
import qrcode.constants
import io
import base64

# Dictionary to store payment sessions
payment_sessions = {}

# Dictionary to store users waiting for screenshot
waiting_for_screenshot = {}

async def generate_upi_qr(upi_id, amount, name="Premium Plan"):
    """Generate UPI QR code for payment"""
    try:
        print(f"Starting QR generation with UPI ID: {upi_id}, Amount: {amount}")
        
        # Check if UPI_ID is set
        if not upi_id or upi_id == "":
            print("Error: UPI ID is empty or not set")
            return None
        
        # Clean the UPI ID
        upi_id = str(upi_id).strip()
        
        # Basic validation
        if '@' not in upi_id:
            print(f"Error: Invalid UPI ID format (missing @): {upi_id}")
            return None
        
        # Create UPI payment URL
        upi_url = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR&tn=Premium%20Payment"
        
        print(f"Generated UPI URL: {upi_url}")
        
        # Generate QR code with simpler settings
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(upi_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to BytesIO
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        print("QR code generated successfully")
        return img_byte_arr
        
    except Exception as e:
        print(f"Error generating QR code: {e}")
        import traceback
        traceback.print_exc()
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
            
            print(f"UPI 1 selected - Days: {days}, Price: {price}")
            print(f"UPI_ID from config: {UPI_ID}")
            
            # Generate QR code for UPI 1
            qr_image = await generate_upi_qr(UPI_ID, price, "Premium Plan")
            
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
                print("QR image generation failed")
                await query.answer("Failed to generate QR code. Please check your UPI ID in config.", show_alert=True)

    # Handle UPI 2 selection
    elif data.startswith("upi2_"):
        parts = data.split("_")
        if len(parts) == 3:
            days = parts[1]
            price = parts[2]
            
            print(f"UPI 2 selected - Days: {days}, Price: {price}")
            print(f"UPI_ID from config: {UPI_ID}")
            
            # Generate QR code for UPI 2
            qr_image = await generate_upi_qr(UPI_ID, price, "Premium Plan")
            
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
                print("QR image generation failed")
                await query.answer("Failed to generate QR code. Please check your UPI ID in config.", show_alert=True)

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
