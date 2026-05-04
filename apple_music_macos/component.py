from __future__ import annotations

import json
import os
import platform
import subprocess
import threading
from pathlib import Path
from typing import Any


def _is_truthy(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "on"}


def _run(command: list[str], purpose: str) -> None:
    proc = subprocess.run(command, capture_output=True, text=True)
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        detail = stderr or stdout or f"exit={proc.returncode}"
        raise RuntimeError(f"{purpose} failed: {detail}")


def _prepare_apple_music(full_config: dict[str, Any]) -> dict[str, Any] | None:
    if platform.system().lower() != "darwin":
        return None

    section = full_config.get("apple_music") if isinstance(full_config.get("apple_music"), dict) else {}
    if not _is_truthy(section.get("enabled"), default=True):
        return None

    repo_url = str(section.get("repo_url") or "https://github.com/epheterson/mcp-applemusic.git").strip()
    branch = str(section.get("branch") or "main").strip() or "main"
    install_dir = Path(str(section.get("install_dir") or "~/.xiaozhi/applemusic-mcp")).expanduser().resolve()
    venv_dir = install_dir / "venv"
    venv_python = venv_dir / "bin" / "python"

    install_dir.parent.mkdir(parents=True, exist_ok=True)

    if not (install_dir / ".git").exists():
        _run(["git", "clone", "--branch", branch, repo_url, str(install_dir)], "clone applemusic repo")
    elif _is_truthy(section.get("update_on_startup"), default=True):
        _run(["git", "-C", str(install_dir), "fetch", "origin", branch], "fetch applemusic updates")
        _run(["git", "-C", str(install_dir), "pull", "--ff-only", "origin", branch], "pull applemusic updates")

    if not venv_python.exists():
        _run(["python3", "-m", "venv", str(venv_dir)], "create applemusic venv")

    _run([str(venv_python), "-m", "pip", "install", "-e", str(install_dir)], "install applemusic package")

    return {
        "command": str(venv_python),
        "args": ["-m", "applemusic_mcp"],
        "tool_prefix": str(section.get("tool_prefix") or "apple_music_").strip() or "apple_music_",
        "env": {},
    }


class _StdioMCPClient:
    def __init__(self, command: list[str], env: dict[str, str] | None = None) -> None:
        self._command = command
        self._env = env or {}
        self._proc: subprocess.Popen[bytes] | None = None
        self._id = 1
        self._lock = threading.Lock()

    def _ensure_started(self) -> None:
        if self._proc and self._proc.poll() is None:
            return

        merged_env = os.environ.copy()
        merged_env.update(self._env)
        self._proc = subprocess.Popen(
            self._command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=merged_env,
        )
        self._request(
            "initialize",
            {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "xiaozhi-apple-music-bridge", "version": "0.1.0"}},
        )
        self._notify("notifications/initialized", {})

    def _notify(self, method: str, params: dict[str, Any]) -> None:
        self._write_message({"jsonrpc": "2.0", "method": method, "params": params})

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        req_id = self._id
        self._id += 1
        self._write_message({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
        while True:
            msg = self._read_message()
            if msg.get("id") != req_id:
                continue
            if "error" in msg:
                err = msg.get("error") or {}
                raise RuntimeError(str(err.get("message", "unknown mcp error")))
            return msg

    def _write_message(self, payload: dict[str, Any]) -> None:
        if not self._proc or not self._proc.stdin:
            raise RuntimeError("mcp process not started")
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        header = f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii")
        self._proc.stdin.write(header + raw)
        self._proc.stdin.flush()

    def _read_message(self) -> dict[str, Any]:
        if not self._proc or not self._proc.stdout:
            raise RuntimeError("mcp process not started")

        headers = b""
        while b"\r\n\r\n" not in headers:
            b = self._proc.stdout.read(1)
            if not b:
                raise RuntimeError("mcp process stdout closed while reading headers")
            headers += b

        content_length = 0
        for line in headers.decode("ascii", errors="replace").split("\r\n"):
            if line.lower().startswith("content-length:"):
                content_length = int(line.split(":", 1)[1].strip())
                break

        if content_length <= 0:
            raise RuntimeError("invalid mcp content length")

        body = b""
        while len(body) < content_length:
            chunk = self._proc.stdout.read(content_length - len(body))
            if not chunk:
                raise RuntimeError("unexpected eof while reading mcp response")
            body += chunk
        return json.loads(body.decode("utf-8"))

    def list_tools(self) -> list[dict[str, Any]]:
        with self._lock:
            self._ensure_started()
            msg = self._request("tools/list", {})
            tools = (msg.get("result") or {}).get("tools") or []
            return [t for t in tools if isinstance(t, dict)]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._ensure_started()
            msg = self._request("tools/call", {"name": name, "arguments": arguments})
            return {"success": True, "result": msg.get("result")}


class Component:
    def __init__(self, _config: dict[str, Any] | None = None, full_config: dict[str, Any] | None = None) -> None:
        self.full_config = full_config or {}
        self._bridge_cfg: dict[str, Any] | None = None
        self._bridge: _StdioMCPClient | None = None
        self._tools: list[dict[str, Any]] | None = None
        self._error: str | None = None

    def supports_role(self, role: str) -> bool:
        return role == "client" and platform.system().lower() == "darwin"

    def _ensure_bridge(self) -> _StdioMCPClient | None:
        if self._bridge is not None:
            return self._bridge
        if self._error is not None:
            return None
        try:
            self._bridge_cfg = _prepare_apple_music(self.full_config)
            if self._bridge_cfg is None:
                self._error = "apple_music disabled or non-macos"
                return None
            cmd = [str(self._bridge_cfg.get("command", ""))]
            cmd.extend([str(x) for x in (self._bridge_cfg.get("args") or [])])
            env = self._bridge_cfg.get("env") if isinstance(self._bridge_cfg.get("env"), dict) else {}
            self._bridge = _StdioMCPClient(cmd, {str(k): str(v) for k, v in env.items()})
            return self._bridge
        except Exception as exc:  # noqa: BLE001
            self._error = str(exc)
            return None

    def export_tools(self) -> list[dict[str, Any]]:
        if self._tools is not None:
            return self._tools
        bridge = self._ensure_bridge()
        if bridge is None or self._bridge_cfg is None:
            self._tools = []
            return self._tools

        prefix = str(self._bridge_cfg.get("tool_prefix") or "apple_music_")
        tools: list[dict[str, Any]] = []
        for raw in bridge.list_tools():
            raw_name = str(raw.get("name", "")).strip()
            if not raw_name:
                continue
            tools.append(
                {
                    "name": f"{prefix}{raw_name}",
                    "description": str(raw.get("description", "")),
                    "input_schema": raw.get("inputSchema") or raw.get("input_schema") or {"type": "object", "properties": {}},
                    "_raw_name": raw_name,
                }
            )

        self._tools = tools
        return self._tools

    def invoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict:
        bridge = self._ensure_bridge()
        if bridge is None:
            return {"success": False, "error": self._error or "bridge unavailable"}

        for tool in self.export_tools():
            if tool.get("name") == tool_name:
                return bridge.call_tool(str(tool.get("_raw_name", "")), arguments)

        raise RuntimeError(f"unknown bridged tool: {tool_name}")

    async def ainvoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict:
        return self.invoke_tool(tool_name, arguments)

    def register(self, _mcp: Any) -> None:
        return None
