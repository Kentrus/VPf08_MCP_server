# bot.py — Telegram-бот, подключается к MCP-серверу и использует OpenAI для выбора инструментов

import json
import re
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

from config import get_telegram_token, get_openai_key
from mcp_client import call_mcp_tool

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Ты — умный помощник по выбору десертов моти.
Ты можешь использовать следующие инструменты:
list_mochi - показать все десерты
find_mochi_by_name - найти десерты по названию (требует параметр "name")
find_mochi_by_ingredient - найти десерты по ингредиенту (требует параметр "ingredient")
add_mochi - добавить новый десерт (требует параметры "name", "description", "category", "price")
calculate - вычислить математическое выражение (требует параметр "expression")

Когда пользователь просит что-то сделать, определи, какой инструмент нужен, и верни JSON в формате:
{
  "tool": "название_инструмента",
  "arguments": {"параметр": "значение"}
}
Если инструмент не нужен, просто ответь пользователю обычным текстом.
Примеры:
"покажи все моти" → {"tool": "list_mochi", "arguments": {}}
"найди моти клубника" → {"tool": "find_mochi_by_name", "arguments": {"name": "клубника"}}
"что есть с кокосом" → {"tool": "find_mochi_by_ingredient", "arguments": {"ingredient": "кокос"}}
"добавь десерт моти Нутелла описание шоколадный крем и орехи 190 фруктовый" → {"tool": "add_mochi", "arguments": {"name": "Моти Нутелла", "description": "шоколадный крем и орехи", "category": "шоколадный", "price": 190}}
"посчитай 3*150" → {"tool": "calculate", "arguments": {"expression": "3*150"}}

Отвечай на русском языке, будь дружелюбным и полезным, описывай десерты вкусно и понятно.
Важно: если нужен вызов инструмента — ответь ТОЛЬКО одним JSON-объектом без markdown и без лишнего текста. Если инструмент не нужен — ответь обычным текстом.
"""


def _extract_json(text: str) -> dict | None:
    """Пытается извлечь JSON из ответа модели (иногда обёрнут в ```json ... ```)."""
    text = (text or "").strip()
    # Убираем markdown-блок кода
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _escape_md(s: str) -> str:
    """Экранирует символы для Telegram Markdown (legacy)."""
    if not s:
        return s
    return str(s).replace("\\", "\\\\").replace("*", "\\*").replace("_", "\\_").replace("`", "\\`").replace("[", "\\[")


def _format_mochi_list(items: list) -> str:
    """Форматирует список десертов для красивого ответа пользователю."""
    if not items:
        return "По вашему запросу ничего не найдено."
    lines = []
    for m in items:
        name = _escape_md(m.get("name", "—"))
        desc = _escape_md(m.get("description", ""))
        cat = _escape_md(m.get("category", ""))
        price = m.get("price")
        price_str = f"{price:.0f} ₽" if isinstance(price, (int, float)) else str(price)
        lines.append(f"🍡 *{name}* — {price_str}\n{desc}")
        if cat:
            lines.append(f"   _Категория: {cat}_")
        lines.append("")
    return "\n".join(lines).strip()


def _format_tool_result(tool_name: str, result) -> str:
    """Преобразует результат вызова инструмента в читаемый текст."""
    if isinstance(result, dict) and result.get("error"):
        return f"Ошибка: {result['error']}"
    if tool_name == "list_mochi" or tool_name == "find_mochi_by_name" or tool_name == "find_mochi_by_ingredient":
        if isinstance(result, list):
            return _format_mochi_list(result)
        return str(result)
    if tool_name == "add_mochi" and isinstance(result, dict):
        return f"✅ Добавлен десерт: *{_escape_md(str(result.get('name', '')))}* — {result.get('price')} ₽"
    if tool_name == "calculate" and isinstance(result, dict):
        return f"🧮 {result.get('expression', '')} = *{result.get('result', '')}*"
    return str(result)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = (update.message and update.message.text or "").strip()
    if not user_text:
        await update.message.reply_text("Напишите, что вас интересует: например, «покажи все моти» или «найди моти с клубникой».")
        return

    client = OpenAI(api_key=get_openai_key())
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
        )
        reply = (response.choices[0].message.content or "").strip()
    except Exception as e:
        logger.exception("OpenAI request failed")
        await update.message.reply_text(f"Не удалось получить ответ: {e}. Проверьте OPENAI_API_KEY и доступ к API.")
        return

    # Пробуем распарсить как вызов инструмента
    parsed = _extract_json(reply)
    if isinstance(parsed, dict) and parsed.get("tool"):
        tool_name = parsed.get("tool", "").strip()
        arguments = parsed.get("arguments") or {}
        result = call_mcp_tool(tool_name, arguments)
        formatted = _format_tool_result(tool_name, result)
        # Короткое пояснение от LLM не запрашиваем — сразу отвечаем результатом
        await update.message.reply_text(formatted, parse_mode="Markdown")
        return

    # Обычный текстовый ответ модели
    await update.message.reply_text(reply or "Не удалось сформировать ответ. Попробуйте переформулировать запрос.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я помощник по десертам моти 🍡\n\n"
        "Можете написать, например:\n"
        "• «Покажи все моти»\n"
        "• «Найди моти клубника»\n"
        "• «Что есть с кокосом?»\n"
        "• «Добавь десерт моти Нутелла, описание: шоколад и орехи, 190 руб, категория шоколадный»\n"
        "• «Посчитай 3*150»"
    )


def main() -> None:
    token = get_telegram_token()
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
