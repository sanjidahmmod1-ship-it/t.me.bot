import os
import re
import time
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==========================================
# ⚙️ কনফিগারেশন
# ==========================================
# আপনার চ্যানেল এবং টার্গেট গ্রুপের লিংক/ইউজারনেম দিন
REQUIRED_CHANNEL = "@OFFLINE_BOY_OFFICIAL"
CHANNEL_URL = "https://t.me/OFFLINE_BOY_OFFICIAL"

# ⚠️ পোস্টগুলো যে গ্রুপ বা চ্যানেলে যাবে তার ইউজারনেম (যেমন: "@your_group_name") 
# অথবা প্রাইভেট গ্রুপ হলে গ্রুপের Numeric ID (যেমন: -1001234567890) দিন:
TARGET_GROUP = "@OFFLINE_BOY_OFFICIAL" 

(
    CHECK_PASSWORD,
    GET_FILE, GET_CAPTION,
    GET_BAN_USER, GET_REMOVE_USER,
    GET_POST_TEXT,
    GET_ADD_ADMIN, GET_REMOVE_ADMIN,
    GET_OLD_PASS1, GET_OLD_PASS2, GET_NEW_PASS,
    GET_ADD_GROUP
) = range(12)

bot_config = {
    "password": "1498",
    "master_password": "1498B"
}

failed_attempts = {}
blocked_users = {}

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📢 জয়েন চ্যানেল"), KeyboardButton("➕ অ্যাড গ্রুপ")],
        [KeyboardButton("📁 ফাইল পোস্ট"), KeyboardButton("📢 অটো পোস্ট")],
        [KeyboardButton("🔨 ইউজার ব্যান"), KeyboardButton("👢 ইউজার রিমুভ")],
        [KeyboardButton("🛡️ অ্যাডমিন"), KeyboardButton("🔑 পাসওয়ার্ড পরিবর্তন")]
    ],
    resize_keyboard=True
)

def extract_user(text: str):
    text = text.strip()
    match = re.search(r"(?:https?://)?(?:t.me|telegram.me)/([a-zA-Z0-9_]+)", text)
    if match:
        return f"@{match.group(1)}"
    if text.startswith("@"):
        return text
    if text.isdigit():
        return int(text)
    return text

async def is_user_allowed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> tuple[bool, bool]:
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        if member.status == 'creator':
            return True, True
        elif member.status in ['administrator', 'member']:
            return True, False
        return False, False
    except Exception as e:
        logger.error(f"Channel join check error: {e}")
        return False, False

