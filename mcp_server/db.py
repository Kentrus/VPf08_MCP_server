# db.py — работа с SQLite и инициализация данных из mochi.json
# Путь к mochi.json: сначала mcp_server/mochi.json, затем корень проекта

import sqlite3
import json
import os
import re

# Путь к БД и JSON (относительно корня проекта)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DB_PATH = os.path.join(BASE_DIR, "mochi.db")

# Возможные пути к mochi.json: папка mcp_server, затем корень проекта
MOCHI_JSON_PATHS = [
    os.path.join(BASE_DIR, "mochi.json"),
    os.path.join(PROJECT_ROOT, "mochi.json"),
    os.path.join(PROJECT_ROOT, "assortment_mochi.json"),
]


def _infer_category(description: str) -> str:
    """Определяет категорию по ключевым словам в описании."""
    d = (description or "").lower()
    if any(w in d for w in ["клубник", "манго", "малин", "банан", "ананас", "черник", "личи", "фисташк"]):
        return "фруктовый"
    if any(w in d for w in ["шоколад", "орех", "арахис", "сникерс", "нутелл"]):
        return "шоколадный"
    if any(w in d for w in ["кокос", "пина колада"]):
        return "тропический"
    if any(w in d for w in ["лимон", "лайм", "маракуй"]):
        return "цитрусовый"
    if any(w in d for w in ["кофе", "тирамису", "маскарпоне"]):
        return "кофейный"
    if any(w in d for w in ["мята", "мохито"]):
        return "освежающий"
    if any(w in d for w in ["печенье", "орео", "opeo"]):
        return "десертный"
    return "десерт"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Создаёт таблицу mochi, если её нет, и при необходимости заполняет из mochi.json."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mochi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                price REAL
            )
        """)
        conn.commit()

        cur = conn.execute("SELECT COUNT(*) FROM mochi")
        if cur.fetchone()[0] > 0:
            return

        # Таблица пуста — загружаем из JSON
        data = None
        for path in MOCHI_JSON_PATHS:
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                break

        if not data or not isinstance(data, list):
            return

        import random
        for item in data:
            name = item.get("Десерт") or item.get("name") or ""
            desc = item.get("Описание") or item.get("description") or ""
            category = item.get("category") or _infer_category(desc)
            price = item.get("price")
            if price is None:
                price = round(random.uniform(100, 250), 2)
            conn.execute(
                "INSERT INTO mochi (name, description, category, price) VALUES (?, ?, ?, ?)",
                (name, desc, category, price),
            )
        conn.commit()
    finally:
        conn.close()


def get_all_mochi():
    """Возвращает список всех десертов моти."""
    init_db()
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT id, name, description, category, price FROM mochi ORDER BY name"
        )
        rows = cur.fetchall()
        return [
            {"id": r[0], "name": r[1], "description": r[2], "category": r[3], "price": r[4]}
            for r in rows
        ]
    finally:
        conn.close()


def find_mochi_by_name(name: str):
    """Находит десерты по частичному совпадению имени (без учёта регистра)."""
    if not name or not name.strip():
        return get_all_mochi()
    init_db()
    conn = get_connection()
    try:
        pattern = f"%{name.strip()}%"
        cur = conn.execute(
            "SELECT id, name, description, category, price FROM mochi WHERE LOWER(name) LIKE LOWER(?) ORDER BY name",
            (pattern,),
        )
        rows = cur.fetchall()
        return [
            {"id": r[0], "name": r[1], "description": r[2], "category": r[3], "price": r[4]}
            for r in rows
        ]
    finally:
        conn.close()


def find_mochi_by_ingredient(ingredient: str):
    """Находит десерты по вхождению слова в описании."""
    if not ingredient or not ingredient.strip():
        return []
    init_db()
    conn = get_connection()
    try:
        pattern = f"%{ingredient.strip()}%"
        cur = conn.execute(
            "SELECT id, name, description, category, price FROM mochi WHERE LOWER(description) LIKE LOWER(?) ORDER BY name",
            (pattern,),
        )
        rows = cur.fetchall()
        return [
            {"id": r[0], "name": r[1], "description": r[2], "category": r[3], "price": r[4]}
            for r in rows
        ]
    finally:
        conn.close()


def add_mochi(name: str, description: str, category: str, price: float):
    """Добавляет новый десерт в базу."""
    init_db()
    conn = get_connection()
    try:
        category = category or _infer_category(description or "")
        conn.execute(
            "INSERT INTO mochi (name, description, category, price) VALUES (?, ?, ?, ?)",
            (str(name).strip(), str(description).strip(), str(category).strip(), float(price)),
        )
        conn.commit()
        cur = conn.execute("SELECT last_insert_rowid()")
        row_id = cur.fetchone()[0]
        return {"id": row_id, "name": name, "description": description, "category": category, "price": float(price)}
    finally:
        conn.close()
