from flask import Flask
from threading import Thread
import json
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
)

BOT_TOKEN = "8078304397:AAGk7V0bzOi1b3lUBH0FyALeNHGvmc8Ldzc"
GROUP_CHAT_ID = -1002760567924

app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is running!"

def run():
    app_web.run(host='0.0.0.0', port=8000)

Thread(target=run).start()

# === JSON storage ===
def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(data, file):
    with open(file, "w") as f:
        json.dump(data, f)

MESSAGE_LINKS_FILE = "message_links.json"
USER_DB_FILE = "users.json"
BANNED_FILE = "banned.json"
REPLY_LOG_FILE = "reply_log.json"
USER_HISTORY_FILE = "user_history.json"

message_links = load_json(MESSAGE_LINKS_FILE)
users = load_json(USER_DB_FILE)
banned = load_json(BANNED_FILE)
reply_log = load_json(REPLY_LOG_FILE)
user_history = load_json(USER_HISTORY_FILE)

# === Format Lists ===
def format_user_list():
    result = "📋 قائمة المستخدمين:\n\n"
    for uid, username in users.items():
        tag = f"@{username}" if username != "NoUsername" else f"ID: {uid}"
        result += f"• {tag}\n"
    result += f"\n🔢 العدد الكلي: {len(users)}"
    return result

def format_ban_list():
    if not banned:
        return "✅ لا يوجد أي مستخدمين محظورين."
    result = "🚫 قائمة المحظورين:\n\n"
    for uid, data in banned.items():
        tag = f"@{data['username']}" if data['username'] != "NoUsername" else f"ID: {uid}"
        reason = data.get("reason", "غير محدد")
        result += f"• {tag} — السبب: {reason}\n"
    return result

# === Welcome ===
WELCOME_TEXT = (
    "مرحبا بك . في بوت تواصل الأقسام\n\n"
    "البوت مخصص لـ : -\n"
    "• تفعيل الموقع من خلال إرسال دليل الإشتراك\n"
    "• إرسال ما ورد لكم في الاختبار\n"
    "• إرسال الملاحظات والاقتراحات\n\n"
    "ارسل رسالتك و سيتم الرد عليك في أقرب وقت 🫡"
)

keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("القناة الرئيسية", url="https://t.me/Al2qsam")],
    [InlineKeyboardButton("ابدأ", callback_data="start_again")],
    [InlineKeyboardButton("ما هو دليل الإشتراك", callback_data="guide_info")]
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or "NoUsername"
    is_new = user_id not in users
    users[user_id] = username
    save_json(users, USER_DB_FILE)

    await update.message.reply_text(WELCOME_TEXT, reply_markup=keyboard)

    if is_new:
        mention = f"@{username}" if username != "NoUsername" else f"ID: {user_id}"
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=f"✅ مستخدم جديد بدأ البوت:\n{mention}")

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start_again":
        await query.message.reply_text(WELCOME_TEXT, reply_markup=keyboard)
    elif query.data == "guide_info":
        await query.message.reply_text("دليل الإشتراك هو عبارة عن صورة لجروب دورة إيهاب او صورة الدورة من الموقع يتم إرسالها للبوت لتأكيد اشتراكك لدى ايهاب")

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    if user_id in banned:
        await update.message.reply_text("🚫 لقد تم حظرك من استخدام هذا البوت.")
        return

    username = user.username or "NoUsername"
    mention = f"@{username}" if username != "NoUsername" else "NoUsername"
    msg = update.message
    caption_text = msg.caption or ""
    full_caption = f"رسالة من: {mention} (ID: {user_id})\n{caption_text}"

    forwarded = None
    if msg.photo:
        forwarded = await context.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=msg.photo[-1].file_id, caption=full_caption)
    elif msg.document:
        forwarded = await context.bot.send_document(chat_id=GROUP_CHAT_ID, document=msg.document.file_id, caption=full_caption)
    elif msg.video:
        forwarded = await context.bot.send_video(chat_id=GROUP_CHAT_ID, video=msg.video.file_id, caption=full_caption)
    elif msg.voice:
        forwarded = await context.bot.send_voice(chat_id=GROUP_CHAT_ID, voice=msg.voice.file_id, caption=full_caption)
    elif msg.audio:
        forwarded = await context.bot.send_audio(chat_id=GROUP_CHAT_ID, audio=msg.audio.file_id, caption=full_caption)
    elif msg.text:
        forwarded = await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=f"رسالة من: {mention} (ID: {user_id})\n{msg.text}")
    else:
        await update.message.reply_text("❗ نوع الرسالة غير مدعوم حالياً.")
        return

    message_links[str(forwarded.message_id)] = user_id
    save_json(message_links, MESSAGE_LINKS_FILE)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_history.setdefault(user_id, []).append({"type": msg.effective_attachment.__class__.__name__, "time": now, "text": msg.text or caption_text})
    save_json(user_history, USER_HISTORY_FILE)

    await update.message.reply_text("✅ تم إرسال رسالتك، سيتم الرد عليك في أقرب وقت ممكن .")

