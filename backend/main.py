from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import shutil
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "warehouse.db"
STATIC_DIR = BASE_DIR / "static"
IMG_DIR = STATIC_DIR / "img"

DEFAULT_ITEMS = [
    {"name": "Cort AnusBass Unlimited Deep Collection", "storage_sector": 12, "weight": 10.0, "price": 1488.0, "quantity": 1, "is_dangerous": False, "image": "/static/img/default.jpg"},
    {"name": "Fender Pidoraster", "storage_sector": 13, "weight": 11.0, "price": 666.0, "quantity": 1, "is_dangerous": False, "image": "/static/img/default.jpg"},
    {"name": "Gibson Mrs oldcunt whore slut", "storage_sector": 14, "weight": 9.0, "price": 4000.0, "quantity": 1, "is_dangerous": False, "image": "/static/img/default.jpg"},
    {"name": "Yamaha DX-1488", "storage_sector": 14, "weight": 100.0, "price": 10000.0, "quantity": 1, "is_dangerous": True, "image": "/static/img/default.jpg"},
    {"name": "8", "storage_sector": 15, "weight": 15.0, "price": 1000000.0, "quantity": 1, "is_dangerous": False, "image": "/static/img/default.jpg"},
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    init_database()
    seed_database()
    yield

def init_database():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            storage_sector INTEGER,
            weight REAL,
            price REAL,
            quantity INTEGER,
            is_dangerous INTEGER DEFAULT 0,
            image TEXT
        )
    ''')
    conn.commit()
    conn.close()

def seed_database():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM items")
    count = cursor.fetchone()[0]
    if count == 0:
        for item in DEFAULT_ITEMS:
            cursor.execute('''
                INSERT INTO items (name, storage_sector, weight, price, quantity, is_dangerous, image)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (item["name"], item["storage_sector"], item["weight"], item["price"], item["quantity"], 1 if item["is_dangerous"] else 0, item["image"]))
        conn.commit()
    conn.close()

app = FastAPI(
    title="Склад",
    description="Сервер для учета хранимых предметов на объекте",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статические файлы
IMG_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class Item(BaseModel):
    name: str
    storage_sector: int
    weight: float
    price: float
    quantity: int
    is_dangerous: bool
    image: str  # поле для URL изображения

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    storage_sector: Optional[int] = None
    weight: Optional[float] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    is_dangerous: Optional[bool] = None
    image: Optional[str] = None

def get_db():
    """Получить соединение с БД"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/items", tags=["Просмотр"])
def get_all_items():
    """Получить все предметы"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items ORDER BY id")
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items

@app.post("/items", tags=["Редактирование"], status_code=201)
async def create_item(
    name: str = Form(...),
    storage_sector: int = Form(...),
    quantity: int = Form(...),
    weight: float = Form(0.0),
    price: float = Form(0.0),
    is_dangerous: bool = Form(False),
    image_file: UploadFile = File(...),
):
    # Сохраняем файл
    file_path = IMG_DIR / image_file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image_file.file, buffer)

    image_url = f"/static/img/{image_file.filename}"

    # Сохраняем в БД
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO items (name, storage_sector, weight, price, quantity, is_dangerous, image)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, storage_sector, weight, price, quantity, 1 if is_dangerous else 0, image_url))

    item_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    new_item = dict(cursor.fetchone())
    conn.close()

    return new_item

@app.delete("/items/{item_id}", tags=["Администрирование"])
def delete_item(item_id: int, confirm: bool = False):
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверяем опасность
    cursor.execute("SELECT is_dangerous, name FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Предмет не найден")
    
    if item["is_dangerous"] == 1 and not confirm:
        conn.close()
        raise HTTPException(status_code=403, detail="Опасный товар. Подтвердите удаление")
    
    # Удаляем
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": f"Предмет '{item['name']}' удален"}

@app.get("/items/count", tags=["Аналитика"])
def get_count():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM items")
    result = cursor.fetchone()
    conn.close()
    return {"total": result["total"]}

