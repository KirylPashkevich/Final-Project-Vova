import sqlite3
from pathlib import Path
from database import items

DB_PATH = Path(__file__).parent / "warehouse.db"

def migrate():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    for item in items:
        query = '''
                INSERT OR IGNORE INTO items (id, name, storage_sector, weight, price, quantity, is_dangerous, image)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                '''
        # Добавляем путь к изображению по умолчанию, если его нет
        image_path = item.get('image', item.get('image_url', '/static/img/default.jpg'))
        if not image_path.startswith('/'):
            image_path = '/' + image_path

        values = (
            item['id'],
            item['name'],
            item['storage_sector'],
            item.get('weight', 0.0),
            item.get('price', 0.0),
            item['quantity'],
            1 if item.get('is_dangerous', False) else 0,
            image_path
        )
        try:
            cursor.execute(query, values)
            print(f"Товар с id {item['id']} успешно добавлен")
        except sqlite3.IntegrityError:
            print(f"Товар с id {item['id']} уже есть в БД")

    conn.commit()
    conn.close()
    print("Миграция завершена")

if __name__ == "__main__":
    migrate()