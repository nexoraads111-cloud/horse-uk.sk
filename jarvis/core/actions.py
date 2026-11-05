"""Restricted action catalog — AI may only propose these named actions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    SAFE = "safe"
    SENSITIVE = "sensitive"
    DESTRUCTIVE = "destructive"


@dataclass
class ActionSpec:
    name: str
    description: str
    risk: RiskLevel
    params: list[str] = field(default_factory=list)


ALLOWED_ACTIONS: dict[str, ActionSpec] = {
    "open_app": ActionSpec("open_app", "Відкрити програму", RiskLevel.SAFE, ["name"]),
    "switch_app": ActionSpec("switch_app", "Перемкнутись на вікно", RiskLevel.SAFE, ["name"]),
    "close_app": ActionSpec(
        "close_app", "Закрити програму", RiskLevel.SENSITIVE, ["name"]
    ),
    "list_apps": ActionSpec("list_apps", "Список встановлених/запущених програм", RiskLevel.SAFE),
    "open_path": ActionSpec(
        "open_path", "Відкрити файл або теку", RiskLevel.SAFE, ["path"]
    ),
    "screenshot": ActionSpec("screenshot", "Зробити знімок екрана", RiskLevel.SAFE),
    "analyze_screen": ActionSpec(
        "analyze_screen", "Проаналізувати знімок екрана", RiskLevel.SAFE, ["question"]
    ),
    "type_text": ActionSpec(
        "type_text", "Ввести текст у активне вікно", RiskLevel.SENSITIVE, ["text"]
    ),
    "remember": ActionSpec(
        "remember", "Запам'ятати факт", RiskLevel.SAFE, ["key", "value"]
    ),
    "recall": ActionSpec("recall", "Пригадати факт", RiskLevel.SAFE, ["key"]),
    "cursor_launch": ActionSpec(
        "cursor_launch", "Запустити Cursor IDE", RiskLevel.SAFE
    ),
    "cursor_open_project": ActionSpec(
        "cursor_open_project",
        "Відкрити проєкт у Cursor",
        RiskLevel.SAFE,
        ["path"],
    ),
    "cursor_prepare_prompt": ActionSpec(
        "cursor_prepare_prompt",
        "Підготувати промпт для Cursor (вставка після підтвердження)",
        RiskLevel.SENSITIVE,
        ["prompt"],
    ),
    "run_shell": ActionSpec(
        "run_shell",
        "Виконати команду оболонки (лише з явним підтвердженням)",
        RiskLevel.DESTRUCTIVE,
        ["command"],
    ),
    "set_task": ActionSpec(
        "set_task", "Додати задачу", RiskLevel.SAFE, ["title"]
    ),
}


ACTION_JSON_RE = re.compile(
    r"```json\s*(\{.*?\})\s*```|<<<ACTION>>>\s*(\{.*?\})\s*<<<END>>>",
    re.DOTALL | re.IGNORECASE,
)


@dataclass
class ProposedAction:
    name: str
    params: dict[str, Any]
    risk: RiskLevel
    raw: dict[str, Any]


def parse_actions_from_reply(text: str) -> tuple[str, list[ProposedAction]]:
    """Extract optional action blocks; return clean reply + actions."""
    actions: list[ProposedAction] = []
    clean = text

    for match in ACTION_JSON_RE.finditer(text):
        blob = match.group(1) or match.group(2)
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        name = str(data.get("action") or data.get("name") or "").strip()
        if name not in ALLOWED_ACTIONS:
            continue
        spec = ALLOWED_ACTIONS[name]
        params = {k: data.get(k) for k in spec.params if k in data}
        # also allow nested "params"
        if isinstance(data.get("params"), dict):
            params.update({k: v for k, v in data["params"].items() if k in spec.params or not spec.params})
        actions.append(
            ProposedAction(name=name, params=params, risk=spec.risk, raw=data)
        )
        clean = clean.replace(match.group(0), "").strip()

    return clean, actions


def action_help_for_prompt() -> str:
    lines = [
        "Якщо потрібно виконати дію на комп'ютері, додай у відповідь блок:",
        "```json",
        '{"action": "open_app", "name": "notepad"}',
        "```",
        "Дозволені дії:",
    ]
    for spec in ALLOWED_ACTIONS.values():
        lines.append(f"- {spec.name}: {spec.description} (ризик: {spec.risk.value})")
    lines.append(
        "Ніколи не пропонуй дії поза списком. Для run_shell потрібне явне підтвердження користувача."
    )
    return "\n".join(lines)


def needs_confirmation(action: ProposedAction, confirm_destructive: bool, confirm_shell: bool) -> bool:
    if action.name == "run_shell" and confirm_shell:
        return True
    if action.risk == RiskLevel.DESTRUCTIVE and confirm_destructive:
        return True
    if action.risk == RiskLevel.SENSITIVE and confirm_destructive:
        return True
    return False
