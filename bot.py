import telebot
from telebot import types
import sqlite3
import os
from flask import Flask, request

# === Get token from environment variable ===
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ TOKEN not found in environment variables")

bot = telebot.TeleBot(TOKEN)

# === Flask app for webhooks ===
app = Flask(__name__)

# === Database Setup ===
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    # Users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT
                )""")
    # Orders table
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    product TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")
    # Favorites table
    c.execute("""CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    product TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")
    conn.commit()
    conn.close()

init_db()

# === Helper functions ===
def add_user(user_id, username):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def add_order(user_id, product):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, product) VALUES (?, ?)", (user_id, product))
    conn.commit()
    conn.close()

def add_favorite(user_id, product):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("INSERT INTO favorites (user_id, product) VALUES (?, ?)", (user_id, product))
    conn.commit()
    conn.close()

def get_orders(user_id):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT product, created_at FROM orders WHERE user_id = ?", (user_id,))
    data = c.fetchall()
    conn.close()
    return data

def get_favorites(user_id):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT product, created_at FROM favorites WHERE user_id = ?", (user_id,))
    data = c.fetchall()
    conn.close()
    return data

# === Bot Handlers ===
@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.from_user.id, message.from_user.username)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛒 New Orders", "⭐ Favorites")
    markup.add("📂 Categories", "ℹ️ About")
    bot.send_message(message.chat.id,
                     "👋 Welcome to My Shop Bot!\n\nChoose an option below:",
                     reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🛒 New Orders")
def new_orders(message):
    bot.send_message(message.chat.id, "Please type the product you want to order:")
    bot.register_next_step_handler(message, save_order)

def save_order(message):
    add_order(message.from_user.id, message.text)
    bot.send_message(message.chat.id, f"✅ Order saved: {message.text}")

@bot.message_handler(func=lambda m: m.text == "⭐ Favorites")
def show_favorites(message):
    favs = get_favorites(message.from_user.id)
    if favs:
        text = "⭐ Your Favorites:\n"
        for f in favs:
            text += f"- {f[0]} (added on {f[1]})\n"
    else:
        text = "You have no favorites yet."
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📂 Categories")
def categories(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📱 Electronics", callback_data="cat_electronics"))
    markup.add(types.InlineKeyboardButton("👟 Shoes", callback_data="cat_shoes"))
    bot.send_message(message.chat.id, "📂 Choose a category:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def category_selected(call):
    if call.data == "cat_electronics":
        product = "iPhone 14 - $999"
    else:
        product = "Nike Air Max - $120"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⭐ Add to Favorites", callback_data=f"fav_{product}"))
    markup.add(types.InlineKeyboardButton("🛒 Order Now", callback_data=f"order_{product}"))

    bot.send_message(call.message.chat.id, f"📦 {product}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("fav_"))
def add_to_fav(call):
    product = call.data.replace("fav_", "")
    add_favorite(call.from_user.id, product)
    bot.answer_callback_query(call.id, "⭐ Added to favorites!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("order_"))
def order_now(call):
    product = call.data.replace("order_", "")
    add_order(call.from_user.id, product)
    bot.answer_callback_query(call.id, f"✅ Order placed: {product}")

@bot.message_handler(func=lambda m: m.text == "ℹ️ About")
def about(message):
    bot.send_photo(
        message.chat.id,
        photo="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg",
        caption="🤖 *My Shop Bot*\n\nYour friendly shopping assistant.\nBrowse categories, save favorites, and place orders easily!",
        parse_mode="Markdown"
    )

# === Debug fallback ===
@bot.message_handler(func=lambda m: True)
def echo_all(message):
    print(f"[DEBUG] Received message: {message.text}")
    bot.send_message(message.chat.id, f"(debug) You said: {message.text}")

# === Flask Routes for Webhook ===
@app.route("/" + TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "🤖 Bot is running with webhooks!", 200

# === Start Flask server ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

