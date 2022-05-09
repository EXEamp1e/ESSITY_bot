import telebot
import schedule
import re
from datetime import datetime
import cx_Oracle
from ourDB import OurDB
import cfg

bot = telebot.TeleBot(cfg.TOKEN)

db = OurDB(cfg.DB)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.from_user.id, "Здравствуйте. Я бот-помощник, который отправляет информацию о"
                                           " самом главном. За подробностями: /help ")


@bot.message_handler(commands=['help'])
def help_message(message):
    if db.user_exists(message.from_user.id) is False:
        bot.send_message(message.from_user.id,
                         "Для взаимодействия с ботом необходимо пройти регистрацию, вызвав команду /setRole")
    #Бригадир
    elif db.get_user_status(message.from_user.id) is 1:
        bot.send_message(message.from_user.id, "Чтобы взаимодействовать с ботом используйте следующие команды:\n "
                                               "/getInfo - для получения информации после завершения смены\n "
                                               "/changeBrigade - для смены команды \n "
                                               "/changeRole - для смены роли \n "
                                               "/addComment - добавить комментарий")
    #Технолог
    elif db.get_user_status(message.from_user.id) is 2:
        bot.send_message(message.from_user.id, "Чтобы взаимодействовать с ботом используйте следующие команды:\n "
                                               "/getInfo - для получения информации после завершения смены\n "
                                               "/setPlan - для установки месячного плана \n "
                                               "/changeRole - для смены роли")
    #Оператор
    elif db.get_user_status(message.from_user.id) is 3:
        bot.send_message(message.from_user.id, "Чтобы взаимодействовать с ботом используйте следующие команды:\n "
                                               "/getInfo - для получения информации после завершения смены\n "
                                               "/changeBrigade - для смены команды \n "
                                               "/changeRole - для смены роли")
    #Админ
    else:
        bot.send_message(message.from_user.id, "Чтобы взаимодействовать с ботом "
                                               "используйте следующие команды:\n "
                                               "/confirmAction - для подтверждения действий пользователей")


@bot.message_handler(commands=['getInfo'])
def get_info(message):
    conn = cx_Oracle.connect(cfg.USER, cfg.PASSWORD, cfg.HOST)
    cursor = conn.cursor()

    shiftCD = make_shift_code(message)
    bot.send_message(message.from_user.id, shiftCD)
    if shiftCD == 0:
        bot.send_message(message.from_user.id,
                         "Вы не можете сформировать отчёт, т.к. не принадлежите какой-либо бригаде")
    elif shiftCD == 1:
        bot.send_message(message.from_user.id, "Смена ещё не завершена")
    else:
        result = cursor.execute("SELECT * FROM PROD WHERE shift = ?", (shiftCD,)).fetchall()

        if result is None:
            bot.send_message(message.from_user.id, "Тут ничего нет :(")
        else:
            result = cursor.execute("SELECT SUM(NETPCS * KGPERPCS) FROM PROD WHERE shift = ?", (shiftCD,)).fetchone()
            prodKg = result[0]
            result = cursor.execute("SELECT SUM(MURO_KG) FROM PROD WHERE shift = ?", (shiftCD,)).fetchone()
            muroKg = result[0]
            result = cursor.execute("SELECT SUM(PRODBUDGETPCS * KGPERPCS) FROM PROD "
                                    "WHERE shift = ? AND NETOUTPUTSW = 'Y'", (shiftCD,)).fetchone()
            maxProdVelocityKg = result[0]
            if maxProdVelocityKg is None:
                maxProdVelocityKg = 0
            ME = prodKg / maxProdVelocityKg
            result = cursor.execute("SELECT SUM(NUMBERUNPLANNEDSTOP) FROM PROD WHERE shift = ?", (shiftCD,)).fetchone()
            stops = result[0]
            if muroKg == 0:
                waste = 0
            else:
                waste = (muroKg - prodKg) / muroKg

            result = cursor.execute("SELECT SHIFTDATE FROM PROD WHERE shift = ?", (shiftCD,)).fetchone()
            dateFromTable = result[0]

            db.add_report(shiftCD, ME, stops, waste)

            bot.send_message(message.from_user.id, f"Информация о работе бригады №"
                                                   f"{db.get_user_brigade(message.from_user.id)}:\n"
                                                   f"ME - {ME}\n"
                                                   f"STOPS - {stops}\n"
                                                   f"WASTE - {waste}")
            #проверка на норму
    cursor.close()
    conn.close()


