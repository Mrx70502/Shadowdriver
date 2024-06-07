import telebot
from telebot import types

# Настройка токена и переменных
BOT_TOKEN = '7394525328:AAEhJis7PgGoiwaUA8R04zEDAUbnEGNgi4I'
ORDER_CHAT_ID = -1002183767964  # Идентификатор чата для заказов
ADMIN_CHAT_ID = -1002183767964  # Идентификатор чата администратора

bot = telebot.TeleBot(BOT_TOKEN)

# Этапы заказа
class OrderState:
    NAME = 1
    PHONE = 2
    PICKUP = 3
    DESTINATION = 4
    TIME = 5

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    item1 = types.KeyboardButton("Заказать водителя 🚕")
    item2 = types.KeyboardButton("Отменить заказ ❌")
    markup.add(item1, item2)
    bot.send_message(message.chat.id, 'Вітаю у нашому сервісі підбору водіїв "SHADOW DRIVER", натискайте створити замовлення 😜', reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Заказать водителя 🚕":
        user_data[message.chat.id] = {}
        bot.send_message(message.chat.id, 'Як можу до вас звертатися?')
        bot.register_next_step_handler(message, get_name)
    elif message.text == "Отменить заказ ❌":
        user_data.pop(message.chat.id, None)
        bot.send_message(message.chat.id, 'Заказ отменён.', reply_markup=types.ReplyKeyboardRemove())

def get_name(message):
    user_data[message.chat.id]['name'] = message.text
    bot.send_message(message.chat.id, 'Будьте ласкаві, залиште ваш номер телефону ')
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    user_data[message.chat.id]['phone'] = message.text
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    button = types.KeyboardButton("Надіслати місцезнаходження  📍", request_location=True)
    markup.add(button)
    bot.send_message(message.chat.id, 'Звідки вас забрати? (можете надіслати геолокацію)', reply_markup=markup)
    bot.register_next_step_handler(message, get_pickup)

def get_pickup(message):
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        user_data[message.chat.id]['pickup'] = f"Локация: ({lat}, {lon})"
        user_data[message.chat.id]['pickup_waze'] = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
    else:
        user_data[message.chat.id]['pickup'] = message.text
        user_data[message.chat.id]['pickup_waze'] = None
    bot.send_message(message.chat.id, 'Вкажіть адресу призначення ')
    bot.register_next_step_handler(message, get_destination)

def get_destination(message):
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        user_data[message.chat.id]['destination'] = f"Локация: ({lat}, {lon})"
        user_data[message.chat.id]['destination_waze'] = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
    else:
        user_data[message.chat.id]['destination'] = message.text
        user_data[message.chat.id]['destination_waze'] = None
    bot.send_message(message.chat.id, 'На котру вам потрібно?')
    bot.register_next_step_handler(message, get_time)

def get_time(message):
    user_id = message.chat.id
    if user_id in user_data:
        user_data[user_id]['time'] = message.text

        order_details = (
            f"Новый заказ:\n"
            f"Имя: {user_data[user_id]['name']}\n"
            f"Телефон: {user_data[user_id]['phone']}\n"
            f"Откуда: {user_data[user_id]['pickup']}\n"
            f"Куда: {user_data[user_id]['destination']}\n"
            f"Время подачи: {user_data[user_id]['time']}"
        )

        if user_data[user_id].get('pickup_waze'):
            order_details += f"\nОткуда: {user_data[user_id]['pickup_waze']}"
        if user_data[user_id].get('destination_waze'):
            order_details += f"\nКуда: {user_data[user_id]['destination_waze']}"

        markup = types.InlineKeyboardMarkup()
        if user_data[user_id].get('pickup_waze'):
            btn_pickup = types.InlineKeyboardButton("ну что народ, погнали нахуй 🚕", url=user_data[user_id]['pickup_waze'])
            markup.add(btn_pickup)
        if user_data[user_id].get('destination_waze'):
            btn_destination = types.InlineKeyboardButton("а куда мне ехать? 📍", url=user_data[user_id]['destination_waze'])
            markup.add(btn_destination)

        bot.send_message(ORDER_CHAT_ID, order_details, reply_markup=markup)
        bot.send_message(user_id, 'Ваш запит прийнято, очікуйте на призначення водія, він вам зателефонує. Дякуємо за те що користуєтеся нашим сервісом, вдячні кожному клієнту за довіру😊')
    else:
        bot.send_message(user_id, 'Произошла ошибка при сохранении ваших данных. Пожалуйста, попробуйте сделать заказ снова.')

bot.polling()