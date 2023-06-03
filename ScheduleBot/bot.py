import datetime
import re
import humanize 
import time
import locale

from methods import Methods
from telegram import ReplyKeyboardRemove, Bot
from bot_config import Token
from keyboards import Keyboard
from db_connect import BotDB
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters

locale.setlocale(
    category=locale.LC_ALL,
    locale="Russian"
)
ADD_LESSON_NAME, ADD_LESSON_TIME, ADD_LESSON_DAY, ADD_LESSON_ROOM = range(4)
bot_db = BotDB('schedule.db')

class Starter:
    def start(update, context):
        user_id = update.effective_user.id
        group_name = bot_db.get_group_name(user_id)
        if group_name != None:
            if bot_db.is_owner(user_id) == True:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"С возвращением, староста!", reply_markup=Keyboard.owner)
            else: 
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"С возвращением!", reply_markup=Keyboard.user)

        else:
            # Если пользователь не состоит в группе, выводим сообщение об этом
            context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text="Вы не состоите ни в одной группе. Для продолжение выбирите кнопку ниже.", 
                                    reply_markup=Keyboard.new_user)

    def create_group(update, context):
        if (bot_db.user_exist(update.effective_user.id )): 
            context.bot.send_message(chat_id=update.effective_chat.id, text="Вы уже состоите в группе", 
                                     reply_markup= Keyboard.owner if bot_db.is_owner(update.effective_user.id) else Keyboard.user)
            ConversationHandler.END
        else: 
            context.bot.send_message(chat_id=update.effective_chat.id, text="Введите название группы:")
            return "CREATE_GROUP"

    def handle_create_group(update, context):
        group_name = update.message.text
        password = Methods.generate_password()
        user_id = update.effective_user.id
        user_name = update.effective_user.username
        if user_name == None: user_name = update.effective_user.first_name
        bot_db.create_group(user_id, group_name, password, user_name)
        
        context.bot.send_message(chat_id=update.effective_chat.id,
                                text=f"Группа {group_name} успешно создана.\n"
                                    f"Код пароля для присоединения к группе: {password}", 
                                    reply_markup=Keyboard.owner)
        return ConversationHandler.END

    def join_group(update, context):
        user_id = update.effective_user.id
        if (bot_db.user_exist(user_id)): 
            context.bot.send_message(chat_id=update.effective_chat.id, text="Вы уже состоите в группе", reply_markup= (Keyboard.owner if bot_db.is_owner(user_id) else Keyboard.user))
            return ConversationHandler.END
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Введите код группы для присоединения:")
            return "JOIN_GROUP"
        
    def handle_join_group(update, context):
        password = update.message.text
        user_id = update.effective_user.id
        row = bot_db.password_exist(password)
        user_name = update.effective_user.username
        if user_name == None: user_name = update.effective_user.first_name
        if row:
            group_name = row[0]
            bot_db.join_group(str(user_id), str(group_name), user_name)

            context.bot.send_message(chat_id=update.effective_chat.id,
                                    text=f"Вы успешно присоединились к группе {group_name}.",
                                    reply_markup=Keyboard.user)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                    text="Группа с указанным кодом пароля не найдена.")
        return ConversationHandler.END