def make_shift_code(message):
    n = db.get_user_brigade(message.from_user.id)
    if n == 0 or n is None:
        return 0                                # не давать возмоность сформировать (нет бригады)
    date = datetime.now()
    time = date.hour * 100 + date.minute
    if 800 <= time <= 840:
        smena = '2'
    elif 2000 <= time <= 2040:
        smena = '1'
    elif 1200 <= time <= 1300:
        smena = '1'
    else:
        return 1                                 # не давать возмоность сформировать (смена не кончилась)
    return str(date.strftime("%y%W%w") + smena + n)


#Выбор или изменение роли
@bot.message_handler(commands=['setRole', 'changeRole'])
def set_role(message):
    if str(message.from_user.id) == cfg.ADMIN_ID:
        sent = bot.send_message(message.from_user.id, "Введите id пользователя, у которого Вы хотите изменить роль:")
        bot.register_next_step_handler(sent, get_user_id_for_status_change)
    else:
        markup = telebot.types.InlineKeyboardMarkup(row_width=3)
        item1 = telebot.types.InlineKeyboardButton('Бригадир', callback_data='1')
        item2 = telebot.types.InlineKeyboardButton('Технолог', callback_data='2')
        item3 = telebot.types.InlineKeyboardButton('Оператор', callback_data='3')
        markup.add(item1, item2, item3)
        bot.send_message(message.from_user.id, "Выберете роль", reply_markup=markup)


def get_user_id_for_status_change(message):
    user_id = message.text
    sent = bot.send_message(cfg.ADMIN_ID, "Укажите роль пользователя:\n1 - Бригадир\n2 - Технолог\n3 - Оператор")
    bot.register_next_step_handler(sent, get_status_for_status_change, user_id)


def get_status_for_status_change(message, user_id):
    status = message.text
    if status is '2':
        db.add_technologist_to_requests(user_id, status)
        confirm_status_change(user_id)
    elif status is '1' or '3':
        sent = bot.send_message(cfg.ADMIN_ID, "Укажите номер бригады:")
        bot.register_next_step_handler(sent, get_brigade_for_status_change, user_id, status)
    else:
        bot.send_message(cfg.ADMIN_ID, "Роль указана некорректно. Повторите попытку")


def get_brigade_for_status_change(message, user_id, status):
    brigade = message.text
    db.add_user_to_requests(user_id, status, brigade)
    confirm_status_change(user_id)


def add_user(message, status):
    brigade = message.text
    db.add_user_to_requests(message.from_user.id, status, brigade)
    bot.send_message(message.from_user.id, "Заявка на регистрацию отправлена на рассмотрение")
    confirm_registration(message.from_user.id)


def update_user(message, status):
    brigade = message.text
    db.add_user_to_requests(message.from_user.id, status, brigade)
    bot.send_message(message.from_user.id, "Заявка на изменение роли отправлена на рассмотрение")
    confirm_status_change(message.from_user.id)


def confirm_registration(user_id):
    markup2 = telebot.types.InlineKeyboardMarkup(row_width=2)
    item4 = telebot.types.InlineKeyboardButton('Да', callback_data='4')
    item5 = telebot.types.InlineKeyboardButton('Нет', callback_data='5')
    markup2.add(item4, item5)
    bot.send_message(cfg.ADMIN_ID, "Подтвердить регистрацию пользователя с id " + str(user_id) + "?", reply_markup=markup2)


def confirm_brigade_change(user_id):
    markup3 = telebot.types.InlineKeyboardMarkup(row_width=2)
    item6 = telebot.types.InlineKeyboardButton('Да', callback_data='6')
    item7 = telebot.types.InlineKeyboardButton('Нет', callback_data='7')
    markup3.add(item6, item7)
    bot.send_message(cfg.ADMIN_ID, "Подтвердить изменение бригады для пользователя с id " + str(user_id) + "?", reply_markup=markup3)


