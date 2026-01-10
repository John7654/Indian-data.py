import os, json, requests, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- WEB SERVER FOR RENDER ---
app_web = Flask('')
@app_web.route('/')
def home(): return "💠 SYSTEM ONLINE"
def run(): app_web.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

# --- CONFIGURATION ---
TOKEN = "8524842400:AAGlrcTUWLXobdI_GyCKoM0-O0yjHIbOGVY"
ADMIN_ID = 6973940391
DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

USER_DATA = load_db()

# --- STYLING HELPERS ---
def get_header(title):
    return f"<code>╔══════════════════════╗\n║    {title}    ║\n╚══════════════════════╝</code>\n\n"

# --- CORE FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    uname = update.effective_user.username or "Unknown"
    
    if uid not in USER_DATA:
        USER_DATA[uid] = {'credits': 2, 'username': uname, 'blocked': False}
        save_db(USER_DATA)

    welcome_msg = (
        f"<b>👋 Welcome to the Tech Zone, Agent!</b>\n\n"
        f"<code>[+] Status: ACTIVE\n[+] Database: ENCRYPTED\n[+] Access: GRANTED</code>\n\n"
        f"📢 <b>Join Our Network Below:</b>\n"
        f"<i>Developer: @victoriababe | Tech Master</i>"
    )
    
    kb = [
        [InlineKeyboardButton("📡 Official Channel", url="https://t.me/tech_chatx")],
        [InlineKeyboardButton("💡 Tech Updates", url="https://t.me/tech_master_a2z")],
        [InlineKeyboardButton("⚡ JOINED / ACCESS ⚡", callback_data="check_join")]
    ]
    await update.message.reply_text(welcome_msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    data = query.data
    await query.answer()

    if data == "check_join":
        msg = (
            get_header("SYSTEM ACCESS") +
            f"✅ <b>Verification Successful!</b>\n\n"
            f"<code>⚡ Credits: {USER_DATA[uid]['credits']}\n📟 ID: {uid}</code>\n\n"
            f"📥 <b>Input 10-digit Indian Number:</b>"
        )
        await query.message.edit_text(msg, parse_mode="HTML")

    elif data == "admin_menu":
        if query.from_user.id != ADMIN_ID: return
        kb = [[InlineKeyboardButton("👥 USER LIST", callback_data="u_list")],
              [InlineKeyboardButton("📊 BOT STATS", callback_data="b_stats")]]
        await query.message.edit_text(get_header("ADMIN PANEL"), reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

    elif data == "u_list":
        kb = []
        for u, info in USER_DATA.items():
            icon = "🛑" if info.get('blocked') else "🟢"
            kb.append([InlineKeyboardButton(f"{icon} {info['username']} ({u})", callback_data=f"manage_{u}")])
        kb.append([InlineKeyboardButton("⬅️ BACK", callback_data="admin_menu")])
        await query.message.edit_text("📂 <b>Target Database:</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

    elif data.startswith("manage_"):
        target = data.split("_")[1]
        u = USER_DATA[target]
        status = "BLOCKED" if u['blocked'] else "ACTIVE"
        info = (f"<code>[ TARGET PROFILE ]\n\nID: {target}\nUSER: @{u['username']}\nCREDITS: {u['credits']}\nSTATUS: {status}</code>")
        kb = [[InlineKeyboardButton("🚫 BLOCK/UNBLOCK", callback_data=f"blk_{target}")],
              [InlineKeyboardButton("➕ ADD 5 CR", callback_data=f"add5_{target}")],
              [InlineKeyboardButton("⬅️ BACK", callback_data="u_list")]]
        await query.message.edit_text(info, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

    elif data.startswith("blk_"):
        t = data.split("_")[1]
        USER_DATA[t]['blocked'] = not USER_DATA[t].get('blocked', False)
        save_db(USER_DATA)
        query.data = f"manage_{t}"
        await handle_callback(update, context)

    elif data.startswith("add5_"):
        t = data.split("_")[1]
        USER_DATA[t]['credits'] += 5
        save_db(USER_DATA)
        await query.answer(f"✅ 5 Credits added to {t}")
        query.data = f"manage_{t}"
        await handle_callback(update, context)

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if USER_DATA.get(uid, {}).get('blocked'):
        await update.message.reply_text("<code>[!] ACCESS DENIED: YOU ARE BLOCKED.</code>", parse_mode="HTML")
        return

    num = update.message.text
    if not num.isdigit() or len(num) != 10:
        await update.message.reply_text("<code>[!] ERROR: INVALID 10-DIGIT NUMBER.</code>", parse_mode="HTML")
        return

    if USER_DATA[uid]['credits'] <= 0:
        await update.message.reply_text("<code>[!] ERROR: INSUFFICIENT CREDITS.</code>", parse_mode="HTML")
        return

    status_msg = await update.message.reply_text("<code>⏳ BYPASSING FIREWALL...</code>", parse_mode="HTML")
    time.sleep(1)
    await status_msg.edit_text("<code>📡 FETCHING DATA FROM SERVER...</code>", parse_mode="HTML")

    try:
        r = requests.get(f"https://number-info-web.vercel.app/api/search?number={num}")
        USER_DATA[uid]['credits'] -= 1
        save_db(USER_DATA)
        final_res = f"<b>🔎 INFOMATION FOUND:</b>\n\n<code>{r.text}</code>\n\n<code>[-] Credit Used: 1\n[-] Remaining: {USER_DATA[uid]['credits']}</code>"
        await status_msg.edit_text(final_res, parse_mode="HTML")
    except:
        await status_msg.edit_text("<code>[!] SYSTEM ERROR: API DOWN.</code>", parse_mode="HTML")

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    kb = [[InlineKeyboardButton("🛠 OPEN ADMIN PANEL", callback_data="admin_menu")]]
    await update.message.reply_text("<code>[+] MASTER ACCESS GRANTED.</code>", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def add_cr_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t, amt = context.args[0], int(context.args[1])
        USER_DATA[t]['credits'] += amt
        save_db(USER_DATA)
        await update.message.reply_text(f"<code>[+] SUCCESS: {amt} CR ADDED TO {t}</code>", parse_mode="HTML")
    except:
        await update.message.reply_text("<code>Usage: /addcr [UID] [AMT]</code>", parse_mode="HTML")

def main():
    keep_alive()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("addcr", add_cr_cmd))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    print("CORE STARTED...")
    app.run_polling()

if __name__ == '__main__': main()
