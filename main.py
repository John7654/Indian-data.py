import os
import json
import requests
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- FLASK SERVER (Render Keep Alive) ---
app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is running online!"

def run():
    app_web.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURATION ---
TOKEN = "8524842400:AAGlrcTUWLXobdI_GyCKoM0-O0yjHIbOGVY"
ADMIN_ID = 6973940391
DB_FILE = "users_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

USER_DATA = load_db()

# --- USER COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "No Username"
    
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {'credits': 2, 'username': username, 'blocked': False}
        save_db(USER_DATA)

    keyboard = [
        [InlineKeyboardButton("📢 Official Channel", url="https://t.me/tech_chatx")],
        [InlineKeyboardButton("💡 Tech Updates", url="https://t.me/tech_master_a2z")],
        [InlineKeyboardButton("✅ Joined", callback_data="check_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Welcome to the tech zone!\n\nবটটি ব্যবহার করতে নিচের বাটন থেকে আমাদের চ্যানেল ও গ্রুপে জয়েন করুন।\n\nDeveloper: @victoriababe",
        reply_markup=reply_markup
    )

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if USER_DATA.get(user_id, {}).get('blocked', False):
        await update.message.reply_text("🚫 আপনি এই বট থেকে ব্লকড! এডমিনের সাথে যোগাযোগ করুন।")
        return

    number = update.message.text
    if not number.isdigit() or len(number) != 10:
        await update.message.reply_text("❌ ভুল নম্বর! ১০ ডিজিটের নাম্বার দিন।")
        return

    if USER_DATA[user_id]['credits'] <= 0:
        await update.message.reply_text("🚫 ক্রেডিট শেষ! এডমিন থেকে ক্রেডিট নিন।")
        return

    await update.message.reply_text("🔍 তথ্য খোঁজা হচ্ছে...")
    try:
        response = requests.get(f"https://number-info-web.vercel.app/api/search?number={number}")
        result = response.text
        USER_DATA[user_id]['credits'] -= 1
        save_db(USER_DATA)
        await update.message.reply_text(f"📊 Result:\n\n`{result}`\n\n✅ অবশিষ্ট ক্রেডিট: {USER_DATA[user_id]['credits']}", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ সার্ভার সমস্যা।")

# --- ADMIN PANEL FUNCTIONS ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    keyboard = [
        [InlineKeyboardButton("👥 User List", callback_data="user_list")],
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")]
    ]
    await update.message.reply_text("🛠 **Admin Control Panel**", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = query.data
    await query.answer()

    if data == "check_join":
        await query.message.edit_text(f"✅ জয়েন সম্পূর্ন!\n\nএখন নাম্বার দিন।\n💰 ক্রেডিট: {USER_DATA.get(user_id, {}).get('credits', 0)}")

    elif data == "user_list" and query.from_user.id == ADMIN_ID:
        keyboard = []
        for uid, info in USER_DATA.items():
            status = "🚫" if info.get('blocked', False) else "✅"
            uname = info.get('username', 'Unknown')
            keyboard.append([InlineKeyboardButton(f"{status} {uname} ({uid})", callback_data=f"manage_{uid}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_admin")])
        await query.message.edit_text("📑 **ইউজার লিস্ট:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("manage_") and query.from_user.id == ADMIN_ID:
        uid = data.split("_")[1]
        user = USER_DATA.get(uid)
        status = "Blocked" if user.get('blocked', False) else "Active"
        msg = f"👤 **User Info**\n\nUID: `{uid}`\nUser: @{user.get('username')}\nCredits: {user.get('credits')}\nStatus: {status}"
        
        kb = [[InlineKeyboardButton("🚫 Block/Unblock", callback_data=f"toggle_{uid}")],
              [InlineKeyboardButton("⬅️ Back to List", callback_data="user_list")]]
        await query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data.startswith("toggle_") and query.from_user.id == ADMIN_ID:
        uid = data.split("_")[1]
        USER_DATA[uid]['blocked'] = not USER_DATA[uid].get('blocked', False)
        save_db(USER_DATA)
        # রিফ্রেশ
        query.data = f"manage_{uid}"
        await handle_callback(update, context)

    elif data == "admin_stats":
        await query.message.edit_text(f"📊 মোট ইউজার: {len(USER_DATA)} জন", 
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_admin")]]))

    elif data == "back_admin":
        keyboard = [[InlineKeyboardButton("👥 User List", callback_data="user_list")], [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")]]
        await query.message.edit_text("🛠 **Admin Control Panel**", reply_markup=InlineKeyboardMarkup(keyboard))

# --- MAIN ---
def main():
    keep_alive()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
