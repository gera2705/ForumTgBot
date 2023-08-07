import telebot
import gspread
from google.oauth2.service_account import Credentials

# Ключ для Telegram бота
TELEGRAM_BOT_TOKEN = '6371702557:AAFKsUIw92jpEnQ34uNK3c_vO0P0BAfaiVY'

# Путь к файлу с учетными данными для Google Sheets API
GOOGLE_SHEETS_CREDENTIALS = 'tgbotforum-bb2b945b0889.json'

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Подключение к Google Таблицам
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(GOOGLE_SHEETS_CREDENTIALS, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key('1szZXmRmIzZm2yQ2Njf8XtDIntIV9O9QNPL5pfG8ku_Q').sheet1  # Замените на ID вашей таблицы Google Sheets

# Глобальная переменная для хранения выбранного эксперта
selected_expert = None


# Глобальная переменная для хранения текущего режима
current_mode = "experts"

# Обработка команды /start
@bot.message_handler(commands=['start'])
def start(message):
    global current_mode
    current_mode = "experts"

    bot.send_message(message.chat.id, "Привет! Это бот для записи на консультацию к эксперту:")

    # Получаем список уникальных ФИО из таблицы
    experts = list(set(sheet.col_values(1)[1:]))

    # Создаем инлайн-кнопки для каждого эксперта
    keyboard = telebot.types.InlineKeyboardMarkup()
    for expert in experts:
        keyboard.add(telebot.types.InlineKeyboardButton(text=expert, callback_data=f"expert_{expert}"))

    bot.send_message(message.chat.id, "Выберите эксперта:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('expert_'))
def handle_expert_selection(call):
    global current_mode, selected_expert
    expert_name = call.data.split('_')[1]

    selected_expert = expert_name

    # Получаем строки из таблицы для выбранного эксперта
    data = sheet.get_all_values()
    slots = [(row[1], row[2]) for row in data if row[0] == expert_name]

    keyboard = telebot.types.InlineKeyboardMarkup()
    for slot, status in slots:
        button_text = f"{slot} - {'занято' if status == 'TRUE' else 'свободно'}"
        if status == 'FALSE':
            keyboard.add(telebot.types.InlineKeyboardButton(text=button_text, callback_data=f"slot_{slot}"))

    # Добавляем кнопку "Назад"
    keyboard.add(telebot.types.InlineKeyboardButton(text="Назад", callback_data="back"))

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"Выберите слот для эксперта {expert_name}:", reply_markup=keyboard)

    # Изменяем режим на "slots"
    current_mode = "slots"

@bot.callback_query_handler(func=lambda call: call.data.startswith('slot_'))
def handle_slot_selection(call):
    expert_name = call.message.reply_markup.keyboard[0][0].callback_data.split('_')[1]
    slot = call.data.split('_')[1]

    print(f"Data for {expert_name}: {slot}")

    bot.send_message(call.message.chat.id, f"Введите ваше имя")
    bot.register_next_step_handler(call.message, handle_name_input, expert_name, slot, call)

def handle_name_input(message, expert_name, slot, call):
    user_name = message.text

    data = sheet.get_all_values()

    # Изменяем статус слота в таблице
    data = sheet.get_all_values()
    for row in data:
        if row[0] == selected_expert and row[1] == slot:
            row[2] = 'TRUE'
            sheet.update_cell(data.index(row) + 1, 3, 'TRUE')
            sheet.update_cell(data.index(row) + 1, len(row), user_name)
            break

          # Удаляем нажатую кнопку
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    for row in call.message.reply_markup.keyboard:
        for button in row:
            if button.callback_data == call.data:
                continue
            keyboard.add(button)

    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)     
    bot.send_message(message.chat.id, f"Вы успешно записались к {selected_expert} на время {slot}.")