class Scheduler:
    def add_lesson(update, context):
        if (bot_db.is_owner(update.effective_user.id)):
            context.bot.send_message(chat_id=update.effective_chat.id, text="Введите название предмета:", reply_markup = ReplyKeyboardRemove())
            return ADD_LESSON_NAME
        else: 
            context.bot.send_message(chat_id=update.effective_chat.id, text="У вас нет доступа к этой команде") 
            return ConversationHandler.END
            
    def handle_add_lesson_name(update, context):
        lesson_name = update.message.text
        context.user_data['lesson_name'] = lesson_name
        context.bot.send_message(chat_id=update.effective_chat.id, text="Введите аудиторию:")

        return ADD_LESSON_ROOM

    def handle_add_lesson_room(update, context): 
        lesson_room = update.message.text
        context.user_data['lesson_room'] = lesson_room
        context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите день недели:", reply_markup=Keyboard.week)
        
        return ADD_LESSON_DAY

    def handle_add_lesson_day(update, context):
        lesson_day = update.message.text
            
        if (not Methods.check_day(lesson_day)): 
            update.message.reply_text("Некоректный ввод, попробуйте снова")
            return ADD_LESSON_DAY
        
        context.user_data['lesson_day'] = lesson_day
        context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите время:", reply_markup=Keyboard.time)

        return ADD_LESSON_TIME

    def handle_add_lesson_time(update, context):
        lesson_time = update.message.text
        group_name = bot_db.get_group_name(update.effective_user.id)
        lesson_day = context.user_data['lesson_day']
        lesson_name = context.user_data['lesson_name']
        lesson_room = context.user_data['lesson_room']

        if (not Methods.check_time(lesson_time)):
            update.message.reply_text("Некоректный ввод, введите время по образцу: \nxx:xx-xx:xx")
            return ADD_LESSON_TIME

        bot_db.add_lesson(group_name, lesson_time, lesson_day, lesson_room, lesson_name)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                text="Расписание успешно обновлено.", 
                                reply_markup=Keyboard.owner)
        return ConversationHandler.END

    def get_schedule(update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите день:", reply_markup=Keyboard.today_week)
        return "GET_SCHEDULE"

    def handle_get_schedule(update, context): 
        user_id = update.effective_user.id
        group_name = bot_db.get_group_name(user_id)
        owner = bot_db.is_owner(user_id)
        day = update.message.text 
        if (day == 'Сегодня'): 
            day = datetime.datetime.today().strftime('%A').capitalize()
        
        lessons = bot_db.get_schedule(group_name, day)

        if lessons: 
            schedule_text = Methods.print_schedule(lessons, day)
            context.bot.send_message(chat_id=update.effective_chat.id, text=schedule_text, reply_markup= (Keyboard.owner if owner else Keyboard.user))
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Расписание пусто", reply_markup= (Keyboard.owner if owner else Keyboard.user))
        
        return ConversationHandler.END

class Sender: 
    def send_schedule_to_all_users(bot):
        user_ids = bot_db.get_all_users(0)
        day = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime('%A').capitalize()
        for user_data in user_ids:
            
            if (int(user_data[2]) == 0): continue 
            if (not user_data[1]): continue

            schedule = bot_db.get_schedule(bot_db.get_group_name(user_data[0]), day)
            
            if schedule:
                time.sleep(1)
                bot.send_message(chat_id=user_data[0], text=f"Ваше расписание на завтра:\n{Methods.print_schedule(schedule, day)}")
    
    def switch_notification(update, context): 
        user_id = update.effective_user.id
        if (bot_db.check_notification_status(user_id)): 
            bot_db.switch_notification(user_id, '0')
            context.bot.send_message(chat_id=user_id, text="Ежедневное уведомление о расписании в 20:00 - выключенно")
        else: 
            bot_db.switch_notification(user_id, '1')
            context.bot.send_message(chat_id=user_id, text="Ежедневное уведомление о расписании в 20:00 - включенно")
    
    def push_sender(update, context, group_name): 
        user_ids = bot_db.get_user_id_from_group(group_name)
        for i in user_ids: 
            if (int(i[1]) == 1): continue
            else:
                context.bot.send_message(chat_id=i[0], text="В группе появились новые уведомления", reply_markup = Keyboard.show)
        
class Notificator:
# Функция обработки команды /get_notifications
    def get_notifications(update, context):
        user_id = update.effective_user.id
        group_name = bot_db.get_group_name(user_id)
        now_date = datetime.datetime.today().strftime("%y.%m.%d")
        
        result = bot_db.get_notifications(now_date, group_name)
        
        notification_text = ""

        if not result:
            update.message.reply_text("В группе нет уведомлений.")
        else:
            for notification in result: 
                date = notification[1].split(".")
                notification_text += f"|{date[2]}.{date[1]}.{date[0]}| \n{notification[0]}\n\n"
            update.message.reply_text(f"Уведомления группы:\n{notification_text}", reply_markup= Keyboard.owner if bot_db.is_owner(user_id) else Keyboard.user) 
                
    # Функция обработки команды /add_notification
    def add_notification(update, context):
        if (bot_db.is_owner(update.effective_user.id)):
            update.message.reply_text("Введите текст уведомления:")
            return "ADD_DAY"
        else: 
            context.bot.send_message(chat_id=update.effective_chat.id, text="У вас нет доступа к этой команде") 
            return ConversationHandler.END

    def handle_add_day_until(update,context): 
        context.user_data['notification_text'] = update.message.text
        update.message.reply_text("Введите сколько дней будет доступно уведомление")
        return "ENTER_NOTIFICATION"

    # Функция обработки ответа с уведомлением для группы
    def handle_notification(update, context): 
        notification_day = update.message.text

        if ((not re.match('^[0-9]*$', notification_day)) or int(notification_day) <= 0): 
            update.message.reply_text("Некоректный ввод, введите корректную информацию")
            return "ENTER_NOTIFICATION"
        elif (int(notification_day) > 60): 
            update.message.reply_text("Наш бот обрабатывает лишь уведомления сроком не более 60 дней, пожалуйста введите коректнуо число")
            return "ENTER_NOTIFICATION"
        
        notification_text = context.user_data['notification_text']
        until_day = (datetime.datetime.today() + datetime.timedelta(days= int(notification_day))).strftime("%y.%m.%d")
        group_name = bot_db.get_group_name(update.effective_user.id)

        bot_db.add_notification(group_name, notification_text, until_day)

        update.message.reply_text("Уведомление успешно добавлено.")
        Sender.push_sender(update=update, context=context, group_name=group_name)
        return ConversationHandler.END

class Statuser: 
    def get_status(update, context): 
        humanize.i18n.activate("ru_RU")
        user_id = update.effective_user.id
        group_name = bot_db.get_group_name(user_id)
        day = str(datetime.datetime.today().strftime('%A').capitalize())
        time_now_min = int(datetime.datetime.today().strftime('%M'))
        time_now_hour = int(datetime.datetime.today().strftime('%H'))
        
        status = bot_db.get_status(group_name, day)

        min_difference = 1000000
        count_min_current_less = 0
        name_less_with_min_dif = ""
        name_current_less = ""
        status_text = ""
        if status: 
            for current in status: 
                times = current[1].split("-")
                count_now_min = (time_now_hour * 60 + time_now_min)
                start_lessons_time_hour = int(times[0].split(":")[0])
                start_lessons_time_min = int(times[0].split(":")[1])
                end_lessons_time_hour = int(times[1].split(":")[0])
                end_lessons_time_min = int(times[1].split(":")[1])
                if (count_now_min >= (start_lessons_time_hour * 60 + start_lessons_time_min) and count_now_min < (end_lessons_time_hour * 60 + end_lessons_time_min)):
                    time_until_end = (end_lessons_time_hour * 60 + end_lessons_time_min) - count_now_min
                    name_current_less = current[0]
                    count_min_current_less = (end_lessons_time_hour * 60 + end_lessons_time_min) - (start_lessons_time_hour * 60 + start_lessons_time_min)
                elif (count_now_min < (start_lessons_time_hour * 60 + start_lessons_time_min)): 
                    difference = (start_lessons_time_hour * 60 + start_lessons_time_min) - count_now_min
                    if min_difference > difference:
                        min_difference = difference
                        name_less_with_min_dif = current[0]
                else: 
                    continue
            if (name_current_less != ""): 
                time_after_start = ((count_min_current_less - time_until_end) / count_min_current_less) * 100
                progress_bar = "|"

                for i in range(10):
                    if (time_after_start > 10): 
                        progress_bar += "⬜"
                        time_after_start -= 10
                    else: 
                        progress_bar += " —"
                progress_bar += "|"
                status_text += f"Сейчас идет: {name_current_less} \n {progress_bar} до конца: {humanize.precisedelta(datetime.timedelta(minutes=time_until_end))}\n"
            if (min_difference != 1000000): 
                status_text += f"Следующее занятие {name_less_with_min_dif} начнется через {humanize.precisedelta(datetime.timedelta(minutes=difference))}"
            if (name_current_less == "" and min_difference == 1000000): 
                status_text += "Сегодня пар больше не будет"
        else: 
            status_text += "Сегодня у вас нет пар"

        context.bot.send_message(chat_id=update.effective_chat.id, text=status_text, reply_markup=Keyboard.owner if bot_db.is_owner(user_id) else Keyboard.user)

class Deleter: 
    def delete_group(update, context):
        user_id = update.effective_user.id
        owner = bot_db.is_owner(user_id) 
        group = bot_db.get_group_name(user_id)

        if owner:
            bot_db.delete_group(group)
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"Группа '{group}' удалена.", reply_markup = Keyboard.new_user)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="У вас нет доступа к этой команде")

    def delete_lesson(update, context): 
        user_id = update.effective_user.id
        owner = bot_db.is_owner(user_id) 
        if owner: 
            context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите день:", reply_markup=Keyboard.week)
            return "DELETE_LESSON_TIME"
        else: 
            context.bot.send_message(chat_id=update.effective_chat.id, text="У вас нет доступа к этой команде")
            return ConversationHandler.END

    def delete_lesson_time(update, context): 
        user_id = update.effective_user.id
        day = update.message.text
        context.user_data['day'] = day
        result = bot_db.give_time_with_lesson(bot_db.get_group_name(user_id), day)

        if result: 
            time_buttons = []
            for i in result: 
                button = []
                button.append(f"|{i[1]}| {i[0]}")
                time_buttons.append(button)
            context.user_data['buttons'] = time_buttons
            context.bot.send_message(chat_id=update.effective_chat.id, text="Выберете занятие которое хотите удалить:", reply_markup = ReplyKeyboardMarkup(keyboard=time_buttons, resize_keyboard=True,one_time_keyboard=True))
            return "HANDLE_DELETE_LESSON"
        else: 
            context.bot.send_message(chat_id=update.effective_chat.id, text="В этот день у вас нет занятий")
            return ConversationHandler.END

    def handle_delete_lesson(update, context): 
        lesson = update.message.text
        buttons = context.user_data['buttons']
        
        if (not Methods.check_lessons(buttons, lesson)): 
            context.bot.send_message(chat_id=update.effective_chat.id, text="В этот день нет такой пары, выберете одну из кнопок")
            return "HANDLE_DELETE_LESSON"
        
        user_id = update.effective_user.id 
        group_name = bot_db.get_group_name(user_id)
        day = context.user_data['day']
        lesson_name = lesson.split()[-1]
        bot_db.delete_lesson(lesson_name, day, group_name)
        context.bot.send_message(chat_id=update.effective_chat.id, text="Занятие успешно удалено", reply_markup= Keyboard.owner)
        return ConversationHandler.END

