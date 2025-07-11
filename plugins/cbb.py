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

    elif data == "premium":
        await query.message.delete()
        await client.send_message(
            chat_id=query.message.chat.id,
            text=(
                f"Hello {query.from_user.first_name} 👋\n\n"
                f"Here You Buy Premium Membership Of This Bot.\n"
                f"Some Plan Are Given Below Click On Them To Proceed."
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🧪 Test - 1 ₹ 1 Min", callback_data="plan_test_1")
                ],
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
                    InlineKeyboardButton("🔙 Back", callback_data="start")
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
                    f"💎 <b>{plan_name} Premium Plan</b>\n\n"
                    f"💰 <b>Price:</b> {price} ₹\n"
                    f"⏰ <b>Duration:</b> {plan_name}\n\n"
                    f"📱 <b>Payment Instructions:</b>\n"
                    f"1️⃣ <b>Pay {price} ₹ to the UPI ID below</b>\n"
                    f"2️⃣ <b>Take a screenshot of payment</b>\n"
                    f"3️⃣ <b>Send screenshot to admin</b>"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("💰 I Have Paid", callback_data=f"paid_{days}_{price}")
                    ],
                    [
                        InlineKeyboardButton("🔙 Back to Plans", callback_data="premium"),
                        InlineKeyboardButton("🏠 Home", callback_data="start")
                    ]
                ])
            )
        except Exception as e:
            # Fallback if QR generation fails
            await query.message.edit_text(
                text=(
                    f"💎 <b>{plan_name} Premium Plan</b>\n\n"
                    f"💰 <b>Price:</b> {price} ₹\n"
                    f"⏰ <b>Duration:</b> {plan_name}\n\n"
                    f"📱 <b>Payment Instructions:</b>\n"
                    f"1️⃣ <b>Pay {price} ₹ to UPI ID: singhzerotwo@fam</b>\n"
                    f"2️⃣ <b>Take a screenshot of payment</b>\n"
                    f"3️⃣ <b>Send screenshot to admin</b>\n\n"
                    f"⚠️ <b>QR Code generation failed. Please pay manually.</b>"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("💰 I Have Paid", callback_data=f"paid_{days}_{price}")
                    ],
                    [
                        InlineKeyboardButton("🔙 Back to Plans", callback_data="premium"),
                        InlineKeyboardButton("🏠 Home", callback_data="start")
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
                f"📸 <b>Please send your payment screenshot now.</b>\n\n"
                f"⏰ <b>You have 5 minutes to send the screenshot.</b>"
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
                f"✅ <b>Payment screenshot received!</b>\n\n"
                f"Your payment is being verified by admin.\n"
                f"You will get premium access once verified.\n\n"
                f"Thank you for your purchase! 🎉"
            )
        )
        
        # Forward screenshot to owner with payment info
        try:
            await client.send_photo(
                chat_id=OWNER_ID,
                photo=message.photo.file_id,
                caption=(
                    f"💰 <b>Payment Information</b>\n\n"
                    f"👤 <b>Username:</b> {username}\n"
                    f"🆔 <b>User ID:</b> {user_id_mono}\n"
                    f"💳 <b>Payment Selected:</b> {plan_info}\n"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{session['days']}"),
                        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
                    ]
                ])
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

# Function to add premium user to database
async def add_premium_user_to_db(user_id, days):
    try:
        # Calculate expiration date
        ist = timezone("Asia/Kolkata")
        current_time = datetime.now(ist)
        
        # Handle test plan (1 minute)
        if days == "test":
            expiration_time = current_time + timedelta(minutes=1)
        else:
            expiration_time = current_time + timedelta(days=int(days))
        
        # Format expiration timestamp
        expiration_timestamp = expiration_time.isoformat()
        
        # Check if user already exists in premium collection
        existing_user = await collection.find_one({"user_id": user_id})
        
        if existing_user:
            # Update existing user's expiration time
            await collection.update_one(
                {"user_id": user_id},
                {"$set": {"expiration_timestamp": expiration_timestamp}}
            )
        else:
            # Add new premium user
            await collection.insert_one({
                "user_id": user_id,
                "expiration_timestamp": expiration_timestamp
            })
        
        return True
    except Exception as e:
        print(f"Error adding premium user to DB: {e}")
        return False

# Handler for admin approval/rejection
@Bot.on_callback_query(filters.user(OWNER_ID))
async def handle_admin_payment_actions(client: Bot, query: CallbackQuery):
    data = query.data
    
    if data.startswith("approve_"):
        parts = data.split("_")
        user_id = int(parts[1])
        days = parts[2]
        
        try:
            # Add premium user to database
            success = await add_premium_user_to_db(user_id, days)
            
            if success:
                # Calculate expiration date for display
                ist = timezone("Asia/Kolkata")
                current_time = datetime.now(ist)
                
                if days == "test":
                    expiration_time = current_time + timedelta(minutes=1)
                    duration_text = "1 minute"
                else:
                    expiration_time = current_time + timedelta(days=int(days))
                    duration_text = f"{days} days"
                
                expiration_str = expiration_time.strftime("%d-%m-%Y %I:%M %p")
                
                # Send success message to user
                await client.send_message(
                    chat_id=user_id,
                    text=(
                        f"🎉 <b>Payment Approved!</b>\n\n"
                        f"✅ <b>Your premium membership has been activated.</b>\n"
                        f"⏰ <b>Valid until:</b> {expiration_str} IST\n"
                        f"⌛ <b>Duration:</b> {duration_text}\n\n"
                        f"Enjoy your premium features! ✨"
                    )
                )
                
                # Update admin message
                await query.message.edit_caption(
                    caption=query.message.caption + f"\n\n✅ <b>APPROVED</b> by admin\n🎯 <b>Premium activated for {duration_text}</b>",
                    reply_markup=None
                )
                
                await query.answer("Payment approved and premium activated!", show_alert=True)
            else:
                await query.answer("Failed to add premium to database!", show_alert=True)
            
        except Exception as e:
            await query.answer("Failed to approve payment!", show_alert=True)
            print(f"Error in approval: {e}")
    
    elif data.startswith("reject_"):
        parts = data.split("_")
        user_id = int(parts[1])
        
        try:
            await client.send_message(
                chat_id=user_id,
                text=(
                    f"❌ <b>Payment Rejected!</b>\n\n"
                    f"Your payment screenshot was not verified.\n"
                    f"Please contact admin: {OWNER_TAG}"
                )
            )
            
            # Update admin message
            await query.message.edit_caption(
                caption=query.message.caption + f"\n\n❌ <b>REJECTED</b> by admin",
                reply_markup=None
            )
            
            await query.answer("Payment rejected!", show_alert=True)
            
        except Exception as e:
            await query.answer("Failed to reject payment!", show_alert=True)
