import os
import telebot
from flask import Flask, request

# -------------------------------
# Setup
# -------------------------------
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

# -------------------------------
# Flask app
# -------------------------------
app = Flask(__name__)

@app.route("/" + TOKEN, methods=["POST"])
def getMessage():
    json_str = request.stream.read().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def webhook():
    return "Bot is running!", 200

# -------------------------------
# Handlers
# -------------------------------
@bot.message_handler(commands=["start"])
def start(message):
    print("✅ /start received from", message.chat.id, flush=True)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Hello 👋")
    bot.send_message(
        message.chat.id,
        "Welcome! This is a minimal bot.",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: msg.text == "Hello 👋")
def hello(message):
    bot.send_message(message.chat.id, "Hi back! 👋")

# -------------------------------
# Run local (testing only)
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

