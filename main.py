import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

# JSON file path for storing categories
DATABASE_FILE = "categories.json"

# Ensure the database file exists
if not os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, 'w') as f:
        json.dump({}, f)

# Helper functions to manage JSON-based data
def load_data():
    with open(DATABASE_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATABASE_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Command Handlers
def start(update: Update, context: CallbackContext):
    buttons = [
        [InlineKeyboardButton("View Categories", callback_data="view_categories")],
        [InlineKeyboardButton("Add Category", callback_data="add_category")],
        [InlineKeyboardButton("Add Image", callback_data="add_image")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text("Welcome to the Image Categorizer Bot!", reply_markup=reply_markup)

def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    data = load_data()

    if query.data == "view_categories":
        buttons = [[InlineKeyboardButton(cat, callback_data=f"category_{cat}")] for cat in data.keys()]
        buttons.append([InlineKeyboardButton("Back", callback_data="start")])
        query.edit_message_text("Choose a category:", reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data.startswith("category_"):
        category = query.data.split("_")[1]
        subcategories = data.get(category, {})
        buttons = [[InlineKeyboardButton(sub, callback_data=f"subcategory_{category}_{sub}")] for sub in subcategories.keys()]
        buttons.append([InlineKeyboardButton("Back", callback_data="view_categories")])
        query.edit_message_text(f"Subcategories in {category}:", reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data.startswith("subcategory_"):
        _, category, subcategory = query.data.split("_")
        images = data.get(category, {}).get(subcategory, [])
        if images:
            media_group = [InputMediaPhoto(file_id) for file_id in images]
            context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)
        else:
            query.edit_message_text("No images in this subcategory.")

    elif query.data == "add_category":
        query.edit_message_text("Send the name of the new category.")
        context.user_data['add_category'] = True

    elif query.data == "add_image":
        query.edit_message_text("Upload an image and send the category/subcategory (format: `category:subcategory`).")
        context.user_data['add_image'] = True

def add_category(update: Update, context: CallbackContext):
    if 'add_category' in context.user_data and context.user_data['add_category']:
        category_name = update.message.text
        data = load_data()
        if category_name in data:
            update.message.reply_text("Category already exists!")
        else:
            data[category_name] = {}
            save_data(data)
            update.message.reply_text(f"Category '{category_name}' added successfully!")
        context.user_data.pop('add_category', None)

def add_image(update: Update, context: CallbackContext):
    if 'add_image' in context.user_data and context.user_data['add_image']:
        file_id = update.message.photo[-1].file_id
        category_sub = update.message.caption
        try:
            category, subcategory = category_sub.split(":")
        except ValueError:
            update.message.reply_text("Invalid format. Use `category:subcategory`.")
            return

        data = load_data()
        if category not in data:
            update.message.reply_text("Category does not exist!")
        else:
            if subcategory not in data[category]:
                data[category][subcategory] = []
            data[category][subcategory].append(file_id)
            save_data(data)
            update.message.reply_text(f"Image added to {category}/{subcategory}!")
        context.user_data.pop('add_image', None)

# Main Function
def main():
    TOKEN = "7685817655:AAGiGlH7zrPjGwUFQLpiJPlaIpyOutvXkgU"
    updater = Updater(TOKEN)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, add_category))
    dp.add_handler(MessageHandler(Filters.photo, add_image))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
