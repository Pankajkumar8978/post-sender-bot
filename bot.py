import os
import telebot
import requests
import time
import threading

# Set up Telegram bot
BOT_TOKEN = os.getenv("YOUR_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Define owner and admin list
OWNER_ID = 1749001913
admin_ids = [OWNER_ID]  # Add other admin user IDs if needed

# List of channels/groups to broadcast messages to
chat_ids = ["YOUR_CHANNEL_OR_GROUP_ID_1", "YOUR_CHANNEL_OR_GROUP_ID_2"]

def is_admin(user_id):
    return user_id in admin_ids

def add_admin(user_id):
    if user_id not in admin_ids:
        admin_ids.append(user_id)
        return True
    return False

def remove_admin(user_id):
    if user_id in admin_ids and user_id != OWNER_ID:
        admin_ids.remove(user_id)
        return True
    return False

def admin_only(func):
    def wrapper(message):
        if is_admin(message.from_user.id):
            return func(message)
        else:
            bot.reply_to(message, "You don't have permission to use this command.")
    return wrapper

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = "Welcome to the Telegram Post Sender Bot!\n\n" \
                "Available commands:\n" \
                "/send - Send a message to the specified channel/group (Admins only)\n" \
                "/broadcast - Broadcast a message to all configured channels/groups (Admins only)\n" \
                "/schedule - Schedule a message to be sent at a specific time (Admins only)\n" \
                "/addchat - Add a new channel/group to the broadcast list (Admins only)\n" \
                "/removechat - Remove a channel/group from the broadcast list (Admins only)\n" \
                "/listchats - List all configured channels/groups (Admins only)\n" \
                "/getchatid - Retrieve the chat ID of a channel/group\n" \
                "/addadmin - Add a user as admin (Owner only)\n" \
                "/removeadmin - Remove an admin (Owner only)\n" \
                "/help - Show this help message"
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['addadmin'])
def add_admin_command(message):
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, "Please send the user ID of the user to be added as admin.")
        bot.register_next_step_handler(message, add_admin_step)
    else:
        bot.reply_to(message, "Only the owner can use this command.")

def add_admin_step(message):
    try:
        user_id = int(message.text.strip())
        if add_admin(user_id):
            bot.reply_to(message, "User added as admin successfully!")
        else:
            bot.reply_to(message, "User is already an admin.")
    except ValueError:
        bot.reply_to(message, "Invalid user ID. Please enter a valid user ID.")

@bot.message_handler(commands=['removeadmin'])
def remove_admin_command(message):
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, "Please send the user ID of the user to be removed as admin.")
        bot.register_next_step_handler(message, remove_admin_step)
    else:
        bot.reply_to(message, "Only the owner can use this command.")

def remove_admin_step(message):
    try:
        user_id = int(message.text.strip())
        if remove_admin(user_id):
            bot.reply_to(message, "Admin removed successfully!")
        else:
            bot.reply_to(message, "User is not an admin or cannot remove the owner.")
    except ValueError:
        bot.reply_to(message, "Invalid user ID. Please enter a valid user ID.")

@bot.message_handler(commands=['send'])
@admin_only
def send_message(message):
    bot.reply_to(message, "Please send your message to be posted in the channel/group.")
    bot.register_next_step_handler(message, get_chat_id)

def get_chat_id(message):
    global message_text
    message_text = message.text.strip()
    bot.reply_to(message, "Please send the chat ID of the channel/group where the message should be posted.")
    bot.register_next_step_handler(message, post_message)

def post_message(message):
    try:
        chat_id = message.text.strip()
        bot.send_message(chat_id, message_text)
        bot.reply_to(message, "Message posted successfully!")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=['broadcast'])
@admin_only
def broadcast_message(message):
    bot.reply_to(message, "Please send your message to be broadcasted to all channels/groups.")
    bot.register_next_step_handler(message, post_broadcast)

def post_broadcast(message):
    for chat_id in chat_ids:
        try:
            bot.send_message(chat_id, message.text.strip())
        except Exception as e:
            bot.reply_to(message, f"Error sending to {chat_id}: {str(e)}")
    bot.reply_to(message, "Message broadcasted successfully!")

@bot.message_handler(commands=['schedule'])
@admin_only
def schedule_message(message):
    bot.reply_to(message, "Please send your message to be scheduled.")
    bot.register_next_step_handler(message, get_schedule_time)

def get_schedule_time(message):
    global scheduled_message
    scheduled_message = message.text.strip()
    bot.reply_to(message, "Please send the time in format 'YYYY-MM-DD HH:MM' when the message should be posted.")
    bot.register_next_step_handler(message, set_schedule)

def set_schedule(message):
    try:
        schedule_time = message.text.strip()
        schedule_timestamp = time.mktime(time.strptime(schedule_time, '%Y-%m-%d %H:%M'))
        current_timestamp = time.time()
        delay = schedule_timestamp - current_timestamp
        if delay > 0:
            threading.Timer(delay, post_scheduled_message).start()
            bot.reply_to(message, "Message scheduled successfully!")
        else:
            bot.reply_to(message, "Scheduled time is in the past. Please try again.")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

def post_scheduled_message():
    for chat_id in chat_ids:
        try:
            bot.send_message(chat_id, scheduled_message)
        except Exception as e:
            print(f"Error sending to {chat_id}: {str(e)}")

@bot.message_handler(commands=['addchat'])
@admin_only
def add_chat(message):
    bot.reply_to(message, "Please send the chat ID of the channel/group to be added.")
    bot.register_next_step_handler(message, save_chat_id)

def save_chat_id(message):
    chat_id = message.text.strip()
    if chat_id not in chat_ids:
        chat_ids.append(chat_id)
        bot.reply_to(message, "Chat ID added successfully!")
    else:
        bot.reply_to(message, "Chat ID is already in the list.")

@bot.message_handler(commands=['removechat'])
@admin_only
def remove_chat(message):
    bot.reply_to(message, "Please send the chat ID of the channel/group to be removed.")
    bot.register_next_step_handler(message, delete_chat_id)

def delete_chat_id(message):
    chat_id = message.text.strip()
    if chat_id in chat_ids:
        chat_ids.remove(chat_id)
        bot.reply_to(message, "Chat ID removed successfully!")
    else:
        bot.reply_to(message, "Chat ID not found in the list.")

@bot.message_handler(commands=['getchatid'])
def get_chat_id_command(message):
    if message.chat.type == "private":
        bot.reply_to(message, "Please add the bot to the channel/group and forward a message from there.")
    else:
        chat_id = message.chat.id
        bot.reply_to(message, f"The chat ID for this channel/group is: {chat_id}")

@bot.message_handler(commands=['listchats'])
@admin_only
def list_chats(message):
    if chat_ids:
        chat_list = "\n".join(chat_ids)
        bot.reply_to(message, f"List of configured channels/groups:\n{chat_list}")
    else:
        bot.reply_to(message, "No channels/groups have been added yet.")

# Polling
bot.polling()