@bot.callback_query_handler(func=lambda call: call.data == 'back')
def handle_back_button(call):
    global current_mode
    if current_mode == "slots":
        current_mode = "experts"

        # Получаем список уникальных ФИО из таблицы
        experts = list(set(sheet.col_values(1)[1:]))

        keyboard = telebot.types.InlineKeyboardMarkup()
        for expert in experts:
            keyboard.add(telebot.types.InlineKeyboardButton(text=expert, callback_data=f"expert_{expert}"))

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Выберите эксперта:", reply_markup=keyboard)
    else:
        # Код для обработки других случаев, если необходимо
        pass


if __name__ == "__main__":
    bot.polling(none_stop=True)



# from posixpath import split
# import telebot
# import gspread
# from google.oauth2.service_account import Credentials

# # Ключ для Telegram бота
# TELEGRAM_BOT_TOKEN = '6371702557:AAFKsUIw92jpEnQ34uNK3c_vO0P0BAfaiVY'

# # Путь к файлу с учетными данными для Google Sheets API
# GOOGLE_SHEETS_CREDENTIALS = 'tgbotforum-bb2b945b0889.json'

# # Инициализация бота
# bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# # Подключение к Google Таблицам
# scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# creds = Credentials.from_service_account_file(GOOGLE_SHEETS_CREDENTIALS, scopes=scope)
# client = gspread.authorize(creds)
# sheet = client.open_by_key('1szZXmRmIzZm2yQ2Njf8XtDIntIV9O9QNPL5pfG8ku_Q').sheet1  # Замените на ID вашей таблицы Google Sheets

# selected_expert = None

# # Обработка команды /start
# @bot.message_handler(commands=['start'])
# def start(message):
#     bot.send_message(message.chat.id, "Привет! Выберите эксперта:")

#     # Получаем список уникальных ФИО из таблицы
#     experts = list(set(sheet.col_values(1)[1:]))

#     # Создаем инлайн-кнопки для каждого эксперта
#     keyboard = telebot.types.InlineKeyboardMarkup()
#     for expert in experts:
#         # Добавляем метку "expert_" перед именем эксперта
#         keyboard.add(telebot.types.InlineKeyboardButton(text=expert, callback_data=f"expert_{expert}"))

#     bot.send_message(message.chat.id, "Выберите эксперта:", reply_markup=keyboard)

# # Обработка нажатия кнопки с ФИО эксперта
# @bot.callback_query_handler(func=lambda call: call.data.startswith('expert_'))
# def handle_button_click(call):

#     expert_name = call.data.split('_')[1]

#     global selected_expert
#     selected_expert = call.data.split('_')[1]

#     # Получаем строки из таблицы для выбранного эксперта
#     data = sheet.get_all_values()
#     slots = [(row[1], row[2]) for row in data if row[0] == expert_name]

#     keyboard = telebot.types.InlineKeyboardMarkup()
#     for slot, status in slots:
#         button_text = f"{slot} - {'занято' if status == 'TRUE' else 'свободно'}"
#         if status == 'FALSE':
#             # Добавляем метку "slot_" перед временем слота
#             keyboard.add(telebot.types.InlineKeyboardButton(text=button_text, callback_data=f"slot_{slot}"))

#     if len(keyboard.keyboard) > 0:
#         bot.send_message(call.message.chat.id, f"Выберите слот для эксперта {expert_name}:", reply_markup=keyboard)
#     else:
#         bot.send_message(call.message.chat.id, f"У эксперта {expert_name} нет свободных слотов.")

# # Обработка нажатия кнопки со слотом времени
# @bot.callback_query_handler(func=lambda call: call.data.startswith('slot_'))
# def handle_slot_selection(call):
#     expert_name = selected_expert
#     slot = call.data.split('_')[1]

#     print(f"Data for {expert_name}: {slot}")

#     # Изменяем статус слота в таблице
#     data = sheet.get_all_values()
#     for row in data:
#         if row[0] == expert_name and row[1] == slot:
#             row[2] = 'TRUE'
#             sheet.update_cell(data.index(row) + 1, 3, 'TRUE')
#             break

#     bot.send_message(call.message.chat.id, f"Вы успешно записались к {expert_name} на время {slot}.")



