import telebot
import schedule
import cx_Oracle
from users_db import UsersDB
from reports_db import ReportsDB
from plans_db import PlansDB
import cfg

bot = telebot.TeleBot(cfg.TOKEN)

db = UsersDB(cfg.USERS_DB)
reports = ReportsDB(cfg.REPORTS_DB)
plans = PlansDB(cfg.PLANS_DB)


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.from_user.id, "Здравствуйте. Я бот-помощник, который отправляет информацию о"
                                           " самом главном. За подробностями: /help ")


@bot.message_handler(commands=['help'])
def help_message(message):
    if db.user_exists(message.from_user.id) is False:
        bot.send_message(message.from_user.id,
                         "Для взаимодействия с ботом необходимо пройти регистрацию, вызвав команду /setRole")
    elif db.get_user_status(message.from_user.id) is 'Brigadier':
        bot.send_message(message.from_user.id, "Чтобы взаимодействовать с ботом "
                                               "используйте следующие команды:\n /getInfo - для получения информации после завершения смены"
                                               "\n /changeCommand - для смены команды \n /changeRole - для смены роли \n /addComment - добавить комментарий")
    elif db.get_user_status(message.from_user.id) is 'Technologist':
        bot.send_message(message.from_user.id, "Чтобы взаимодействовать с ботом "
                                               "используйте следующие команды:\n /getInfo - для получения информации после завершения смены"
                                               "\n /setPlan - для установки месячного плана \n /changeRole - для смены роли")
    elif db.get_user_status(message.from_user.id) is 'Operator':
        bot.send_message(message.from_user.id, "Чтобы взаимодействовать с ботом "
                                               "используйте следующие команды:\n /getInfo - для получения информации после завершения смены"
                                               "\n /changeCommand - для смены команды \n /changeRole - для смены роли")
    else:
        bot.send_message(message.from_user.id, "Чтобы взаимодействовать с ботом "
                                               "используйте следующие команды:\n /confirmAction - для подтверждения действий пользователей")


@bot.message_handler(commands=['getInfo'])
def get_info(message):
    conn = cx_Oracle.connect(user=cfg.USER, password=cfg.PASSWORD, host=cfg.HOST, port=cfg.PORT)
    cursor = conn.cursor()
    result = cursor.execute("SELECT FROM ORDER BY id DESC LIMIT 1").fetchall()
    if result is None:
        bot.send_message(message.from_user.id, "Тут ничего нет :(")
    else:
        # TODO тут будет запрос из их бд
        bot.send_message(message.from_user.id,
                         f"Информация о работе бригады №{n}:\nME - {ME}\nSTOPS - {stops}\nWASTE - {waste}")
    cursor.close()
    conn.close()


@bot.message_handler(commands=['setRole', 'changeRole'])
def set_role(message):
    if db.user_exists(message.from_user.id) is False:
        markup = telebot.types.InlineKeyboardMarkup(row_width=3)
        item1 = telebot.types.InlineKeyboardButton('Бригадир', callback_data='1')
        item2 = telebot.types.InlineKeyboardButton('Технолог', callback_data='2')
        item3 = telebot.types.InlineKeyboardButton('Оператор', callback_data='3')
        markup.add(item1, item2, item3)
        bot.send_message(message.from_user.id, "Выберете свою роль", reply_markup=markup)


@bot.message_handler(commands=['setPlan', 'updatePlan'])
def set_plan(message):
    if db.user_exists(message.from_user.id) is False:
        sent = bot.send_message(message.from_user.id, "Введите месячный план:")
        bot.register_next_step_handler(sent, get_plan)


def get_plan(message):
    plan = message.text
    plans.add_plan(plan)
    bot.send_message(message.from_user.id, "План сохранен")


@bot.message_handler(commands=['writeComment'])
def write_comment(message):
    if db.user_exists(message.from_user.id) is False:
        sent = bot.send_message(message.from_user.id, "Напишите комментарий:")
        bot.register_next_step_handler(sent, get_comment)


def get_comment(message):
    comment = message.text
    reports.add_report(comment)
    bot.send_message(message.from_user.id, "Комментарий успешно сохранен")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            if call.data == '1':
                db.add_user(call.from_user.id, 'Brigadier')
            elif call.data == '2':
                db.add_user(call.from_user.id, 'Technologist')
            elif call.data == '3':
                db.add_user(call.from_user.id, 'Operator')

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="Выберете свою роль", reply_markup=None)

            bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text="Пользователь добавлен")
    except Exception as e:
        print(repr(e))


@bot.message_handler(commands=['deleteUser'])
def delete_user(message):
    db.delete_user(message.from_user.id)
    bot.send_message(message.from_user.id, "Пользователь успешно удален")


if __name__ == '__main__':
    bot.polling(none_stop=True)
