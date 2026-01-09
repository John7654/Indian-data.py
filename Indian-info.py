import os
import json
import requests
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- FLASK SERVER FOR RENDER ---
app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is running online!"

def run():
    app_web.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT CONFIGURATION ---
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

# --- BOT FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {'credits': 2}
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

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    await query.message.edit_text(
        f"✅ আপনার জয়েন সম্পূর্ন হয়েছে।\n\nএখন একটি ১০ ডিজিটের Indian নাম্বার দিন।\n\n💰 আপনার ক্রেডিট: {USER_DATA.get(user_id, {}).get('credits', 0)}"
    )

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    number = update.message.text

    if not number.isdigit() or len(number) != 10:
        await update.message.reply_text("❌ ভুল নম্বর! দয়া করে ১০ ডিজিটের ইন্ডিয়ান নাম্বার দিন।")
        return

    if USER_DATA.get(user_id, {}).get('credits', 0) <= 0:
        await update.message.reply_text("🚫 আপনার ক্রেডিট শেষ! আরও ক্রেডিট পেতে এডমিনের সাথে যোগাযোগ করুন।")
        return

    await update.message.reply_text("🔍 তথ্য খোঁজা হচ্ছে, দয়া করে অপেক্ষা করুন...")
    
    try:
        response = requests.get(f"https://number-info-web.vercel.app/api/search?number={number}")
        if response.status_code == 200:
            result = response.text
            USER_DATA[user_id]['credits'] -= 1
            save_db(USER_DATA)
            await update.message.reply_text(f"📊 Search Result:\n\n`{result}`\n\n✅ ১ ক্রেডিট কাটা হয়েছে। অবশিষ্ট: {USER_DATA[user_id]['credits']}", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ এপিআই থেকে তথ্য পাওয়া যায়নি।")
    except:
        await update.message.reply_text("❌ কোনো একটি সমস্যা হয়েছে।")

async def add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = context.args[0]
        amount = int(context.args[1])
        if target_id in USER_DATA:
            USER_DATA[target_id]['credits'] += amount
            save_db(USER_DATA)
            await update.message.reply_text(f"✅ User {target_id} কে {amount} ক্রেডিট দেওয়া হয়েছে।")
        else:
            await update.message.reply_text("❌ ইউজার আগে বটটি স্টার্ট করতে হবে।")
    except:
        await update.message.reply_text("সঠিক নিয়ম: `/addcredit ইউজার_আইডি পরিমাণ`", parse_mode="Markdown")

def main():
    # Flask সার্ভার চালু করা
    keep_alive()
    
    # বট চালু করা
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addcredit", add_credit))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    
    print("Bot and Server are running...")
    app.run_polling()

if __name__ == '__main__':
    main()
