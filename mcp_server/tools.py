# tools.py — MCP-инструменты и безопасный калькулятор (без eval)

import ast
import operator
from typing import Any

import db

# Безопасные бинарные операторы для калькулятора
BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
UNARY_OPS = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval(expression: str) -> float:
    """
    Безопасное вычисление математического выражения без eval.
    Разрешены только числа и операторы +, -, *, /, //, %, **.
    """
    if not expression or not isinstance(expression, str):
        raise ValueError("Пустое выражение")
    expr = expression.strip()
    if not expr:
        raise ValueError("Пустое выражение")

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Некорректное выражение: {e}")

    def visit(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Разрешены только числа")
        if isinstance(node, ast.BinOp):
            left = visit(node.left)
            right = visit(node.right)
            op = BIN_OPS.get(type(node.op))
            if op is None:
                raise ValueError("Недопустимая операция")
            if type(node.op) == ast.Div and right == 0:
                raise ValueError("Деление на ноль")
            return op(left, right)
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, (ast.USub, ast.UAdd)):
                return UNARY_OPS[type(node.op)](visit(node.operand))
            raise ValueError("Недопустимая унарная операция")
        raise ValueError("Разрешены только числа и арифметические операции")

    result = visit(tree.body)
    if isinstance(result, float) and result == int(result):
        result = int(result)
    return result


def list_mochi() -> list:
    """Возвращает список всех десертов моти."""
    return db.get_all_mochi()


def find_mochi_by_name(name: str) -> list:
    """Находит десерты по частичному совпадению имени."""
    return db.find_mochi_by_name(name)


def find_mochi_by_ingredient(ingredient: str) -> list:
    """Находит десерты по вхождению слова в описании."""
    return db.find_mochi_by_ingredient(ingredient)


def add_mochi(name: str, description: str, category: str, price: float) -> dict:
    """Добавляет новый десерт в базу."""
    return db.add_mochi(name, description, category, price)


def calculate(expression: str) -> dict:
    """Безопасно вычисляет математическое выражение."""
    result = safe_eval(expression)
    return {"expression": expression, "result": result}


# MCP JSON Schema для инструментов (для экспорта по HTTP)
MCP_TOOLS = [
    {
        "name": "list_mochi",
        "description": "Показать список всех десертов моти из меню.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "find_mochi_by_name",
        "description": "Найти десерты моти по частичному совпадению названия (например: клубника, манго).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Часть названия десерта для поиска.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "find_mochi_by_ingredient",
        "description": "Найти десерты моти по ингредиенту (слово в описании: кокос, шоколад, малина и т.д.).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ingredient": {
                    "type": "string",
                    "description": "Ингредиент для поиска в описании.",
                },
            },
            "required": ["ingredient"],
        },
    },
    {
        "name": "add_mochi",
        "description": "Добавить новый десерт моти в меню.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Название десерта."},
                "description": {"type": "string", "description": "Описание десерта."},
                "category": {"type": "string", "description": "Категория (например: фруктовый, шоколадный)."},
                "price": {"type": "number", "description": "Цена (руб)."},
            },
            "required": ["name", "description", "category", "price"],
        },
    },
    {
        "name": "calculate",
        "description": "Безопасно вычислить математическое выражение (например: 3*150, 100+50).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Математическое выражение: числа, +, -, *, /, **.",
                },
            },
            "required": ["expression"],
        },
    },
]

# Маппинг имён инструментов на функции
TOOL_HANDLERS = {
    "list_mochi": lambda **kw: list_mochi(),
    "find_mochi_by_name": lambda **kw: find_mochi_by_name(kw.get("name", "")),
    "find_mochi_by_ingredient": lambda **kw: find_mochi_by_ingredient(kw.get("ingredient", "")),
    "add_mochi": lambda **kw: add_mochi(
        kw.get("name", ""),
        kw.get("description", ""),
        kw.get("category", ""),
        kw.get("price", 0),
    ),
    "calculate": lambda **kw: calculate(kw.get("expression", "")),
}


def call_tool(name: str, arguments: dict) -> Any:
    """Вызывает MCP-инструмент по имени с переданными аргументами."""
    if name not in TOOL_HANDLERS:
        return {"error": f"Неизвестный инструмент: {name}"}
    try:
        return TOOL_HANDLERS[name](**arguments)
    except Exception as e:
        return {"error": str(e)}
