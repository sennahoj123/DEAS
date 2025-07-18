# create_database.py
import sqlite3

def create_database():
    """Maakt een nieuwe SQLite database aan en vult deze met voorbeeldplanten."""
    try:
        conn = sqlite3.connect('planten.db')
        cursor = conn.cursor()
        print("Database 'planten.db' succesvol aangemaakt/geopend.")

        cursor.execute("DROP TABLE IF EXISTS plants")

        cursor.execute("""
        CREATE TABLE plants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            quality TEXT,
            price_per_unit REAL,
            plants_per_m2 INTEGER,
            flower_start_month INTEGER,
            flower_end_month INTEGER,
            structure_start_month INTEGER,
            structure_end_month INTEGER,
            image_path TEXT
        )
        """)
        print("Tabel 'plants' succesvol aangemaakt.")

        sample_plants = [
            ('Aster "Little Carlow"', 'P9', 3.50, 7, 8, 10, 1, 12, None),
            ('Calamintha nepeta ssp. nepeta', 'P9', 3.00, 9, 6, 9, 2, 11, None),
            ('Echinops bannaticus "Taplow Blue"', 'P9', 3.25, 7, 7, 8, 0, 0, None),
            ('Geranium x oxonianum "Rose Clair"', 'P9', 3.50, 8, 6, 9, 0, 0, None),
            ('Salvia nemerosa "Schneehugel"', 'P9', 3.75, 7, 6, 8, 0, 0, None)
        ]

        cursor.executemany("""
        INSERT INTO plants (name, quality, price_per_unit, plants_per_m2, flower_start_month, flower_end_month, structure_start_month, structure_end_month, image_path) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_plants)
        
        print(f"{len(sample_plants)} voorbeeldplanten succesvol toegevoegd.")
        
        conn.commit()
        conn.close()
        print("Wijzigingen opgeslagen en verbinding gesloten.")

    except sqlite3.Error as e:
        print(f"Een databasefout is opgetreden: {e}")

if __name__ == "__main__":
    create_database()