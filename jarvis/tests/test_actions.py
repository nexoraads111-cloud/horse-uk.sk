"""Unit tests for action parsing and risk gates."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.actions import (
    ALLOWED_ACTIONS,
    RiskLevel,
    needs_confirmation,
    parse_actions_from_reply,
    ProposedAction,
)


def test_parse_json_fence():
    text = 'Добре.\n```json\n{"action": "open_app", "name": "notepad"}\n```\n'
    clean, actions = parse_actions_from_reply(text)
    assert "notepad" not in clean or "```" not in clean
    assert len(actions) == 1
    assert actions[0].name == "open_app"
    assert actions[0].params.get("name") == "notepad"
    assert actions[0].risk == RiskLevel.SAFE


def test_parse_action_markers():
    text = '<<<ACTION>>>{"action":"screenshot"}<<<END>>>'
    clean, actions = parse_actions_from_reply(text)
    assert len(actions) == 1
    assert actions[0].name == "screenshot"


def test_unknown_action_ignored():
    text = '```json\n{"action": "rm_rf", "path": "/"}\n```'
    clean, actions = parse_actions_from_reply(text)
    assert actions == []


def test_shell_needs_confirmation():
    act = ProposedAction(
        name="run_shell",
        params={"command": "dir"},
        risk=RiskLevel.DESTRUCTIVE,
        raw={},
    )
    assert needs_confirmation(act, True, True) is True
    assert needs_confirmation(act, True, False) is True  # still destructive


def test_allowed_catalog_has_cursor():
    assert "cursor_launch" in ALLOWED_ACTIONS
    assert "cursor_open_project" in ALLOWED_ACTIONS
    assert "cursor_prepare_prompt" in ALLOWED_ACTIONS
