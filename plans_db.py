import sqlite3


class PlansDB:
    def __init__(self, database):
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def get_plans(self):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `plans`").fetchall()

    def get_current_plan(self):
        with self.connection:
            return self.cursor.execute('SELECT `plan` FROM `plans` ORDER BY id DESC LIMIT 1').fetchall()

    def add_plan(self, efficiency, stops, waste):
        with self.connection:
            return self.cursor.execute("INSERT INTO `reports` (`efficiency`, `stops`, `waste`) "
                                       "VALUES(?, ?, ?)", (efficiency, stops, waste))

    def update_plan(self, efficiency, stops, waste):
        with self.connection:
            id = self.cursor.execute('SELECT `id` FROM `plans` ORDER BY id DESC LIMIT 1').fetchone()
            return self.cursor.execute("UPDATE `plans` SET `efficiency` = ?, `stops` = ?, `waste` = ? "
                                       "WHERE `id` = ?", (efficiency, stops, waste, id))

    def close(self):
        self.connection.close()
