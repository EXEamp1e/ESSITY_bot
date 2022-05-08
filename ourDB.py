import sqlite3

class OurDB:

    def __init__(self, database):
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def close(self):
        self.connection.close()

#Таблица с пользователями
    def get_users(self):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `users`").fetchall()

    def get_user_status(self, user_id):
        with self.connection:
            return self.cursor.execute('SELECT `status` FROM `users` WHERE `user_id` = ?', (user_id,)).fetchall()

    def user_exists(self, user_id):
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `users` WHERE `user_id` = ?', (user_id,)).fetchall()
            return bool(len(result))

    def add_user(self, user_id, status, brigade):
        with self.connection:
            return self.cursor.execute("INSERT INTO `users` (`user_id`, `status`, `brigade`) VALUES(?, ?, ?)",
                                       (user_id, status, brigade))

    def update_user_status(self, user_id, status):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `status` = ? WHERE `user_id` = ?", (status, user_id))

    def update_user_brigade(self, user_id, brigade):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `brigade` = ? WHERE `user_id` = ?", (brigade, user_id))

    def delete_user(self, user_id):
        with self.connection:
            return self.cursor.execute("DELETE FROM `users` WHERE `user_id` = ?", user_id)

    def subscribe(self, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `subscription` = True WHERE `user_id` = ?", user_id)

    def unsubscribe(self, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `subscription` = False WHERE `user_id` = ?", user_id)


#Таблица с отчетами
    def get_reports(self):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `reports`").fetchall()

    def get_report(self, shift_code):
        with self.connection:
            return self.cursor.execute('SELECT * FROM `reports` WHERE `shift_code` = ?', shift_code).fetchall()

    def add_comment(self, shift_code, comment):
        with self.connection:
            return self.cursor.execute("INSERT INTO `reports` (`shift_code`, `comment`) VALUES(?, ?)",
                                       (shift_code, comment))

    def add_report(self, shift_code, efficiency, stops, waste):
        with self.connection:
            return self.cursor.execute("INSERT INTO `reports` (`shift_code`, `efficiency`, `stops`, `waste`) "
                                       "VALUES(?, ?, ?, ?)", (shift_code, efficiency, stops, waste))

    def update_comment(self, shift_code, comment):
        with self.connection:
            return self.cursor.execute("UPDATE `reports` SET `comment` = ? WHERE `shift_code` = ?",
                                       (comment, shift_code))

    def update_report(self, shift_code, efficiency, stops, waste):
        with self.connection:
            return self.cursor.execute("UPDATE `reports` SET `efficiency` = ?, `stops` = ?, `waste` = ? "
                                       "WHERE `shift_code` = ?", (efficiency, stops, waste, shift_code))

# Таблица с планами
    def get_plans(self):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `plans`").fetchall()

    def get_current_plan(self):
        with self.connection:
            return self.cursor.execute('SELECT `efficiency`, `stops`, `waste` '
                                       'FROM `plans` ORDER BY id DESC LIMIT 1').fetchall()

    def get_plan_by_date(self, date):
        with self.connection:
            return self.cursor.execute('SELECT `efficiency`, `stops`, `waste` '
                                       'FROM `plans` WHERE `date` = ?', date).fetchall()

    def add_plan(self, efficiency, stops, waste, date):
        with self.connection:
            return self.cursor.execute("INSERT INTO `reports` (`efficiency`, `stops`, `waste`, `date`) "
                                       "VALUES(?, ?, ?, ?)", (efficiency, stops, waste, date))

    def update_current_plan(self, efficiency, stops, waste):
        with self.connection:
            id = self.cursor.execute('SELECT `id` FROM `plans` ORDER BY id DESC LIMIT 1').fetchone()
            return self.cursor.execute("UPDATE `plans` SET `efficiency` = ?, `stops` = ?, `waste` = ? "
                                       "WHERE `id` = ?", (efficiency, stops, waste, id))

    def update_plan_by_date(self, efficiency, stops, waste, date):
        with self.connection:
            return self.cursor.execute("UPDATE `plans` SET `efficiency` = ?, `stops` = ?, `waste` = ? "
                                       "WHERE `date` = ?", (efficiency, stops, waste, date))
