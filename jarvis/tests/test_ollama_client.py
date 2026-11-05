"""Ollama client tests with httpx mock transport."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.ollama_client import OllamaClient, OllamaError


def test_list_models_and_chat():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(
                200,
                json={"models": [{"name": "llama3.2:latest"}]},
            )
        if request.url.path == "/api/chat":
            return httpx.Response(
                200,
                json={"message": {"role": "assistant", "content": "Привіт!"}},
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = OllamaClient("http://test")
    # monkeypatch _client
    client._client = lambda: httpx.Client(base_url="http://test", transport=transport, timeout=5)

    assert client.is_available() is True
    assert "llama3.2:latest" in client.list_models()
    assert client.chat([{"role": "user", "content": "hi"}], "llama3.2") == "Привіт!"


def test_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("fail", request=request)

    transport = httpx.MockTransport(handler)
    client = OllamaClient("http://test")
    client._client = lambda: httpx.Client(base_url="http://test", transport=transport, timeout=5)
    assert client.is_available() is False
