import telebot
import requests
import datetime
import json
from telebot import types
from threading import Thread
from flask import Flask, request

bot = telebot.TeleBot("6490766765:AAEo1jTAbJeQT3ikeJY1AXGUIu2orT93Nqg", parse_mode=None)

print('....')


user_post = ''
type_rec = ''
sub_topic = ''
request_description = ""

ChatData = {}

TYPE_PERSON_DEFAULT = 'client'
TYPE_REQUEST_DEFAULT = 'problem'
SUBTYPE_REQUEST_DEFAULT = 'els'



@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    ChatData[chat_id] = {'userData': {'name': message.from_user.first_name,
                                      'type_person': TYPE_PERSON_DEFAULT},
                         'requestData': {'type_request': TYPE_REQUEST_DEFAULT,
                                         'subtype_request': SUBTYPE_REQUEST_DEFAULT,
                                         'request_text': None}}
    print(ChatData)

    markup = types.InlineKeyboardMarkup()
    markup.add(createButton('клиент', 'client'), createButton('сотрудник "Жизньмарт"', 'employee'))
    bot.send_message(message.chat.id, f'Здравствуйте, укажите кто вы', parse_mode='HTML', reply_markup=markup)


def createButton(title, progName):
    button = types.InlineKeyboardButton(text=title, callback_data=progName)
    return button



@bot.callback_query_handler(func=lambda call: True)  # переход к типу запроса
def callback(call):
    chat_id = call.message.chat.id
    global user_post, type_rec, sub_topic

    if call.data in ['employee', 'client', 'shop', 'back_office']:
        ChatData[chat_id]['userData']['type_person'] = call.data
        if call.data == "employee":  # call.data это callback_data, которую мы указали при объявлении кнопки
            markup = types.InlineKeyboardMarkup()
            markup.add(createButton('магазин', 'shop'), createButton('бэк офис', 'back_office'))
            bot.send_message(call.message.chat.id, f'Уточните место работы', parse_mode='HTML', reply_markup=markup)
        elif call.data == "shop":
            mesg = bot.send_message(call.message.chat.id, 'В каком магазине вы работаете?')
            bot.register_next_step_handler(mesg, get_text)  # запрос на текст (переходим к блоку кода ниже)
        else:
            define_type(call.message.chat.id)


    elif call.data == "problem":
        allNameButton_problems = [
            (('с обслуживанием', 'service'), ['client']),
            (('с приложением', 'app'), ['client', 'back_office', 'shop']),
            (('с сайтом', 'website'), ['client', 'back_office', 'shop']),
            (('с оплатой', 'payment'), ['client', 'shop']),
            (('с доставкой', 'delivery'), ['client']),
            (('с сервером', 'server'), ['back_office']),
            (('с оборудованием', 'equipment'), ['back_office', 'shop']),
            (('с кассой', 'box_office'), ['shop']),
            (('другое', 'els'), ['client', 'back_office', 'shop'])
        ]
        person = ChatData[chat_id]['userData']['type_person']
        markup = createButtonsForType(allNameButton_problems, person)
        print(person)
        user_post = person
        type_rec = "problem"
        ChatData[chat_id]['requestData']['type_request'] = call.data
        bot.send_message(call.message.chat.id, f'С чем возникла проблема?', parse_mode='HTML', reply_markup=markup)
    else:
        print(call.data) # проблема с...
        ChatData[chat_id]['requestData']['subtype_request'] = call.data
        sub_topic = call.data
        mesg = bot.send_message(call.message.chat.id, f'Опишите, что случилось', parse_mode='HTML')
        bot.register_next_step_handler(mesg, get_text_art) # get_text
        # bot.send_message(call.message.chat.id, f'Ваш запрос принят в работу', parse_mode='HTML')


def createButtonsForType(allNameButton, person):
    markup = types.InlineKeyboardMarkup()
    for button in allNameButton:
        if person in button[1]:
            markup.add(types.InlineKeyboardButton(text=button[0][0], callback_data=button[0][1]))
    return markup


@bot.message_handler(content_types=['text'])  # если соощение это текст, то выполняем
def get_text(message):
    request = message.text  # номер или адрес магазина
    print(request)
    ChatData[message.chat.id]['requestData']['request_text'] = message.text
    define_type(message.chat.id)


def get_text_art(message):
    global request_description
    request = message.text  # номер или адрес магазина
    print(request)
    bot.send_message(message.chat.id, f'Ваш запрос принят в работу', parse_mode='HTML')
    request_description = request
    send_to_server(message.chat.id)


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


def send_to_server(chat_id):
    data = {
        # "id": 5,#4,
        "id": chat_id,
        "name": ChatData[chat_id]['requestData']['subtype_request'],
        "user": {
            "name": ChatData[chat_id]['userData']['name'],
            "phone": chat_id
        },
        "messages": {
            "sender": "CLIENT",
            "name": chat_id,
            "text": ChatData[chat_id]['requestData']['request_text'],
            "date": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }
    }
    del ChatData[chat_id] #удаляем данные после отправки

    createTicket = {
        "name": sub_topic,
        "status": "status",
        "type": "Problem",
        "sender": "Client",
        "priority": 1
    }

    # data_json = json.dumps(data)
    # payload = {'json_payload': data_json}
    r = requests.post("http://localhost:5179/api/ticket", json=createTicket) # создается тикет
    addMessage = {
        "sender": "Client",
        "text": request_description,
        "timestamp": "05.12.23",
        "ticketId": r.text
    }
    user_by_ticket[int(r.text)] = chat_id
    r = requests.post("http://localhost:5179/api/ticket/message", json=addMessage)# добавляю сообщение в тикет


# bot.polling(none_stop=True)  # чтобы программа не заканчивала работу




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
def processUpdate(): # localhost:5000
    body = json.loads(request.json)
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
