"""ActionExecutor safety tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from automation.safety import ActionExecutor
from core.actions import ProposedAction, RiskLevel


class DummyApps:
    def open_app(self, name):
        return True, f"opened {name}"

    def list_installed(self):
        return [{"name": "x", "path": "/x"}]

    def list_running(self):
        return []


def test_rejects_without_confirm():
    ex = ActionExecutor(
        confirm_callback=lambda a, r: False,
        confirm_destructive=True,
        confirm_shell=True,
        apps=DummyApps(),
    )
    act = ProposedAction("close_app", {"name": "x"}, RiskLevel.SENSITIVE, {})
    res = ex.execute(act)
    assert res.success is False
    assert "Відхилено" in res.message


def test_safe_action_runs():
    ex = ActionExecutor(
        confirm_callback=lambda a, r: False,
        apps=DummyApps(),
    )
    act = ProposedAction("open_app", {"name": "x"}, RiskLevel.SAFE, {})
    res = ex.execute(act)
    assert res.success is True


def test_emergency_stop_blocks():
    ex = ActionExecutor(apps=DummyApps())
    ex.emergency_stop()
    act = ProposedAction("open_app", {"name": "x"}, RiskLevel.SAFE, {})
    res = ex.execute(act)
    assert res.success is False


def test_blocked_shell_patterns():
    ex = ActionExecutor(
        confirm_callback=lambda a, r: True,
        confirm_shell=True,
    )
    act = ProposedAction(
        "run_shell",
        {"command": "rm -rf /"},
        RiskLevel.DESTRUCTIVE,
        {},
    )
    res = ex.execute(act, pre_approved=True)
    assert res.success is False
    assert "заблоковано" in res.message.lower() or "політик" in res.message.lower()
