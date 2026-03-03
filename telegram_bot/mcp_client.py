# mcp_client.py — вызов MCP-инструментов по HTTP

import json
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

from config import get_mcp_base_url


def call_mcp_tool(tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
    """
    Вызывает инструмент MCP-сервера по HTTP.
    POST {MCP_SERVER_URL}/call с телом {"tool": "<name>", "arguments": {...}}
    """
    base = get_mcp_base_url()
    url = f"{base}/call"
    payload = {"tool": tool_name, "arguments": arguments or {}}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            out = json.loads(body)
            if out.get("error"):
                return {"error": out["error"]}
            return out.get("result")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
            detail = json.loads(body).get("detail", body)
        except Exception:
            detail = str(e)
        return {"error": f"HTTP {e.code}: {detail}"}
    except urllib.error.URLError as e:
        return {"error": f"Не удалось подключиться к MCP-серверу: {e.reason}. Убедитесь, что сервер запущен (python server.py в mcp_server)."}
    except json.JSONDecodeError as e:
        return {"error": f"Некорректный ответ сервера: {e}"}