async def handle_group_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        original_id = str(update.message.reply_to_message.message_id)
        if original_id in message_links:
            target_id = int(message_links[original_id])
            msg = update.message
            sent = None
            if msg.text:
                sent = await context.bot.send_message(chat_id=target_id, text=msg.text)
            elif msg.photo:
                sent = await context.bot.send_photo(chat_id=target_id, photo=msg.photo[-1].file_id, caption=msg.caption or "")
            elif msg.document:
                sent = await context.bot.send_document(chat_id=target_id, document=msg.document.file_id, caption=msg.caption or "")
            elif msg.video:
                sent = await context.bot.send_video(chat_id=target_id, video=msg.video.file_id, caption=msg.caption or "")
            elif msg.voice:
                sent = await context.bot.send_voice(chat_id=target_id, voice=msg.voice.file_id)
            elif msg.audio:
                sent = await context.bot.send_audio(chat_id=target_id, audio=msg.audio.file_id)

            if sent:
                reply_log[str(msg.message_id)] = {"chat_id": target_id, "msg_id": sent.message_id}
                save_json(reply_log, REPLY_LOG_FILE)
                await msg.reply_text("✅ تم إرسال الرد للمستخدم.")

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        mid = str(update.message.reply_to_message.message_id)
        if mid in reply_log:
            data = reply_log[mid]
            try:
                await context.bot.delete_message(chat_id=data["chat_id"], message_id=data["msg_id"])
                await update.message.reply_text("✅ تم حذف الرسالة من عند المستخدم.")
            except:
                await update.message.reply_text("❌ فشل في حذف الرسالة من عند المستخدم.")
        else:
            await update.message.reply_text("❗ لا يوجد سجل لهذه الرسالة.")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        original_id = str(update.message.reply_to_message.message_id)
        if original_id in message_links:
            user_id = message_links[original_id]
            reason = " ".join(context.args) if context.args else "غير محدد"
            username = users.get(user_id, "NoUsername")
            banned[user_id] = {"username": username, "reason": reason}
            save_json(banned, BANNED_FILE)
            await update.message.reply_text(f"🚫 تم حظر المستخدم {username}.")
    elif context.args:
        user_id = context.args[0]
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "غير محدد"
        username = users.get(user_id, "NoUsername")
        banned[user_id] = {"username": username, "reason": reason}
        save_json(banned, BANNED_FILE)
        await update.message.reply_text(f"🚫 تم حظر المستخدم {username}.")
    else:
        await update.message.reply_text("❗ استخدم: /ban [user_id] [سبب]")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        user_id = context.args[0]
        if user_id in banned:
            banned.pop(user_id)
            save_json(banned, BANNED_FILE)
            await update.message.reply_text(f"✅ تم رفع الحظر عن المستخدم.")
        else:
            await update.message.reply_text("❗ المستخدم غير موجود في قائمة الحظر.")
    else:
        await update.message.reply_text("❗ استخدم: /unban [user_id]")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=format_user_list())

async def ban_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_ban_list())

async def commands_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠️ الأوامر المتاحة:\n"
        "/start - بدء البوت\n"
        "/all <الرسالة> - إرسال إعلان إلى جميع المستخدمين\n"
        "/list - عرض قائمة المستخدمين\n"
        "/ban - حظر مستخدم عن طريق الرد أو ID\n"
        "/unban - رفع الحظر عن مستخدم\n"
        "/banlist - عرض قائمة المحظورين\n"
        "/delete - حذف رد أُرسل بالخطأ\n"
        "/history - عرض كل رسائل المستخدم\n"
        "/commands - عرض هذه الرسالة"
    )

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        original_id = str(update.message.reply_to_message.message_id)
        if original_id in message_links:
            user_id = message_links[original_id]
            history = user_history.get(user_id, [])
            if not history:
                await update.message.reply_text("❗ لا توجد رسائل سابقة لهذا المستخدم.")
                return
            result = f"📜 سجل رسائل المستخدم {user_id}:\n\n"
            for entry in history:
                result += f"🕒 {entry['time']}\n{entry.get('text', '[ملف]')}\n\n"
            await update.message.reply_text(result)
    else:
        await update.message.reply_text("❗ يجب الرد على رسالة المستخدم لاستخدام هذا الأمر.")

# ✅ NEW: Broadcast to all users
async def broadcast_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ استخدم الأمر هكذا: /all <الرسالة>")
        return
    text = " ".join(context.args)
    count = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=text)
            count += 1
        except:
            pass
    await update.message.reply_text(f"📣 تم إرسال الرسالة إلى {count} مستخدم.")

# === Application ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("delete", delete_command))
app.add_handler(CommandHandler("ban", ban_command))
app.add_handler(CommandHandler("unban", unban_command))
app.add_handler(CommandHandler("list", list_users))
app.add_handler(CommandHandler("banlist", ban_list))
app.add_handler(CommandHandler("commands", commands_list))
app.add_handler(CommandHandler("history", history_command))
app.add_handler(CommandHandler("all", broadcast_all))  # ✅ ADDED
app.add_handler(CallbackQueryHandler(handle_button))
app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_private_message))
app.add_handler(MessageHandler(filters.Chat(GROUP_CHAT_ID), handle_group_reply))

print("Bot started.")
app.run_polling()
