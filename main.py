import telebot
import requests
import datetime
import json
from telebot import types
from threading import Thread
from flask import Flask, request

bot = telebot.TeleBot("6490766765:AAEo1jTAbJeQT3ikeJY1AXGUIu2orT93Nqg", parse_mode=None)

print('....')

# TODO удалить
'''
user_post = ''
type_rec = ''
sub_topic = ''
request_description = ""
'''
ChatData = {}

TYPE_PERSON_DEFAULT = 'client'
TYPE_REQUEST_DEFAULT = 'problem'
SUBTYPE_REQUEST_DEFAULT = 'els'
ALLNAMEBUTTON_PROBLEMS = [
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



@bot.message_handler(commands=['start'])
def start(message):
    global ChatData
    chat_id = message.chat.id
    ChatData[chat_id] = {'userData': {'name': message.from_user.first_name,
                                      'type_person': TYPE_PERSON_DEFAULT},

                         'requestData': {'type_request': TYPE_REQUEST_DEFAULT,
                                         'subtype_request': SUBTYPE_REQUEST_DEFAULT,
                                         'request_text': None}}
    q1_definitionPerson(message)


def q1_definitionPerson(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(createButton('клиент', 'client'), createButton('сотрудник "Жизньмарт"', 'employee'))
    bot.send_message(message.chat.id, f'Здравствуйте, укажите кто вы', parse_mode='HTML', reply_markup=markup)


def createButton(title, progName):
    button = types.InlineKeyboardButton(text=title, callback_data=progName)
    return button


def person_identif_type(chat_id, type_person):
    global ChatData
    ChatData[chat_id]['userData']['type_person'] = type_person
    if type_person == "employee":
        markup = types.InlineKeyboardMarkup()
        markup.add(createButton('магазин', 'shop'), createButton('бэк офис', 'back_office'))
        bot.send_message(chat_id, f'Уточните место работы', parse_mode='HTML', reply_markup=markup)
    elif type_person == "shop":
        mesg = bot.send_message(chat_id, 'В каком магазине вы работаете?')
        bot.register_next_step_handler(mesg, get_text_shop)  # TODO разделить
    else:
        define_type(chat_id)


def define_type(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(createButton('есть проблема', 'problem'))
    markup.add(createButton('задать вопрос', 'question'))
    markup.add(createButton('оставить отзыв', 'reviews'))
    bot.send_message(chat_id, f'Чем могу помочь?', parse_mode='HTML', reply_markup=markup)


def request_identif_type(chat_id, type_request):
    global ChatData
    ChatData[chat_id]['requestData']['type_request'] = type_request
    if type_request == "problem":
        person = ChatData[chat_id]['userData']['type_person']
        markup = createButtonsForType(ALLNAMEBUTTON_PROBLEMS, person)  # создает кнопки по типу пользователя
        bot.send_message(chat_id, f'С чем возникла проблема?', parse_mode='HTML', reply_markup=markup)
    elif type_request == "question":
        mesg = bot.send_message(chat_id, f'Напишите ваш вопрос', parse_mode='HTML')
        bot.register_next_step_handler(mesg, get_text_art) #TODO разделить
    elif type_request == "reviews":
        mesg = bot.send_message(chat_id, f'Пожалуйста, оставте ваш отзыв ниже)', parse_mode='HTML')
        bot.register_next_step_handler(mesg, get_text_art)  # TODO разделить


def createButtonsForType(allNameButton, person):
    markup_problems_type = types.InlineKeyboardMarkup()
    for button in allNameButton:
        if person in button[1]:
            markup_problems_type.add(createButton(button[0][0], button[0][1]))
    return markup_problems_type


def problem_identif_type(chat_id, type_request):
    global ChatData
    ChatData[chat_id]['requestData']['subtype_request'] = type_request
    mesg = bot.send_message(chat_id, f'Опишите, что случилось', parse_mode='HTML')
    bot.register_next_step_handler(mesg, get_text_art)  # TODO разделить


@bot.callback_query_handler(func=lambda call: True)  # в ответ на нажатие кнопок
def callback(call):
    chat_id = call.message.chat.id

    if call.data in ['employee', 'client', 'shop', 'back_office']:
        person_identif_type(chat_id, call.data)

    elif call.data in ['problem', 'question', 'reviews']:  # кнопки типа запроса
        request_identif_type(chat_id, call.data)

    elif call.data in [problem[0][1] for problem in ALLNAMEBUTTON_PROBLEMS]:
        problem_identif_type(chat_id, call.data)


@bot.message_handler(content_types=['text'])  # если соощение это текст, то выполняем
def get_text(message): # новое сообщение от пользователя
    global ChatData
    request = message.text
    print(request)
    ChatData[message.chat.id]['requestData']['request_text'] = request
    send_to_server(message.chat.id)


def get_text_shop(message):
    global ChatData
    request = message.text  # номер или адрес магазина
    print(request)
    #TODO пока номер магазина никуда не сохраняется
    #ChatData[message.chat.id]['requestData']['request_text'] = message.text
    define_type(message.chat.id)


def get_text_art(message):  # запрос пользователя
    global ChatData
    request = message.text
    print(request)
    ChatData[message.chat.id]['requestData']['request_text'] = request
    if ChatData[message.chat.id]['requestData']['type_request'] == 'reviews':
        bot.send_message(message.chat.id, f'Спасибо за вашу обратную связь, вы помогаете нам становиться лучше)', parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, f'Ваш запрос принят в работу', parse_mode='HTML')
    print(ChatData)
    send_to_server(message.chat.id)


def send_to_server(chat_id):
    global ChatData
    # data = {
    #     # "id": 5,#4,
    #     "id": chat_id,
    #     "name": ChatData[chat_id]['requestData']['subtype_request'],
    #     "user": {
    #         "name": ChatData[chat_id]['userData']['name'],
    #         "phone": chat_id
    #     },
    #     "messages": {
    #         "sender": "CLIENT",
    #         "name": chat_id,
    #         "text": ChatData[chat_id]['requestData']['request_text'],
    #         "date": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    #     }
    # }
    # del ChatData[chat_id] #удаляем данные после отправки

    departamentMapper = {
        'client': 2,
        'shop': 1,
        'back_office': 0
    }

    user = ChatData[chat_id]
    createTicket = {
        "name": user['requestData']['request_text'],
        "webhook": "http://localhost:5000/update",
        "type": 0, #user['requestData']['type_request'].upper(),
        "departament": departamentMapper[user['userData']['type_person']],
        "sender": {
            "name": user['userData']['name'],
            "type": 0
        },
        "priority": 1 #TODO автоматизировать (1 - высокий 0 - низкий)
    }

    # data_json = json.dumps(data)
    # payload = {'json_payload': data_json}
    r = requests.post("http://localhost:5179/api/ticket", json=createTicket) # создается тикет
    addMessage = {
        "ticketId": r.text,
        "text": user['requestData']['request_text'],
        "sender": {
            "name": user['userData']['name'],
            "type": 0
        },
        "timestamp": datetime.datetime.now().strftime("%d.%m.%Y")
    }
    user_by_ticket[int(r.text)] = chat_id
    r = requests.post("http://localhost:5179/api/message/add", json=addMessage)# добавляю сообщение в тикет


# ------ zabota_client ---------
# host_name = "localhost"
# server_port = 8080

user_by_ticket = {} # пишу свой словарь
server = Flask(__name__)


@server.route("/update/", methods=['POST'])
def processUpdate(): #  TODO dict localhost:5000
    body = json.loads(request.json)
    print(body)
    action = body['action']
    ticket = body['ticket']
    data = body['data']
    if action == "NEW_MESSAGE":
        bot.send_message(user_by_ticket[ticket], data['text'], parse_mode='HTML')
    return ""

# {
#   "action": "NEW_MESSAGE",
#   "ticket": 1,
#   "data": {
#     "text": "нереальный текст"
#   }
# }


def bot_polling():
    bot.infinity_polling()


Thread(target=bot_polling).start()

server.run()
