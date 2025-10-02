import os
import telebot
from telebot import types
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request

# -------------------------------
# Setup
# -------------------------------
TOKEN = os.getenv("TOKEN")   # Bot token from environment
bot = telebot.TeleBot(TOKEN)

DATABASE_URL = os.getenv("DATABASE_URL")   # Postgres connection from environment
conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
cursor = conn.cursor()

# Create tables if not exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    item TEXT NOT NULL
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    item TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

# -------------------------------
# Database helper functions
# -------------------------------
def add_order(user_id, item):
    cursor.execute("INSERT INTO orders (user_id, item) VALUES (%s, %s)", (user_id, item))
    conn.commit()

def get_orders(user_id):
    cursor.execute("SELECT item FROM orders WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    return [row["item"] for row in cursor.fetchall()]

def add_favorite(user_id, item):
    cursor.execute("INSERT INTO favorites (user_id, item) VALUES (%s, %s)", (user_id, item))
    conn.commit()

def get_favorites(user_id):
    cursor.execute("SELECT item FROM favorites WHERE user_id = %s", (user_id,))
    return [row["item"] for row in cursor.fetchall()]

# -------------------------------
# Bot handlers
# -------------------------------
@bot.message_handler(commands=["start"])
def start(message):
    print(f"✅ /start received from: {message.from_user.username}")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛒 New Orders", "⭐ Favorites")
    markup.row("📂 Categories", "ℹ️ About")
    bot.send_message(
        message.chat.id,
        "Welcome! Choose an option below:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: msg.text == "🛒 New Orders")
def new_orders(message):
    add_order(message.from_user.id, "Sample Product")
    bot.send_message(message.chat.id, "Your new order has been placed!")

@bot.message_handler(func=lambda msg: msg.text == "⭐ Favorites")
def favorites(message):
    favs = get_favorites(message.from_user.id)
    if favs:
        bot.send_message(message.chat.id, "Your favorites:\n" + "\n".join(favs))
    else:
        bot.send_message(message.chat.id, "You have no favorites yet.")

@bot.message_handler(func=lambda msg: msg.text == "📂 Categories")
def categories(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Electronics", callback_data="cat_electronics"))
    markup.add(types.InlineKeyboardButton("Shoes", callback_data="cat_shoes"))
    bot.send_message(message.chat.id, "Choose a category:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "ℹ️ About")
def about(message):
    bot.send_photo(
        message.chat.id,
        photo="https://via.placeholder.com/300x200.png?text=My+Bot",
        caption="This is my shop bot. Order safely anytime 24/7!"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def category_handler(call):
    if call.data == "cat_electronics":
        bot.send_message(call.message.chat.id, "Electronics:\n- Phone\n- Laptop")
        add_favorite(call.from_user.id, "Electronics Category")
    elif call.data == "cat_shoes":
        bot.send_message(call.message.chat.id, "Shoes:\n- Sneakers\n- Sandals")
        add_favorite(call.from_user.id, "Shoes Category")

# -------------------------------
# Flask Webhook Setup (for Render)
# -------------------------------
app = Flask(__name__)

@app.route("/" + TOKEN, methods=["POST"])
def getMessage():
    json_str = request.stream.read().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def home():
    return "Bot is running!", 200

# -------------------------------
# Run local (for testing only)
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

