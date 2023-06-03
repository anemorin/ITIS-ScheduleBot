import string 
import random
import re

class Methods: 
    def generate_password():
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(6))

    def check_time(time): 
        if (not re.match('\d\d:\d\d-\d\d:\d\d', time)): 
            return False
        
        times = time.split('-')
        for i in times:
            times = i.split(':')
            if int(times[0]) > 23 or int(times[1]) > 59: 
                return False
        return True

    def check_lessons(buttons, lesson): 
        for i in buttons: 
            if (lesson in i[0]): return True 
        return False

    def check_day(day): 
        if ((re.match('^[0-9]*$', day))): 
            return False
        days = {"Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"}
        if (day in days): 
            return True 
        else: 
            return False

    def print_schedule(lessons, day): 
        schedule_text = f"{day}\n" 
        for lesson in lessons: 
            schedule_text += f"|{lesson[1]}| {lesson[0]}, {lesson[2]} \n"
        return schedule_text