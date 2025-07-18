# database/manager.py
import sqlite3

class DatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            print(f"Database succesvol verbonden: {self.db_file}")
        except sqlite3.Error as e:
            print(f"Fout bij verbinden met database: {e}")

    def close(self):
        if self.conn:
            self.conn.close()
            print("Databaseverbinding gesloten.")

    def get_all_plant_names(self):
        if not self.conn: return []
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM plants ORDER BY name ASC")
        return [row['name'] for row in cursor.fetchall()]

    def get_plant_details(self, name):
        if not self.conn: return None
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM plants WHERE LOWER(name)=?", (name.lower(),))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Fout bij ophalen details voor {name}: {e}")
            return None