class Another: 
    def leave_group(update, context): 
        user_id = update.effective_user.id
        group_name = bot_db.get_group_name(user_id)
        if (not bot_db.is_owner(user_id)):
            bot_db.delete_user(update.effective_user.id)
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"Вы успешно покинули группу {group_name}", reply_markup=Keyboard.new_user)
        else: 
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"Вы не можете покинуть группу, так как являетесь её старостой. При желании удалить группу воспользуйтесь командой /delete_group", reply_markup=Keyboard.owner)

    def unknown(update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                text="Извините, я не понимаю эту команду.")
    
    def commands(update, context): 
        context.bot.send_message(chat_id=update.effective_chat.id, 
                                 text="Список команд для старост: \n •/delete_group - удаление группы \n •/delete_lesson - удаление занятия \n\n Список общих команд: \n •/leave - покинуть группу \n •/switch_notification - Включение/отключение ежедневного уведомления \n •/users - Список всех пользователей")
    
    def get_list_users(update, context): 
        user_id = update.effective_user.id
        user_name = update.effective_user.username

        group_name = bot_db.get_group_name(user_id)
        users = bot_db.get_list_users(group_name) 
        owner = bot_db.get_owner(group_name)
        
        text = f'|Староста|\n@{owner[0]}'

        if owner[0] == user_name: text+= ' <- это вы\n'
        else: text += '\n'

        text += '|Юзеры|\n'
        for i in users: 
            text += f'@{i[0]}'
            if i[0] == user_name: text += ' <- это вы\n'
            else: text += '\n'
        context.bot.send_message(chat_id=update.effective_chat.id, text = text)

