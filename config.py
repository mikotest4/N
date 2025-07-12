import os
from os import environ, getenv
import logging
from logging.handlers import RotatingFileHandler

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler('bot.log', maxBytes=50000000, backupCount=10)
    ]
)

# LOGGER function that returns a logger instance
def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

#--------------------------------------------
# Bot token @Botfather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "7540338860:AAG37_VvSjWK0vBLoZVTwLBkQpNnbKPzw08")
APP_ID = int(os.environ.get("APP_ID", "28614709"))  # Your API ID from my.telegram.org
API_HASH = os.environ.get("API_HASH", "f36fd2ee6e3d3a17c4d244ff6dc1bac8")  # Your API Hash from my.telegram.org

#--------------------------------------------
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002583602391"))  # Your db channel Id
OWNER = os.environ.get("OWNER", "Mikoyae756")  # Owner username without @
OWNER_ID = int(os.environ.get("OWNER_ID", "7970350353"))  # Owner id

#--------------------------------------------
PORT = os.environ.get("PORT", "6110")

#--------------------------------------------
DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://Koi:aloksingh@cluster0.86wo9.mongodb.net/?retryWrites=true&w=majority")
DB_NAME = os.environ.get("DATABASE_NAME", "Pookies")

#--------------------------------------------
BAN_SUPPORT = os.environ.get("BAN_SUPPORT", None)
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "200"))

#--------------------------------------------
START_PIC = os.environ.get("START_PIC", "https://telegra.ph/file/e159ff1c9c3e076669a91-fdb27e80269b152e44.jpg")
FORCE_PIC = os.environ.get("FORCE_PIC", "https://telegra.ph/file/e159ff1c9c3e076669a91-fdb27e80269b152e44.jpg")

#--------------------------------------------
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "gplinks.com")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "05161838e63ca7c62e309ca1f3f87916cab6b071")
VERIFY_EXPIRE = int(os.environ.get('VERIFY_EXPIRE', "60"))  # Add time in seconds
TUT_VID = os.environ.get("TUT_VID", "https://t.me/hwdownload/3")

#--------------------------------------------
HELP_TXT = "<b>ɪ ᴀᴍ ᴊᴜsᴛ ғɪʟᴇ sʜᴀʀɪɴɢ ʙᴏᴛ. ɴᴏᴛʜɪɴɢ ʜᴇʀᴇ ʏᴏᴜ ᴄᴀɴ ɢᴏ ʙᴀᴄᴋ.\nɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴘᴀɪᴅ ʙᴏᴛ ʜᴏsᴛɪɴɢ ʏᴏᴜ ᴄᴀɴ ᴅᴍ ᴍᴇ ʜᴇʀᴇ @Yae_X_Miko</b>"
ABOUT_TXT = "<b>◈ ᴄʀᴇᴀᴛᴏʀ: <a href=https://t.me/Yae_X_Miko>『𝚈𝚊𝚎 𝙼𝚒𝚔𝚘』❋𝄗⃝🦋 ⌞𝚆𝚊𝚛𝚕𝚘𝚛𝚍𝚜⌝ ㊋</a></b>"

#--------------------------------------------
START_MSG = os.environ.get("START_MESSAGE", "<b>ʜᴇʟʟᴏ {first}\n\nɪ ᴀᴍ ғɪʟᴇ sᴛᴏʀᴇ ʙᴏᴛ, ɪ ᴄᴀɴ sᴛᴏʀᴇ ᴘʀɪᴠᴀᴛᴇ ғɪʟᴇs ɪɴ sᴘᴇᴄɪғɪᴇᴅ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴏᴛʜᴇʀ ᴜsᴇʀs ᴄᴀɴ ᴀᴄᴄᴇss ɪᴛ ғʀᴏᴍ sᴘᴇᴄɪᴀʟ ʟɪɴᴋ.</b>")
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "ʜᴇʟʟᴏ {first}\n\n<b>ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʀᴇʟᴏᴀᴅ button ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛᴇᴅ ꜰɪʟᴇ.</b>")

CMD_TXT = """<blockquote><b>» ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs:</b></blockquote>

<b>›› /dlt_time :</b> sᴇᴛ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇ
<b>›› /check_dlt_time :</b> ᴄʜᴇᴄᴋ ᴄᴜʀʀᴇɴᴛ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇ
<b>›› /dbroadcast :</b> ʙʀᴏᴀᴅᴄᴀsᴛ ᴅᴏᴄᴜᴍᴇɴᴛ / ᴠɪᴅᴇᴏ
<b>›› /ban :</b> ʙᴀɴ ᴀ ᴜꜱᴇʀ
<b>›› /unban :</b> ᴜɴʙᴀɴ ᴀ ᴜꜱᴇʀ
<b>›› /banlist :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜰ ʙᴀɴɴᴇᴅ ᴜꜱᴇʀs
<b>›› /addchnl :</b> ᴀᴅᴅ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ
<b>›› /delchnl :</b> ʀᴇᴍᴏᴠᴇ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ
<b>›› /listchnl :</b> ᴠɪᴇᴡ ᴀᴅᴅᴇᴅ ᴄʜᴀɴɴᴇʟs
<b>›› /fsub_mode :</b> ᴛᴏɢɢʟᴇ ꜰᴏʀᴄᴇ sᴜʙ ᴍᴏᴅᴇ
<b>›› /pbroadcast :</b> sᴇɴᴅ ᴘʜᴏᴛᴏ ᴛᴏ ᴀʟʟ ᴜꜱᴇʀs
<b>›› /add_admin :</b> ᴀᴅᴅ ᴀɴ ᴀᴅᴍɪɴ
<b>›› /deladmin :</b> ʀᴇᴍᴏᴠᴇ ᴀɴ ᴀᴅᴍɪɴ
<b>›› /admins :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜰ ᴀᴅᴍɪɴs
<b>›› /addpremium :</b> ᴀᴅᴅ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ
<b>›› /premium_users :</b> ʟɪsᴛ ᴀʟʟ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀs
<b>›› /remove_premium :</b> ʀᴇᴍᴏᴠᴇ ᴘʀᴇᴍɪᴜᴍ ꜰʀᴏᴍ ᴀ ᴜꜱᴇʀ
<b>›› /myplan :</b> ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ sᴛᴀᴛᴜs
<b>›› /count :</b> ᴄᴏᴜɴᴛ verifications
"""

#--------------------------------------------
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)  # set your Custom Caption here, Keep None for Disable Custom Caption
PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "True") == "True" else False  # set True if you want to prevent users from forwarding files from bot

#--------------------------------------------
# Set true if you want Disable your Channel Posts Share button
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'True'

#--------------------------------------------
BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "ʙᴀᴋᴋᴀ ! ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴍʏ ꜱᴇɴᴘᴀɪ!!"

#==========================(BUY PREMIUM)====================#
OWNER_TAG = os.environ.get("OWNER_TAG", "@Yae_X_Miko")
UPI_ID = os.environ.get("UPI_ID", "ᴀsᴋ ғʀᴏᴍ ᴏᴡɴᴇʀ")
UPI_IMAGE_URL = os.environ.get("UPI_IMAGE_URL", "https://telegra.ph/file/a4e279ec76dfb285ef297-0a72f2ad5e693e628f.jpg")

#==========================(PREMIUM PAYMENT UPI)====================#
# UPI Payment Configuration
UPI_1 = "singhzerotwo@fam"
UPI_2 = "7348433876@mbk"
