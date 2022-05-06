import sqlite3

class UsersDB:

    def __init__(self, database):
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

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

    def add_user(self, user_id, status):
        with self.connection:
            return self.cursor.execute("INSERT INTO `users` (`user_id`, `status`) VALUES(?,?)", (user_id,status))

    def update_user(self, user_id, status):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `status` = ? WHERE `user_id` = ?", (status, user_id))

    def delete_user(self, user_id):
        with self.connection:
            return self.cursor.execute("DELETE FROM `users` WHERE 'user_id' = ?", user_id)

    def subscribe(self, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `subscription` = True WHERE `user_id` = ?", user_id)

    def unsubscribe(self, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `subscription` = False WHERE `user_id` = ?", user_id)

    def close(self):
        self.connection.close()