def main():
    bot = Bot(token=Token.token)
    updater = Updater(bot=bot, use_context=True)
    dispatcher = updater.dispatcher

    # Регистрация обработчиков
    start_handler = CommandHandler('start', Starter.start)

    get_schedule_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(r'Расписание'), Scheduler.get_schedule)],
        states={
            "GET_SCHEDULE": [MessageHandler(Filters.text, Scheduler.handle_get_schedule)]
        },
        fallbacks=[]
    )
    
    unknown_handler = MessageHandler(Filters.command, Another.unknown)

    create_group_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(r'Создать группу'), Starter.create_group)],
        states={
            "CREATE_GROUP": [MessageHandler(Filters.text, Starter.handle_create_group)]
        },
        fallbacks=[]
    )

    join_group_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(r'Присоединиться к группе'), Starter.join_group)],
        states={
            "JOIN_GROUP": [MessageHandler(Filters.text, Starter.handle_join_group)]
        },
        fallbacks=[]
    )

    delete_lesson_handler = ConversationHandler( 
        entry_points=[CommandHandler('delete_lesson', Deleter.delete_lesson)], 
        states={ 
            "DELETE_LESSON_TIME": [MessageHandler(Filters.text, Deleter.delete_lesson_time)], 
            "HANDLE_DELETE_LESSON": [MessageHandler(Filters.text, Deleter.handle_delete_lesson)]
        }, 
        fallbacks=['cancel']
    )

    add_lesson_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(r'Добавить занятие'), Scheduler.add_lesson)],
        states={
            ADD_LESSON_NAME: [MessageHandler(Filters.text, Scheduler.handle_add_lesson_name)],
            ADD_LESSON_TIME: [MessageHandler(Filters.text, Scheduler.handle_add_lesson_time)],
            ADD_LESSON_ROOM: [MessageHandler(Filters.text, Scheduler.handle_add_lesson_room)],
            ADD_LESSON_DAY: [MessageHandler(Filters.text, Scheduler.handle_add_lesson_day)]
        },
        fallbacks=[]
    )

    add_notification_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(r'Добавить уведомление'), Notificator.add_notification)],
        states={
            "ADD_DAY": [MessageHandler(Filters.text, Notificator.handle_add_day_until)],
            "ENTER_NOTIFICATION": [MessageHandler(Filters.text, Notificator.handle_notification)]
        },
        fallbacks=[],
    )

    dispatcher.add_handler(CommandHandler('commands', Another.commands))
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(create_group_handler)
    dispatcher.add_handler(join_group_handler)
    dispatcher.add_handler(add_lesson_handler)
    dispatcher.add_handler(get_schedule_handler)
    dispatcher.add_handler(add_notification_handler)
    dispatcher.add_handler(MessageHandler(Filters.regex(r'Уведомления') | Filters.regex(r'Показать'), Notificator.get_notifications))
    dispatcher.add_handler(CommandHandler('delete_group', Deleter.delete_group))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'Статус'), Statuser.get_status))
    dispatcher.add_handler(delete_lesson_handler)
    dispatcher.add_handler(CommandHandler('leave', Another.leave_group))
    dispatcher.add_handler(CommandHandler('switch_notification', Sender.switch_notification))
    dispatcher.add_handler(CommandHandler('users', Another.get_list_users))
    dispatcher.add_handler(unknown_handler)

    # Запуск бота
    updater.start_polling()

    while True:
        now = datetime.datetime.now()
        if now.hour == 20 and now.minute == 0 and now.second == 0:
            Sender.send_schedule_to_all_users(bot)
        time.sleep(1)

    # Остановка бота при нажатии Ctrl+C
    updater.idle()

    

if __name__ == '__main__':
    main()
    
