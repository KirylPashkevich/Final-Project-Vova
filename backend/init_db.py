import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "warehouse.db"
connection = sqlite3.connect(str(DB_PATH))
cursor = connection.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        storage_sector INTEGER,
        weight REAL,
        price REAL,
        quantity INTEGER,
        is_dangerous INTEGER DEFAULT 0,
        image TEXT      )
''')
connection.commit()
connection.close()
print("База данных успешно было создана чеек расширение")