"""Screenshot analysis via local Ollama vision models."""

from __future__ import annotations

from pathlib import Path

from core.ollama_client import OllamaClient, OllamaError


class VisionAnalyzer:
    def __init__(self, client: OllamaClient, model: str = "llava") -> None:
        self.client = client
        self.model = model

    def set_model(self, model: str) -> None:
        self.model = model

    def analyze(self, image_path: Path | str, question: str) -> str:
        prompt = question or "Опиши українською, що видно на цьому знімку екрана."
        try:
            return self.client.analyze_image(image_path, prompt, self.model)
        except OllamaError as exc:
            return (
                f"Не вдалося проаналізувати зображення. "
                f"Переконайтесь, що модель «{self.model}» встановлена (ollama pull {self.model}). "
                f"Деталі: {exc}"
            )
