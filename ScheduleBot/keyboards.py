from telegram import ReplyKeyboardMarkup, replykeyboardremove

class Keyboard: 
    owner = ReplyKeyboardMarkup([['Расписание', 'Уведомления'], ['Добавить занятие', 'Добавить уведомление'], ['Статус']], resize_keyboard=True)
    
    user = ReplyKeyboardMarkup([['Расписание', 'Уведомления'], ['Статус']], resize_keyboard=True)
    
    new_user = ReplyKeyboardMarkup([['Создать группу', 'Присоединиться к группе']], resize_keyboard=True)
    
    week = ReplyKeyboardMarkup([['Понедельник', 'Вторник'], ['Среда', 'Четверг'], ['Пятница', 'Суббота']],resize_keyboard=True, one_time_keyboard=True)
    
    today_week = ReplyKeyboardMarkup([['Понедельник', 'Вторник'], ['Среда', 'Четверг'], ['Пятница', 'Суббота'], ['Сегодня']], resize_keyboard=True, one_time_keyboard=True, )
    
    time = ReplyKeyboardMarkup([['08:30-10:00', '10:10-11:40'], ['12:10-13:40', '13:50-15:20'], ['15:50-17:20']], resize_keyboard=True, one_time_keyboard=True)

    show = ReplyKeyboardMarkup([['Показать']],resize_keyboard=True, one_time_keyboard=True)