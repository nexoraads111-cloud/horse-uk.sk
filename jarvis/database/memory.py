"""Long-term memory store."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .db import Database


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryStore:
    def __init__(self, db: Database) -> None:
        self.db = db

    def remember(self, key: str, value: str, category: str = "general") -> None:
        with self.db.connection() as conn:
            conn.execute(
                "INSERT INTO memories(key, value, category, updated_at) VALUES(?, ?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, "
                "category=excluded.category, updated_at=excluded.updated_at",
                (key, value, category, _utc_now()),
            )

    def recall(self, key: str) -> str | None:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT value FROM memories WHERE key=?", (key,)
            ).fetchone()
        return None if row is None else str(row["value"])

    def list_all(self, category: str | None = None) -> list[dict[str, Any]]:
        with self.db.connection() as conn:
            if category:
                rows = conn.execute(
                    "SELECT id, key, value, category, updated_at FROM memories "
                    "WHERE category=? ORDER BY updated_at DESC",
                    (category,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, key, value, category, updated_at FROM memories "
                    "ORDER BY updated_at DESC"
                ).fetchall()
        return [dict(r) for r in rows]

    def forget(self, key: str) -> bool:
        with self.db.connection() as conn:
            cur = conn.execute("DELETE FROM memories WHERE key=?", (key,))
            return cur.rowcount > 0

    def clear(self) -> None:
        with self.db.connection() as conn:
            conn.execute("DELETE FROM memories")

    def context_snippet(self, limit: int = 20) -> str:
        items = self.list_all()[:limit]
        if not items:
            return ""
        lines = [f"- {m['key']}: {m['value']}" for m in items]
        return "Відомі факти про користувача:\n" + "\n".join(lines)
