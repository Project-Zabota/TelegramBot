import telebot
import requests
from telebot import types
from threading import Thread
from flask import Flask, request

bot = telebot.TeleBot("6490766765:AAEo1jTAbJeQT3ikeJY1AXGUIu2orT93Nqg", parse_mode=None)

first_name = ''
last_name = ''
user_id = ''
user_name = ''
print('....')

is_client = False
is_backOff = False
is_shop = False

user_post = ''
type_rec = ''
sub_topic = ''
request_description = ""


@bot.message_handler(commands=['start'])
def start(message):

    global first_name, last_name, user_id, user_name
    global is_client, is_backOff, is_shop
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    user_id = message.from_user.id
    user_name = message.from_user.username
    print(first_name, last_name, user_id, user_name)

    is_client = False
    is_backOff = False
    is_shop = False

    markup = types.InlineKeyboardMarkup()
    button_client = types.InlineKeyboardButton(text='клиент', callback_data='client')
    button_employee = types.InlineKeyboardButton(text='сотрудник "Жизньмарт"', callback_data='employee')
    markup.add(button_client, button_employee)
    bot.send_message(message.chat.id, f'Здравствуйте, укажите кто вы', parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)  # переход к типу запроса
def callback_employee(call):
    global is_client, is_backOff, is_shop
    global user_post, type_rec, sub_topic
    if call.data == "employee":  # call.data это callback_data, которую мы указали при объявлении кнопки
        markup = types.InlineKeyboardMarkup()
        button_shop = types.InlineKeyboardButton(text='магазин', callback_data='shop')
        button_back_office = types.InlineKeyboardButton(text='бэк офис', callback_data='back_office')
        markup.add(button_shop, button_back_office)
        bot.send_message(call.message.chat.id, f'Уточните место работы', parse_mode='HTML', reply_markup=markup)
    elif call.data == "client":
        define_type(call.message.chat.id)
        is_client = True
    elif call.data == "shop":
        is_shop = True
        mesg = bot.send_message(call.message.chat.id, 'В каком магазине вы работаете?')
        bot.register_next_step_handler(mesg, get_text)  # запрос на текст (переходим к блоку кода ниже)
        # define_type(call.message.chat.id)
    elif call.data == "back_office":
        define_type(call.message.chat.id)
        is_backOff = True
    elif call.data == "problem":
        allNameButton_problems = [
            (('с обслуживанием', 'service'), ('client', )),
            (('с приложением', 'app'), ('client', 'back_office', 'shop')),
            (('с сайтом', 'website'), ('client', 'back_office', 'shop')),
            (('с оплатой', 'payment'), ('client', 'shop')),
            (('с доставкой', 'delivery'), ('client', )),
            (('с сервером', 'server'), ('back_office', )),
            (('с оборудованием', 'equipment'), ('back_office', 'shop')),
            (('с кассой', 'box_office'), ('shop', )),
            (('другое', 'els'), ('client', 'back_office', 'shop'))
        ]
        person = 'client' if is_client else 'shop' if is_shop else 'back_office'
        markup = createButtons(allNameButton_problems, person)
        print(person)
        user_post = person
        type_rec = "problem"
        bot.send_message(call.message.chat.id, f'С чем возникла проблема?', parse_mode='HTML', reply_markup=markup)
    else:
        print(call.data) # проблема с...
        sub_topic = call.data
        mesg = bot.send_message(call.message.chat.id, f'Опишите, что случилось', parse_mode='HTML')
        bot.register_next_step_handler(mesg, get_text_art) # get_text
        # bot.send_message(call.message.chat.id, f'Ваш запрос принят в работу', parse_mode='HTML')


def createButtons(allNameButton, person):
    markup = types.InlineKeyboardMarkup()
    for button in allNameButton:
        if person in button[1]:
            markup.add(types.InlineKeyboardButton(text=button[0][0], callback_data=button[0][1]))
    return markup


@bot.message_handler(content_types=['text'])  # если соощение это текст, то выполняем
def get_text(message):
    request = message.text  # номер или адрес магазина
    print(request)
    define_type(message.chat.id)


def get_text_art(message):
    global request_description
    request = message.text  # номер или адрес магазина
    print(request)
    bot.send_message(message.chat.id, f'Ваш запрос принят в работу', parse_mode='HTML')
    request_description = request
    # send_to_server()
    user_by_ticket[1] = message.chat.id


def define_type(chat_id):
    markup = types.InlineKeyboardMarkup()
    button_problem = types.InlineKeyboardButton(text='есть проблема', callback_data='problem')
    button_question = types.InlineKeyboardButton(text='задать вопрос', callback_data='question')
    button_reviews = types.InlineKeyboardButton(text='оставить отзыв', callback_data='reviews')
    # markup.add(button_question, button_problem, button_reviews)
    markup.add(button_question)
    markup.add(button_problem)
    markup.add(button_reviews)
    bot.send_message(chat_id, f'Чем могу помочь?', parse_mode='HTML', reply_markup=markup)


def send_to_server():
    data = {
        "id": 5,#4,
        "name":sub_topic,
        "user": {
            "name":first_name,
            "phone": user_id
        },
        "messages":{
            "sender": "CLIENT",
            "name": user_id,
            "text": request_description,
            "date": "11-02-2023 21:30"
        }
    }
    # data_json = json.dumps(data)
    # payload = {'json_payload': data_json}
    r = requests.post("http://localhost:3000/create", json=data)




# "id": 1,
    # "name": "Не работает оплата СБП",
    # "user": {
    #     "name": "",
    #     "phone": "+79000000000"
    # },
    # "employee": {
    #     "department": "CALLCENTER",
    #     "name": "Иванов Иван Иванович"
    # },
    # "messages": [
    #     {
    #         "sender": "CLIENT",
    #         "name": "+79000000000",
    #         "text": "Здравствуйте, у меня не работает оплата по СБП в магазине",
    #         "date": "11-02-2023 21:30"
    #     },


# ------ zabota_client ---------
# host_name = "localhost"
# server_port = 8080


user_by_ticket = {}
server = Flask(__name__)


@server.route("/update/", methods=['POST'])
def processUpdate():
    body = request.json
    action = body['action']
    ticket = body['ticket']
    data = body['data']
    if action == "NEW_MESSAGE":
        bot.send_message(user_by_ticket[ticket], data['text'], parse_mode='HTML')

    return ""


def bot_polling():
    bot.infinity_polling()


Thread(target=bot_polling).start()

server.run()



