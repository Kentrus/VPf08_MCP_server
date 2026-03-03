# server.py — MCP-совместимый HTTP-сервер (mochi-mcp)
# Запуск: python server.py
# Файл mochi.json ищется в: mcp_server/mochi.json, затем корень проекта (mochi.json, assortment_mochi.json)

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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765)