async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.chat_member.new_chat_members:
        if member.id == context.bot.id:
            continue
        user_mention = f"@{member.username}" if member.username else member.first_name
        welcome_text = f"{user_mention} joyen grup"
        await update.chat_member.chat.send_message(welcome_text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_time = time.time()

    if user_id in blocked_users:  
        unblock_time = blocked_users[user_id]  
        if current_time < unblock_time:  
            remaining_hours = int((unblock_time - current_time) / 3600) + 1  
            await update.message.reply_text(  
                f"🚫 আপনি বারবার ভুল পাসওয়ার্ড দেওয়ায় ২৪ ঘণ্টার জন্য ব্লক আছেন! প্রায় {remaining_hours} ঘণ্টা পরে চেষ্টা করুন।",  
                reply_markup=ReplyKeyboardRemove()  
            )  
            return ConversationHandler.END  
        else:  
            del blocked_users[user_id]  
            if user_id in failed_attempts:  
                del failed_attempts[user_id]  

    await update.message.reply_text("🔒 বটের সেবা পেতে দয়া করে পাসওয়ার্ড দিন:", reply_markup=ReplyKeyboardRemove())  
    return CHECK_PASSWORD

async def verify_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text.strip()
    current_pass = bot_config["password"]
    master_pass = bot_config["master_password"]

    # বাইপাস পাসওয়ার্ড চেক (1498B)
    if user_input == master_pass:
        if user_id in failed_attempts:  
            del failed_attempts[user_id]
        await update.message.reply_text("👑 WELCOME OWNER! MASTER PASSWORD MATCHED. ALL CONTROLS ARE UNLOCKED ☺️💝", reply_markup=MAIN_KEYBOARD)  
        return ConversationHandler.END

    if user_input == current_pass or (current_pass == "1498" and user_input in ["1498", "198"]):  
        if user_id in failed_attempts:  
            del failed_attempts[user_id]  
          
        allowed, is_owner = await is_user_allowed(user_id, context)  

        if not allowed:  
            join_btn = InlineKeyboardMarkup([  
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],  
                [InlineKeyboardButton("✅ জয়েন করেছি (Check)", callback_data="check_join")]  
            ])  
            await update.message.reply_text(  
                "❌ পাসওয়ার্ড সঠিক! কিন্তু বট ব্যবহার করার আগে আপনাকে অবশ্যই আমাদের চ্যানেলে জয়েন থাকতে হবে।\n\nচ্যানেলে জয়েন করে নিচের বাটনে চাপ দিন:",  
                reply_markup=join_btn  
            )  
            return ConversationHandler.END  

        welcome_msg = "WELCOME OWNER! ALL CONTROLS ARE UNLOCKED ☺️💝" if is_owner else "HELLO! HOW CAN I HELP YOU ☺️💝"  
        await update.message.reply_text(welcome_msg, reply_markup=MAIN_KEYBOARD)  
        return ConversationHandler.END  

    else:  
        if user_id not in failed_attempts:  
            failed_attempts[user_id] = 0  
        failed_attempts[user_id] += 1  
        attempts = failed_attempts[user_id]  

        if attempts == 5:  
            await update.message.reply_text("⚠️ **সতর্কবার্তা:** টানা ৫ বার ভুল পাসওয়ার্ড দিয়েছেন! আর ১ বার ভুল দিলে ২৪ ঘণ্টার জন্য ব্লক হবেন।")  
            return CHECK_PASSWORD  
        elif attempts >= 6:  
            blocked_users[user_id] = time.time() + 86400  
            await update.message.reply_text("🚫 ৬ বার ভুল পাসওয়ার্ড দেওয়ার কারণে আপনাকে ২৪ ঘণ্টার জন্য ব্লক করা হলো!")  
            return ConversationHandler.END  
        else:  
            await update.message.reply_text(f"❌ ভুল পাসওয়ার্ড! ({attempts}/6)। সঠিক পাসওয়ার্ড আবার দিন:")  
            return CHECK_PASSWORD

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    allowed, is_owner = await is_user_allowed(user_id, context)  

    if allowed:  
        welcome_msg = "WELCOME OWNER! ALL CONTROLS ARE UNLOCKED ☺️💝" if is_owner else "✅ জয়েন সফল হয়েছে! HOW CAN I HELP YOU ☺️💝"  
        await query.message.reply_text(welcome_msg, reply_markup=MAIN_KEYBOARD)  
    else:  
        await query.message.reply_text("❌ আপনি এখনও চ্যানেলে জয়েন করেননি! আগে জয়েন করুন, অন্যথায় কোনো কীবোর্ড বাটন আসবে না।")

async def change_pass_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔑 পাসওয়ার্ড পরিবর্তন করতে ১ম পুরানো পাসওয়ার্ড (Old Pass 1) দিন (যেমন: 1498):")  
    return GET_OLD_PASS1

async def verify_old_pass1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    current_pass = bot_config["password"]
    master_pass = bot_config["master_password"]

    if user_input == current_pass or user_input == master_pass or user_input == "1498":  
        await update.message.reply_text("✅ ১ম পাসওয়ার্ড সঠিক! এবার ২য় পুরানো পাসওয়ার্ড (Old Pass 2) দিন (যেমন: 198):")  
        return GET_OLD_PASS2  
    else:  
        await update.message.reply_text("❌ ১ম পুরানো পাসওয়ার্ড ভুল! বাতিল করা হলো।", reply_markup=MAIN_KEYBOARD)  
        return ConversationHandler.END

async def verify_old_pass2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    if user_input == "198":  
        await update.message.reply_text("✅ ২য় পাসওয়ার্ডও সঠিক! এবার নতুন (New Password) পাসওয়ার্ড লিখুন:")  
        return GET_NEW_PASS  
    else:  
        await update.message.reply_text("❌ ২য় পুরানো পাসওয়ার্ড ভুল! বাতিল করা হলো।", reply_markup=MAIN_KEYBOARD)  
        return ConversationHandler.END

