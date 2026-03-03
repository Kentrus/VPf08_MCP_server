# server.py — MCP-совместимый HTTP-сервер (mochi-mcp)
# Запуск: python server.py
# Порт берётся из .env (MCP_PORT) или переменной окружения; по умолчанию 8765.
# Файл mochi.json ищется в: mcp_server/mochi.json, затем корень проекта (mochi.json, assortment_mochi.json)

import os
from pathlib import Path

# Загружаем .env из mcp_server или из корня проекта (чтобы MCP_PORT подхватывался)
try:
    from dotenv import load_dotenv
    _dir = Path(__file__).resolve().parent
    load_dotenv(_dir / ".env")
    load_dotenv(_dir.parent / ".env")
except ImportError:
    pass

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Optional

import db
from tools import MCP_TOOLS, call_tool


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(
    title="mochi-mcp",
    description="MCP-сервер «Моти-ассистент» для интернет-меню десертов моти",
    version="1.0.0",
    lifespan=lifespan,
)


class ToolCallRequest(BaseModel):
    tool: str
    arguments: dict = {}


class ToolCallResponse(BaseModel):
    result: Any = None
    error: Optional[str] = None


@app.get("/")
def root():
    return {
        "server": "mochi-mcp",
        "docs": "/docs",
        "tools": "/tools",
        "call": "POST /call",
    }


@app.get("/tools", response_model=list)
def list_tools():
    """Возвращает список MCP-инструментов в формате JSON Schema."""
    return MCP_TOOLS


@app.post("/call", response_model=ToolCallResponse)
def invoke_tool(req: ToolCallRequest):
    """Вызывает указанный MCP-инструмент с аргументами."""
    name = (req.tool or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Параметр 'tool' обязателен")
    arguments = req.arguments or {}
    out = call_tool(name, arguments)
    if isinstance(out, dict) and out.get("error"):
        return ToolCallResponse(error=out["error"])
    return ToolCallResponse(result=out)


def _get_port() -> int:
    """Порт из MCP_PORT или из MCP_SERVER_URL (например http://127.0.0.1:8766 -> 8766)."""
    port_str = os.environ.get("MCP_PORT", "").strip()
    if not port_str and os.environ.get("MCP_SERVER_URL"):
        from urllib.parse import urlparse
        u = urlparse(os.environ["MCP_SERVER_URL"])
        if u.port is not None:
            return u.port
    return int(port_str or "8765")


if __name__ == "__main__":
    port = _get_port()
    try:
        uvicorn.run(app, host="0.0.0.0", port=port)
    except OSError as e:
        if e.winerror == 10048 or "Address already in use" in str(e):
            print(f"Порт {port} занят. Остановите другой процесс на этом порту или задайте другой: MCP_PORT=8766 python server.py")
        raise
