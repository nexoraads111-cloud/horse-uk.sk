"""HTTP client for local Ollama (chat + vision)."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Callable, Iterator

import httpx


class OllamaError(Exception):
    """Raised when Ollama is unreachable or returns an error."""


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def is_available(self) -> bool:
        try:
            with self._client() as client:
                r = client.get("/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            with self._client() as client:
                r = client.get("/api/tags")
                r.raise_for_status()
                data = r.json()
                return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except Exception as exc:
            raise OllamaError(f"Не вдалося отримати список моделей: {exc}") from exc

    def chat(
        self,
        messages: list[dict[str, Any]],
        model: str,
        stream: bool = False,
        on_token: Callable[[str], None] | None = None,
    ) -> str:
        payload = {"model": model, "messages": messages, "stream": stream}
        try:
            if stream and on_token is not None:
                return self._chat_stream(payload, on_token)
            with self._client() as client:
                r = client.post("/api/chat", json=payload)
                r.raise_for_status()
                data = r.json()
                return str(data.get("message", {}).get("content", ""))
        except httpx.HTTPError as exc:
            raise OllamaError(
                "Ollama недоступна. Переконайтесь, що Ollama запущена "
                f"({self.base_url}). Помилка: {exc}"
            ) from exc

    def _chat_stream(self, payload: dict[str, Any], on_token: Callable[[str], None]) -> str:
        parts: list[str] = []
        with self._client() as client:
            with client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        parts.append(token)
                        on_token(token)
                    if chunk.get("done"):
                        break
        return "".join(parts)

    def generate(self, prompt: str, model: str) -> str:
        try:
            with self._client() as client:
                r = client.post(
                    "/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False},
                )
                r.raise_for_status()
                return str(r.json().get("response", ""))
        except httpx.HTTPError as exc:
            raise OllamaError(f"Помилка generate: {exc}") from exc

    def analyze_image(
        self,
        image_path: Path | str,
        prompt: str,
        model: str,
    ) -> str:
        path = Path(image_path)
        if not path.exists():
            raise OllamaError(f"Файл зображення не знайдено: {path}")
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        messages = [
            {
                "role": "user",
                "content": prompt,
                "images": [b64],
            }
        ]
        return self.chat(messages, model=model, stream=False)

    def pull_model(self, name: str) -> Iterator[dict[str, Any]]:
        """Yield progress events while pulling a model."""
        with self._client() as client:
            with client.stream("POST", "/api/pull", json={"name": name}) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
