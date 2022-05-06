import sqlite3


class ReportsDB:

    def __init__(self, database):
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def get_reports(self):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `reports`").fetchall()

    def get_report(self):
        with self.connection:
            return self.cursor.execute('SELECT `plan` FROM `reports` ORDER BY id DESC LIMIT 1').fetchall()

    def add_report(self, shift_code, comment):
        with self.connection:
            return self.cursor.execute("INSERT INTO `reports` (`shift_code`, `comment`) VALUES(?, ?)",
                                       (shift_code, comment))

    def add_report(self, shift_code, efficiency, stops, waste):
        with self.connection:
            return self.cursor.execute("INSERT INTO `reports` (`shift_code`, `efficiency`, `stops`, `waste`) "
                                       "VALUES(?, ?, ?, ?)", (shift_code, efficiency, stops, waste))

    def update_report(self, shift_code, comment):
        with self.connection:
            return self.cursor.execute("UPDATE `reports` SET `comment` = ? WHERE `shift_code` = ?",
                                       (comment, shift_code))

    def update_report(self, shift_code, efficiency, stops, waste):
        with self.connection:
            return self.cursor.execute("UPDATE `reports` SET `efficiency` = ?, `stops` = ?, `waste` = ? "
                                       "WHERE `shift_code` = ?", (efficiency, stops, waste, shift_code))

    def close(self):
        self.connection.close()