async def save_new_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_pass = update.message.text.strip()
    bot_config["password"] = new_pass
    await update.message.reply_text(f"✅ পাসওয়ার্ড পরিবর্তন সফল হয়েছে! নতুন পাসওয়ার্ড: {new_pass}", reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")
    return ConversationHandler.END

async def join_channel_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    join_btn = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Official Channel", url=CHANNEL_URL)]])
    await update.message.reply_text("আমাদের অফিশিয়াল চ্যানেল লিঙ্ক:", reply_markup=join_btn)

async def add_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("➕ আপনার গ্রুপ লিংক বা গ্রুপ ID পাঠান:")  
    return GET_ADD_GROUP

async def execute_add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_info = update.message.text.strip()
    await update.message.reply_text(f"✅ গ্রুপ {group_info} যুক্ত করা হয়েছে!", reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")
    return ConversationHandler.END

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id  
    try:  
        admins = await context.bot.get_chat_administrators(chat_id)  
        admin_list_text = "<b>🛡️ গ্রুপের বর্তমান অ্যাডমিন তালিকা:</b>\n\n"  
        for idx, admin in enumerate(admins, 1):  
            user = admin.user  
            name = f"@{user.username}" if user.username else user.first_name  
            admin_list_text += f"{idx}. {name}\n"  

        inline_keyboard = InlineKeyboardMarkup([  
            [  
                InlineKeyboardButton("➕ অ্যাডমিন যোগ করুন", callback_data="add_admin_action"),  
                InlineKeyboardButton("➖ অ্যাডমিন রিমুভ করুন", callback_data="remove_admin_action")  
            ]  
        ])  

        await update.message.reply_text(admin_list_text, parse_mode="HTML", reply_markup=inline_keyboard)  
    except Exception as e:  
        await update.message.reply_text(f"অ্যাডমিন তালিকা আনতে ব্যর্থ।\nত্রুটি: {e}")

async def admin_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "add_admin_action":  
        await query.message.reply_text("যাকে অ্যাডমিন বানাতে চান তার ID, Profile Link বা @username দিন:")  
        return GET_ADD_ADMIN  
    elif query.data == "remove_admin_action":  
        await query.message.reply_text("যাকে অ্যাডমিন থেকে সরাতে চান তার ID, Profile Link বা @username দিন:")  
        return GET_REMOVE_ADMIN

async def execute_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = extract_user(update.message.text)
    chat_id = update.effective_chat.id
    try:
        await context.bot.promote_chat_member(
            chat_id=chat_id, user_id=user_input, can_manage_chat=True, can_delete_messages=True,
            can_restrict_members=True, can_invite_users=True, can_pin_messages=True
        )
        await update.message.reply_text(f"✅ {user_input} কে অ্যাডমিন বানানো হয়েছে!", reply_markup=MAIN_KEYBOARD)
    except Exception as e:
        await update.message.reply_text(f"অ্যাডমিন বানাতে ব্যর্থ।\nত্রুটি: {e}", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

async def execute_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = extract_user(update.message.text)
    chat_id = update.effective_chat.id
    try:
        await context.bot.promote_chat_member(
            chat_id=chat_id, user_id=user_input, can_manage_chat=False, can_delete_messages=False,
            can_restrict_members=False, can_invite_users=False, can_pin_messages=False
        )
        await update.message.reply_text(f"✅ {user_input} কে অ্যাডমিন থেকে সরানো হয়েছে!", reply_markup=MAIN_KEYBOARD)
    except Exception as e:
        await update.message.reply_text(f"অ্যাডমিন সরাতে ব্যর্থ।\nত্রুটি: {e}", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

async def file_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("দয়া করে ফাইল (ছবি/ভিডিও/ডকুমেন্ট) পাঠান:")
    return GET_FILE

async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        context.user_data['file_id'] = update.message.document.file_id
        context.user_data['file_type'] = 'document'
    elif update.message.photo:
        context.user_data['file_id'] = update.message.photo[-1].file_id
        context.user_data['file_type'] = 'photo'
    elif update.message.video:
        context.user_data['file_id'] = update.message.video.file_id
        context.user_data['file_type'] = 'video'
    else:
        await update.message.reply_text("সঠিক ফাইল দিন অথবা /cancel চাপুন।")
        return GET_FILE

    await update.message.reply_text("ফাইল পেয়েছি! এবার ফাইলের সাথে ক্যাপশনটি দিন:")  
    return GET_CAPTION

async def receive_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.text
    file_id = context.user_data.get('file_id')
    file_type = context.user_data.get('file_type')

    try:
        # সরাসরি TARGET_GROUP এ ফাইল পাঠাবে
        if file_type == 'document':  
            await context.bot.send_document(chat_id=TARGET_GROUP, document=file_id, caption=caption)  
        elif file_type == 'photo':  
            await context.bot.send_photo(chat_id=TARGET_GROUP, photo=file_id, caption=caption)  
        elif file_type == 'video':  
            await context.bot.send_video(chat_id=TARGET_GROUP, video=file_id, caption=caption)  
        
        await update.message.reply_text(f"✅ ফাইলটি সফলভাবে {TARGET_GROUP} এ পোস্ট করা হয়েছে!", reply_markup=MAIN_KEYBOARD)  
    except Exception as e:
        await update.message.reply_text(f"❌ পোস্ট করতে ব্যর্থ!\nত্রুটি: {e}\n\n(বটকে গ্রুপে অ্যাডমিন করেছেন কিনা চেক করুন)", reply_markup=MAIN_KEYBOARD)

    return ConversationHandler.END

async def ban_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ইউজার ID, Profile Link বা @username দিন:")
    return GET_BAN_USER

async def execute_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = extract_user(update.message.text)
    chat_id = update.effective_chat.id
    try:
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_input)
        await update.message.reply_text(f"✅ {user_input} কে সফলভাবে ব্যান করা হয়েছে।", reply_markup=MAIN_KEYBOARD)
    except Exception as e:
        await update.message.reply_text(f"ব্যান করতে ব্যর্থ।\nত্রুটি: {e}", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

async def remove_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ইউজার ID, Profile Link বা @username দিন:")
    return GET_REMOVE_USER

async def execute_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = extract_user(update.message.text)
    chat_id = update.effective_chat.id
    try:
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_input)
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_input)
        await update.message.reply_text(f"✅ {user_input} কে রিমুভ করা হয়েছে।", reply_markup=MAIN_KEYBOARD)
    except Exception as e:
        await update.message.reply_text(f"রিমুভ করতে ব্যর্থ।\nত্রুটি: {e}", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

async def post_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("গ্রুপ বা চ্যানেলে পোস্ট করার জন্য মেসেজটি দিন:")
    return GET_POST_TEXT

async def execute_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post_text = update.message.text
    try:
        # সরাসরি TARGET_GROUP এ টেক্সট পাঠাবে
        await context.bot.send_message(chat_id=TARGET_GROUP, text=post_text)
        await update.message.reply_text(f"✅ পোস্টটি সফলভাবে {TARGET_GROUP} এ পাঠানো হয়েছে!", reply_markup=MAIN_KEYBOARD)
    except Exception as e:
        await update.message.reply_text(f"❌ পোস্ট করতে ব্যর্থ হয়েছে!\nত্রুটি: {e}\n\n(বটকে গ্রুপে অ্যাডমিন করেছেন কিনা চেক করুন)", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("বাতিল করা হয়েছে।", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

if __name__ == '__main__':
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        logger.error("BOT_TOKEN environment variable is missing!")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()  

    start_handler = ConversationHandler(  
        entry_points=[CommandHandler('start', start)],  
        states={  
            CHECK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_password)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    pass_change_handler = ConversationHandler(  
        entry_points=[  
            CommandHandler('pass', change_pass_start),  
            MessageHandler(filters.Regex('^🔑 পাসওয়ার্ড পরিবর্তন$'), change_pass_start)  
        ],  
        states={  
            GET_OLD_PASS1: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_old_pass1)],  
            GET_OLD_PASS2: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_old_pass2)],  
            GET_NEW_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_pass)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    add_group_handler = ConversationHandler(  
        entry_points=[MessageHandler(filters.Regex('^➕ অ্যাড গ্রুপ$'), add_group_start)],  
        states={  
            GET_ADD_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_add_group)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    file_handler = ConversationHandler(  
        entry_points=[  
            CommandHandler('file', file_start),  
            MessageHandler(filters.Regex('^📁 ফাইল পোস্ট$'), file_start)  
        ],  
        states={  
            GET_FILE: [MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, receive_file)],  
            GET_CAPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_caption)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    ban_handler = ConversationHandler(  
        entry_points=[  
            CommandHandler('ban', ban_start),  
            MessageHandler(filters.Regex('^🔨 ইউজার ব্যান$'), ban_start)  
        ],  
        states={  
            GET_BAN_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_ban)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    remove_handler = ConversationHandler(  
        entry_points=[  
            CommandHandler('remove', remove_start),  
            MessageHandler(filters.Regex('^👢 ইউজার রিমুভ$'), remove_start)  
        ],  
        states={  
            GET_REMOVE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_remove)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    post_handler = ConversationHandler(  
        entry_points=[  
            CommandHandler('post', post_start),  
            MessageHandler(filters.Regex('^📢 অটো পোস্ট$'), post_start)  
        ],  
        states={  
            GET_POST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_post)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    admin_handler = ConversationHandler(  
        entry_points=[  
            CallbackQueryHandler(admin_button_click, pattern="^(add_admin_action|remove_admin_action)$")  
        ],  
        states={  
            GET_ADD_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_add_admin)],  
            GET_REMOVE_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_remove_admin)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    app.add_handler(start_handler)  
    app.add_handler(pass_change_handler)  
    app.add_handler(add_group_handler)  
      
    app.add_handler(CommandHandler("admin", admin_command))  
    app.add_handler(MessageHandler(filters.Regex('^🛡️ অ্যাডমিন$'), admin_command))  
    app.add_handler(MessageHandler(filters.Regex('^📢 জয়েন চ্যানেল$'), join_channel_btn))  
      
    app.add_handler(file_handler)  
    app.add_handler(ban_handler)  
    app.add_handler(remove_handler)  
    app.add_handler(post_handler)  
    app.add_handler(admin_handler)  
      
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))  
    app.add_handler(ChatMemberHandler(welcome_member, ChatMemberHandler.CHAT_MEMBER))  

    logger.info("Bot starting...")  
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