def confirm_status_change(user_id):
    markup4 = telebot.types.InlineKeyboardMarkup(row_width=2)
    item8 = telebot.types.InlineKeyboardButton('Да', callback_data='8')
    item9 = telebot.types.InlineKeyboardButton('Нет', callback_data='9')
    markup4.add(item8, item9)
    bot.send_message(cfg.ADMIN_ID, "Подтвердить изменение роли для пользователя с id " + str(user_id) + "?", reply_markup=markup4)


#Изменение команды
@bot.message_handler(commands=['changeBrigade'])
def change_brigade(message):
    if db.get_user_brigade(message.from_user.id) is None:
        bot.send_message(message.from_user.id, "Вы не можете изменить команду, так как не состоите не в одной из них")
    elif str(message.from_user.id) == cfg.ADMIN_ID:
        sent = bot.send_message(message.from_user.id, "Введите id пользователя, у которого Вы хотите изменить номер бригады:")
        bot.register_next_step_handler(sent, get_user_id_for_brigade_change)
    else:
        sent = bot.send_message(message.from_user.id, "Введите номер бригады")
        bot.register_next_step_handler(sent, get_brigade, message.from_user.id)


def get_user_id_for_brigade_change(message):
    user_id = message.text
    sent = bot.send_message(cfg.ADMIN_ID, "Укажите номер бригады:")
    bot.register_next_step_handler(sent, get_brigade, user_id)


def get_brigade(message, user_id):
    brigade = message.text
    db.add_user_to_requests(user_id, db.get_user_status(user_id), brigade)
    confirm_brigade_change(user_id)


@bot.message_handler(commands=['setPlan', 'updatePlan'])
def set_plan(message):
    if db.update_user_status(message.from_user.id) is 2:
        sent = bot.send_message(message.from_user.id, "Введите ME:")
        bot.register_next_step_handler(sent, get_ME)
    else:
        bot.send_message(message.from_user.id, "Вы не можете воспользоваться этой командой, так как "
                                               "Вы не являетесь технологом")


def get_ME(message):
    ME = message.text
    sent = bot.send_message(message.from_user.id, "Введите stops:")
    bot.register_next_step_handler(sent, get_stops, ME)


def get_stops(message, ME):
    stops = message.text
    sent = bot.send_message(message.from_user.id, "Введите waste:")
    bot.register_next_step_handler(sent, get_waste, ME, stops)


def get_waste(message, ME, stops):
    waste = message.text
    date = datetime.now().date()
    if db.plan_exist(date) is False:
        db.add_plan(ME, stops, waste, date)
        bot.send_message(message.from_user.id, "План успешно добавлен")
    else:
        db.update_current_plan(ME, stops, waste)
        bot.send_message(message.from_user.id, "План успешно обновлен")


@bot.message_handler(commands=['deleteUser'])
def delete_user(message):
    if db.user_exists(message.from_user.id):
        db.delete_user(message.from_user.id)
        bot.send_message(message.from_user.id, "Пользователь успешно удален")
    elif message.from_user.id == cfg.ADMIN_ID:
        sent = bot.send_message(cfg.ADMIN_ID, "Введите id пользователя, которого Вы хотите удалить:")
        bot.register_next_step_handler(sent, delete_user_by_admin)
    else:
        bot.send_message(message.from_user.id, "Чтобы воспользоваться этой командой необходимо зарегистрироваться")


def delete_user_by_admin(message):
    user_id = message.text
    if db.user_exists(user_id):
        db.delete_user(user_id)
        bot.send_message(cfg.ADMIN_ID, "Пользователь успешно удален")
        bot.send_message(user_id, "Вы были удалены из системы администратором")
    else:
        bot.send_message(cfg.ADMIN_ID, "Не удается найти пользователя с таким id")


@bot.message_handler(commands=['getBrigadeList'])
def get_brigade_list(message):
    if str(message.from_user.id) == cfg.ADMIN_ID:
        sent = bot.send_message(cfg.ADMIN_ID, "Введите номер бригады, список пользователей которой "
                                              "Вы хотите посмотреть:")
        bot.register_next_step_handler(sent, get_brigade_list_by_admin)
    else:
        bot.send_message(message.from_user.id, "Вы не можете воспользоваться этой командой, так как "
                                               "Вы не являетесь администатором")


