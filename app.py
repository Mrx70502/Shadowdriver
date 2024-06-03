import logging
from flask import Flask, request, render_template, redirect, url_for
import requests
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Налаштування журналювання
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/request_driver', methods=['GET', 'POST'])
def request_driver():
    if request.method == 'POST':
        # Перевірка стану бота перед відправкою повідомлення
        status_url = f'https://api.telegram.org/bot{Config.BOT_TOKEN}/getMe'
        response = requests.get(status_url)

        if response.status_code != 200:
            return "Бот недоступний. Будь ласка, спробуйте пізніше.", 500

        name = request.form['name']
        phone = request.form['phone']
        style = request.form['style']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        
        # Створюємо URL для місцезнаходження клієнта на Waze
        waze_url = f"https://waze.com/ul?ll={latitude},{longitude}&navigate=yes"

        # Створюємо текст повідомлення
        message = (
            f"New Driver Request\n"
            f"Name: {name}\n"
            f"Phone: {phone}\n"
            f"Style: {style}\n"
            f"Location: {waze_url}"
        )
        
        # Створюємо inline клавіатуру з кнопкою "Принять заказ"
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "Принять заказ", "callback_data": "accept_order"}
                ]
            ]
        }

        payload = {
            'chat_id': '@drunkshadowdriver',  # Замініть на ваш ID каналу або чат ID користувача
            'text': message,
            'reply_markup': keyboard  # Додаємо inline клавіатуру до повідомлення
        }

        response = requests.post(app.config['TELEGRAM_URL'], json=payload)

        if response.status_code != 200:
            return f"Failed to send message: {response.text}", 500
        
        return redirect(url_for('home'))
    return render_template('request_driver.html')

@app.route('/callback', methods=['POST'])
def callback():
    # Обробляємо callback запити від користувачів
    data = request.json
    query = data.get('callback_query')
    if query:
        chat_id = query['message']['chat']['id']
        message_id = query['message']['message_id']
        callback_data = query['data']

        if callback_data == 'accept_order':
            # Змінюємо кнопку на "Виконується" та змінюємо колбек дані
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "Виконується", "callback_data": "in_progress"},
                        {"text": "Відмінити", "callback_data": "cancel_order"}
                    ]
                ]
            }
            edit_keyboard(chat_id, message_id, keyboard)

        elif callback_data == 'in_progress':
            # Змінюємо кнопку на "Завершено" та змінюємо колбек дані
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "Завершено", "callback_data": "completed"}
                    ]
                ]
            }
            edit_keyboard(chat_id, message_id, keyboard)

        elif callback_data == 'completed':
            # Змінюємо кнопку на "Замовлення завершено"
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "Замовлення завершено", "callback_data": "order_completed"}
                    ]
                ]
            }
            edit_keyboard(chat_id, message_id, keyboard)

    return '', 200

def edit_keyboard(chat_id, message_id, keyboard):
    # Функція для редагування inline клавіатури у повідомленні
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'reply_markup': keyboard
    }
    response = requests.post(f"https://api.telegram.org/bot{Config.BOT_TOKEN}/editMessageReplyMarkup", json=payload)
    if response.status_code != 200:
        logging.error(f"Failed to edit message reply markup: {response.text}")

if __name__ == '__main__':
    app.run(debug=True)