@app.get("/items/search", tags=["Просмотр"])
def search_items(name: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM items 
        WHERE LOWER(name) LIKE LOWER(?)
    ''', (f"%{name}%",))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

@app.get("/items/{item_id}", tags=["Просмотр"])
def get_one_item(item_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()
    
    if not item:
        raise HTTPException(status_code=404, detail="Предмет с таким Id не найден")
    
    return dict(item)

@app.put("/items/{item_id}", tags=["Администрирование"])
def update_item(item_id: int, updated_item: Item):
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверяем существует ли
    cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Предмет не найден")
    
    # Обновляем
    cursor.execute('''
        UPDATE items
        SET name = ?, storage_sector = ?, weight = ?, price = ?, quantity = ?, is_dangerous = ?, image = ?
        WHERE id = ?
    ''', (
        updated_item.name,
        updated_item.storage_sector,
        updated_item.weight,
        updated_item.price,
        updated_item.quantity,
        1 if updated_item.is_dangerous else 0,
        updated_item.image,
        item_id
    ))
    
    conn.commit()
    
    # Возвращаем обновленный
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    updated = dict(cursor.fetchone())
    conn.close()
    
    return {"message": "Данные обновлены", "item": updated}

# Корзина (храним в словаре в памяти)
user_carts = {}

@app.post("/cart/add/{item_id}", tags=["Корзина"])
def add_to_cart(item_id: int, user_id: str):
    # Проверяем существует ли предмет в БД
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
    exists = cursor.fetchone()
    conn.close()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    
    if user_id not in user_carts:
        user_carts[user_id] = {}
    
    current_cart = user_carts[user_id]
    current_cart[item_id] = current_cart.get(item_id, 0) + 1
    
    return {"status": "success", "cart": current_cart}

@app.get("/cart", tags=["Корзина"])
def get_my_cart(user_id: str):
    return user_carts.get(user_id, {})

@app.delete("/cart/remove/{item_id}", tags=["Корзина"])
def remove_from_cart(item_id: int, user_id: str):
    """Удалить предмет из корзины"""
    if user_id in user_carts and item_id in user_carts[user_id]:
        del user_carts[user_id][item_id]
        return {"status": "success", "cart": user_carts.get(user_id, {})}
    raise HTTPException(status_code=404, detail="Предмет не найден в корзине")

@app.post("/cart/clear", tags=["Корзина"])
def clear_cart(user_id: str):
    """Очистить всю корзину"""
    if user_id in user_carts:
        user_carts[user_id] = {}
    return {"status": "success", "message": "Корзина очищена"}

@app.get("/cart/details", tags=["Корзина"])
def get_cart_details(user_id: str):
    """Получить подробную информацию о корзине с данными из БД"""
    cart = user_carts.get(user_id, {})
    if not cart:
        return {"items": [], "total_items": 0}
    
    # Получаем информацию о товарах из БД
    conn = get_db()
    cursor = conn.cursor()
    
    cart_details = []
    total_price = 0  # если добавите цену
    
    for item_id, quantity in cart.items():
        cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        if item:
            item_dict = dict(item)
            item_dict["cart_quantity"] = quantity
            cart_details.append(item_dict)
    
    conn.close()
    
    return {
        "items": cart_details,
        "total_items": sum(cart.values())
    }

FRONTEND_DIR = BASE_DIR.parent / "frontend"

app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR)), name="css")
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR)), name="js")

@app.get("/", include_in_schema=False)
def serve_index():
    from fastapi.responses import FileResponse
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/add.html", include_in_schema=False)
def serve_add():
    from fastapi.responses import FileResponse
    return FileResponse(str(FRONTEND_DIR / "add.html"))

@app.get("/cart.html", include_in_schema=False)
def serve_cart():
    from fastapi.responses import FileResponse
    return FileResponse(str(FRONTEND_DIR / "cart.html"))

@app.get("/item.html", include_in_schema=False)
def serve_item():
    from fastapi.responses import FileResponse
    return FileResponse(str(FRONTEND_DIR / "item.html"))