def get_brigade_list_by_admin(message):
    brigade = message.text
    result = db.get_brigade_list(brigade)
    if len(result):
        bot.send_message(message.from_user.id, "Список пользователей бригады №" + brigade)
        for i in result:
            bot.send_message(message.from_user.id, i)
    else:
        bot.send_message(message.from_user.id, "Такой бригады не существует или в ней пока нет пользователей")


# @bot.message_handler(commands=['writeComment'])
# def write_comment(message):
#     if db.user_exists(message.from_user.id) is False:
#         sent = bot.send_message(message.from_user.id, "Напишите комментарий:")
#         bot.register_next_step_handler(sent, get_comment)
#
#
# def get_comment(message):
#     comment = message.text
#     db.add_report(comment)
#     bot.send_message(message.from_user.id, "Комментарий успешно сохранен")


def get_id_from_message(message):
    result = [int(i) for i in re.findall(r'\d+', message)]
    return result[0]


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            if call.data == '1':
                sent = bot.send_message(call.from_user.id, "Введите номер своей бригады:")
                if db.user_exists(call.from_user.id) is False:
                    bot.register_next_step_handler(sent, add_user, 1)
                else:
                    bot.register_next_step_handler(sent, update_user, 1)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Выберете роль", reply_markup=None)
            elif call.data == '2':
                db.add_technologist_to_requests(call.from_user.id, 2)
                if db.user_exists(call.from_user.id) is False:
                    bot.send_message(call.from_user.id, "Запрос на добавление отправлен на рассмотрение")
                    confirm_registration(call.from_user.id)
                else:
                    bot.send_message(call.from_user.id, "Запрос на изменение рооли отправлен на рассмотрение")
                    confirm_status_change(call.from_user.id)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Выберете роль", reply_markup=None)
            elif call.data == '3':
                sent = bot.send_message(call.from_user.id, "Введите номер своей бригады:")
                if db.user_exists(call.from_user.id) is False:
                    bot.register_next_step_handler(sent, add_user, 3)
                else:
                    bot.register_next_step_handler(sent, update_user, 3)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Выберете роль", reply_markup=None)
            elif call.data == '4':
                text = call.message.text
                user_id = str(get_id_from_message(text))
                db.add_user(user_id, db.get_user_status_from_requests(user_id), db.get_user_brigade_from_requests(user_id))
                db.delete_user_from_requests(user_id)
                bot.send_message(user_id, "Регистрация прошла успешно")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Подтвердить регистрацию пользователя с id " + user_id + "?", reply_markup=None)
            elif call.data == '5':
                text = call.message.text
                user_id = str(get_id_from_message(text))
                db.delete_user_from_requests(user_id)
                bot.send_message(user_id, "Admin отклонил действие")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Подтвердить регистрацию пользователя с id " + user_id + "?", reply_markup=None)
            elif call.data == '6':
                text = call.message.text
                user_id = str(get_id_from_message(text))
                db.update_user_brigade(user_id, db.get_user_brigade_from_requests(user_id))
                db.delete_user_from_requests(user_id)
                bot.send_message(user_id, "Смена бригады прошла успешно")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Подтвердить изменение бригады для пользователя с id " + user_id + "?",
                                      reply_markup=None)
            elif call.data == '7':
                text = call.message.text
                user_id = str(get_id_from_message(text))
                db.delete_user_from_requests(user_id)
                bot.send_message(user_id, "Admin отклонил изменение бригады")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Подтвердить изменение бригады для пользователя с id " + user_id + "?",
                                      reply_markup=None)
            elif call.data == '8':
                text = call.message.text
                user_id = str(get_id_from_message(text))
                db.update_user_status(user_id, db.get_user_status_from_requests(user_id))
                db.update_user_brigade(user_id, db.get_user_brigade_from_requests(user_id))
                db.delete_user_from_requests(user_id)
                bot.send_message(user_id, "Смена роли прошла успешно")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Подтвердить изменение роли для пользователя с id " + user_id + "?",
                                      reply_markup=None)
            elif call.data == '9':
                text = call.message.text
                user_id = str(get_id_from_message(text))
                db.delete_user_from_requests(user_id)
                bot.send_message(user_id, "Admin отклонил изменение роли")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Подтвердить изменение роли для пользователя с id " + user_id + "?",
                                      reply_markup=None)
    except Exception as e:
        print(repr(e))


if __name__ == '__main__':
    bot.polling(none_stop=True)
