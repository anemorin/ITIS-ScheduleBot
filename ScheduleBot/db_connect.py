import sqlite3

class BotDB:
    def __init__(self, db_file):
        self.conn = sqlite3.connect('schedule.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS groups (group_name TEXT PRIMARY KEY, password TEXT)")
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users(user_id TEXT PRIMARY KEY, group_name TEXT, is_group_owner TEXT, send_schedule TEXT, user_name TEXT)''')
        self.cursor.execute("CREATE TABLE IF NOT EXISTS schedule (lesson_name TEXT, time TEXT, day TEXT, group_name TEXT, room TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS notifications (group_name TEXT, message TEXT, until_day TEXT)")

    def is_owner(self, user_id):
        result = self.cursor.execute("SELECT is_group_owner FROM users WHERE user_id=?", (user_id,)).fetchone()

        if int(result[0]) == 1: return True
        else: return False

    def group_name_exist(self, group_name): 
        result = self.cursor.execute("SELECT * FROM groups WHERE group_name=?", (group_name,)).fetchone()

        if result and result[0]: return True
        else: return False

    def user_exist(self, user_id):
        result = self.cursor.execute("SELECT group_name FROM users WHERE user_id=?", (user_id,)).fetchone()

        if result and result[0]:return True
        else: return False

    def get_group_name(self, user_id):
        result = self.cursor.execute("SELECT group_name FROM users WHERE user_id=?", (user_id,)).fetchone()

        if result:
            return result[0]
        else:
            return None

    def create_group(self, user_id, group_name, password, user_name):
        self.cursor.execute("INSERT INTO groups (group_name, password) VALUES (?, ?)", (group_name, password))
        self.cursor.execute("INSERT INTO users (user_id, group_name, is_group_owner, send_schedule, user_name) VALUES (?, ?, 1, 1, ?)",
                   (user_id, group_name, user_name))
        self.conn.commit()

    def password_exist(self, password):
        return self.cursor.execute("SELECT group_name FROM groups WHERE password=?", (password,)).fetchone()

    def join_group(self, user_id, group_name, user_name):
        self.cursor.execute("INSERT INTO users (user_id, group_name, is_group_owner, send_schedule, user_name) VALUES (?, ?, 0, 1, ?)",
                   (user_id, group_name, user_name))
        self.conn.commit()

    def add_lesson(self, group_name, lesson_time, lesson_day, lesson_room, lesson_name):
        if self.cursor.execute(
            "SELECT * FROM schedule WHERE group_name=? AND time=? AND day=?",
            (group_name, lesson_time, lesson_day)).fetchall():
            self.cursor.execute("UPDATE schedule SET lesson_name=?, room=? WHERE group_name=? AND time=? AND day=?",
                   (lesson_name, lesson_room, group_name, lesson_time, lesson_day))
        else:
            self.cursor.execute("INSERT INTO schedule (lesson_name, time, day, group_name, room) VALUES (?, ?, ?, ?, ?)",
                    (lesson_name, lesson_time, lesson_day, group_name, lesson_room))

        self.conn.commit()

    def get_schedule(self, group_name, day):
        return self.cursor.execute("SELECT lesson_name, time, room FROM schedule WHERE group_name=? AND day=? ORDER BY time ASC",
                                   (group_name, day,)).fetchall()

    def get_all_users(self):
        return self.cursor.execute("SELECT user_id, group_name, send_schedule FROM users").fetchall()

    def check_notification_status(self, user_id):
        result = self.cursor.execute("SELECT send_schedule FROM users WHERE user_id=?", (user_id,)).fetchone()
        if int(result[0]) == 1: return True
        else: return False

    def give_time_with_lesson(self, group_name, day):
        return self.cursor.execute("SELECT lesson_name, time FROM schedule WHERE group_name=? AND day=? ORDER BY time ASC", (group_name, day,)).fetchall()

    def switch_notification(self, user_id, value):
        self.cursor.execute("UPDATE users SET send_schedule=? WHERE user_id=?", (value, user_id))
        self.conn.commit()

    def get_notifications(self, now_date, group_name):
        self.cursor.execute("DELETE FROM notifications WHERE until_day<?", (now_date,))
        self.conn.commit()

        return self.cursor.execute("SELECT message, until_day FROM notifications WHERE group_name=? ORDER BY until_day ASC",
                                   (group_name,)).fetchall()

    def get_user_id_from_group(self, group_name):
        return self.cursor.execute("SELECT user_id, is_group_owner FROM users WHERE group_name=?", (group_name,)).fetchall()

    def add_notification(self, group_name, notification_text, until_day):
        self.cursor.execute("INSERT INTO notifications (group_name, message, until_day) VALUES (?, ?, ?)",
                   (group_name, notification_text, until_day))
        self.conn.commit()

    def get_status(self, group_name, day):
        return self.cursor.execute("SELECT lesson_name, time FROM schedule WHERE group_name=? AND day=?", (group_name, day,)).fetchall()

    def delete_group(self, group):
        self.cursor.execute("DELETE FROM users WHERE group_name=?", (group,))
        self.cursor.execute("DELETE FROM groups WHERE group_name=?", (group,))
        self.cursor.execute("DELETE FROM notifications WHERE group_name=?", (group,))
        self.cursor.execute("DELETE FROM schedule WHERE group_name=?", (group,))
        self.conn.commit()

    def delete_lesson(self, lesson_name, day, group_name):
        self.cursor.execute("DELETE FROM schedule WHERE lesson_name=? AND day=? AND group_name=?", (lesson_name, day, group_name,))
        self.conn.commit()

    def delete_user(self, user_id):
        self.cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        self.conn.commit()

    def get_list_users(self, group_name):
        return self.cursor.execute("SELECT user_name, user_id FROM users WHERE group_name=? AND is_group_owner=?", (group_name, 0)).fetchall()

    def get_owner(self, group_name):
        return self.cursor.execute("SELECT user_name, user_id FROM users WHERE group_name=? AND is_group_owner=?", (group_name, 1)).fetchone()

    def close(self):
        self.conn.close()
