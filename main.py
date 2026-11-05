import telebot
import psycopg
import time
import threading
from telebot import types
from datetime import datetime

bot = telebot.TeleBot("")

conn =psycopg.connect("dbname=reminder user=postgres password=qwe host=localhost")
cur = conn.cursor()

def record_in_db(telegram_id, name_reminder, reminder_time):
    cur.execute(
        "INSERT INTO reminder(telegram_id, name, time_date) VALUES (%s, %s, %s)",
        (telegram_id, name_reminder, reminder_time)
    )
    conn.commit()

def green(text):
    return f"\033[32m{text}\033[0m"

def check_reminder():
    conn_bg = None
    cur_bg = None
    # print("запуск check_reminder")
    while True:
        # print(f"{datetime.now()}\nзапуск цикла")
        try:
            if conn_bg is None or conn_bg.closed:
                # print("создание подключения")
                conn_bg = psycopg.connect(
                    "dbname=reminder user=postgres password=qwe host=localhost",
                    autocommit=True
                )
                # print("подключение создано")
                cur_bg = conn_bg.cursor()
            
            cur_bg.execute("SELECT current_database(), NOW()")
            db_info = cur_bg.fetchone()
            # print(f"ПОДКЛЮЧЕНО К БАЗЕ: {db_info[0]}, ВРЕМЯ БАЗЫ: {db_info[1]}")
            
            # print("отправка запроса")
            cur_bg.execute(
                "SELECT id, telegram_id, name FROM reminder WHERE time_date <= NOW() AND is_sent = FALSE"    
            )
            # print("запрос выполнен")
            reminders = cur_bg.fetchall()
            # print(f"{reminders}")
            for i in reminders:
                id = i[0]
                telegram_id = i[1]
                name = i[2]
                bot.send_message(telegram_id, f"{name}")
                cur_bg.execute("UPDATE reminder SET is_sent = TRUE WHERE id = %s", (id,))
                conn_bg.commit()
                # print(f"обновлено id = {id}")
        except Exception as e:
            print(e)
            try:
                bot.send_message(8930629248, f"{e}")
            except:
                pass
            if conn_bg:
                try:
                    conn_bg.close()
                except:
                    pass
                conn_bg = None
                cur_bg = None
        # print(f"сон 10 секунд \n")
        time.sleep(10)

def viewing_reminder(telegram_id):
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name, time_date FROM reminder WHERE telegram_id = %s AND is_sent = FALSE",
                (telegram_id,)
            )
            pass_name = cur.fetchall()
            return pass_name
    except Exception as e:
        conn.rollback()
        print(f"DB error: {e}")
        return []
    

@bot.message_handler(commands=["start"])
def button_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_1 = types.KeyboardButton("Создать напоминание")
    btn_2 = types.KeyboardButton("Посмотреть напоминания")
    btn_3 = types.KeyboardButton("Измененить напоминания")
    btn_4 = types.KeyboardButton("Удаление напоминания")
    markup.row(btn_1, btn_2)
    markup.row(btn_3, btn_4)
    bot.send_message(message.chat.id, "Привет, это бот для напоминаний, выбери пожалуйста действие.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Создать напоминание")
def choice_telegram_id(message):
    markup = types.InlineKeyboardMarkup()
    btn_1 = types.InlineKeyboardButton("@ll_VreDiNa_ll", callback_data="id_1")
    btn_2 = types.InlineKeyboardButton("@j37bfu5f75", callback_data="id_2")
    btn_3 = types.InlineKeyboardButton("@dcf471", callback_dataS="id_3" )
    markup.add(btn_1, btn_2, btn_3)
    bot.send_message(message.chat.id, "Выбери пользователя для, которого будет создано напоминание:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def process_choice_telegram_id(call):
    if call.data == "id_1":
        telegram_id = 6379229451
        bot.answer_callback_query(call.id, "Был выбран пользователь @ll_VreDiNa_ll \n Теперь введи название напоминания:")
        bot.register_next_step_handler(call.message, lambda msg: process_time_reminder(msg, telegram_id))
    elif call.data == "id_2":
        telegram_id = 6447990127
        bot.answer_callback_query(call.id, "Был выбран пользователь @j37bfu5f75 \n Теперь введи название напоминания:")
        bot.register_next_step_handler(call.messege, lambda msg: process_time_reminder(msg, telegram_id))
    elif call.data == "id_3":
        telegram_id = 8930629248
        bot.answer_callback_query(call.id, lambda msg: process_time_reminder(msg, telegram_id))

def process_time_reminder(message, telegram_id):
    name_reminder = message.text
    bot.send_message(message.chat.id, "Теперь введи время и дату когда ты хочешь получить напоминание (пример, 00:00:00, дд.мм):")
    bot.register_next_step_handler(message, lambda msg: process_reminder_time(msg, name_reminder, telegram_id))

    
def process_reminder_time(message, name_reminder, telegram_id):
    reminder_time = message.text
    bot.send_message(message.chat.id, "Напоминание сохранено")
    time_str, date_str = reminder_time.split(",")
    time_str = time_str.strip()
    date_str = date_str.strip()
    current_year = datetime.now().year
    full_date_str = f"{current_year}.{date_str} {time_str}"
    reminder_datetime = datetime.strptime(full_date_str, "%Y.%d.%m %H:%M:%S")
    record_in_db(telegram_id, name_reminder, reminder_datetime)

@bot.message_handler(func=lambda message: message.text == "Посмотреть напоминания")
def view_reminder(message):
    reminders = viewing_reminder(message.from_user.id)
    if not reminders:
        bot.send_message(message.chat.id, "Нет напоминаний")
        return

    text = "\n".join(
        f"{name} — {time_date.strftime('%H:%M:%S  %d.%m.%Y')}"
        for name, time_date in reminders
    )
    bot.send_message(message.chat.id, text)
    
@bot.message_handler(func=lambda message: message.text == "Измененить напоминания")
def change_reminder(message):
    reminders = viewing_reminder(message.from_user.id)
    text = "\n".join(
        f"{name} - {time_date.strftime("%H:%M:%S  %d.%m.%Y")}"
        for name, time_date in reminders
    )
    bot.send_message(message.chat.id, f"Выбери напоминание(введи его название):\n {text} ")
    bot.register_next_step_handler(message, lambda message: process_change_reminder(message))

def process_change_reminder(message):
    name_reminder = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_1 = types.KeyboardButton("Название напоминания")
    btn_2 = types.KeyboardButton("Время напоминания")
    markup.row(btn_1, btn_2)
    bot.send_message(message.chat.id, "Отлично! Теперь выбери, что хочешь изменить", reply_markup=markup)
    bot.register_next_step_handler(message, lambda message: message, name_reminder)

@bot.message_handler(func=lambda message: message.text == "Название напоминания")
def change_name_reminder(message, name_reminder):
    bot.semd_message(message.chet.id, "Введи новое название напоминания, не более 40 символов:")
    bot.register_next_step_handler(message, lambda message: process_change_name_reminder(message, name_reminder))

def process_change_name_reminder(message, name_reminder):
    new_name_reminder = message.text
    new_name_reminder(new_name_reminder, name_reminder)




    

threading.Thread(target=check_reminder, daemon=True).start()

while True:
    try:
        bot.polling(non_stop=True, timeout=20, long_polling_timeout=20)
    except Exception as e:
        print(f"{green("polling упал:")} {e}")
        time.sleep(5)