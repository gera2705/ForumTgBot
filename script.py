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

name_input_allowed = False

selected_slot = None

succes_booking = False

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
        button_text = f"{slot}"
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
    global name_input_allowed
    global selected_slot
    expert_name = call.message.reply_markup.keyboard[0][0].callback_data.split('_')[1]
    selected_slot = call.data.split('_')[1]

    data = sheet.get_all_values()

    print(f"Data for {selected_expert}: {selected_slot}")

    for row in data:
        if row[0] == selected_expert and row[1] == selected_slot:
            print(f"Data for  {selected_expert} {row[3]}: {selected_slot}")
            if row[3]:
                bot.send_message(call.message.chat.id, "Этот слот уже заянят :( Выберите другой.")
                keyboard = telebot.types.InlineKeyboardMarkup()
                for row in call.message.reply_markup.keyboard:
                    for button in row:
                        if button.callback_data == call.data:
                            continue
                        keyboard.add(button)

                bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
                return
            
            name_input_allowed = True
            bot.send_message(call.message.chat.id, f"Введите ваше ФИО")
            bot.register_next_step_handler(call.message, handle_name_input, expert_name, selected_slot, call)
            break


def handle_name_input(message, expert_name, slot, call):
    global name_input_allowed
    global selected_slot, succes_booking
    user_name = message.text
    user_username = call.from_user.username
    user_info = f"{user_name} тг - @{user_username}"

    if name_input_allowed:

        # Изменяем статус слота в таблице
        data = sheet.get_all_values()
        for row in data:
            if row[0] == selected_expert and row[1] == selected_slot:
                if row[3]:
                    bot.send_message(call.message.chat.id, "Этот слот уже заянят :( Выберите другой.")
                    keyboard = telebot.types.InlineKeyboardMarkup()
                    for row in call.message.reply_markup.keyboard:
                        for button in row:
                            if button.callback_data == call.data:
                                continue
                            keyboard.add(button)

                    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
                    return
                else:
                    print(f"Data2 for {slot}: {selected_slot}")
                    if(slot == selected_slot):
                        row[2] = 'TRUE'
                        sheet.update_cell(data.index(row) + 1, 3, 'TRUE')
                        sheet.update_cell(data.index(row) + 1, len(row), user_info)
                        break

            # Удаляем нажатую кнопку
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        for row in call.message.reply_markup.keyboard:
            for button in row:
                if button.callback_data == call.data:
                    continue
                keyboard.add(button)
        
        if selected_slot == slot:
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)     
            bot.send_message(message.chat.id, f"Вы успешно записались к {selected_expert} на - {selected_slot}.")
            selected_slot = None

    else:
        bot.send_message(message.chat.id, f"Сначала выберите слот и эксперта.")

@bot.callback_query_handler(func=lambda call: call.data == 'back')
def handle_back_button(call):
    global current_mode
    global name_input_allowed
    if current_mode == "slots":
        current_mode = "experts"
        name_input_allowed = False

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

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "/start":
        start(message)
    else:
        bot.send_message(message.chat.id, "Введите команду /start для начала работы с ботом")


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



