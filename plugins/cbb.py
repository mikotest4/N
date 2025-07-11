from pyrogram import Client 
from bot import Bot
from config import *
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.database import *
import requests
import urllib.parse

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
                        InlineKeyboardButton("📞 Contact Admin", url=f"https://t.me/{OWNER_TAG.replace('@', '')}")
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
                        InlineKeyboardButton("📞 Contact Admin", url=f"https://t.me/{OWNER_TAG.replace('@', '')}")
                    ],
                    [
                        InlineKeyboardButton("🔙 Back to Plans", callback_data="premium"),
                        InlineKeyboardButton("🏠 Home", callback_data="start")
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
