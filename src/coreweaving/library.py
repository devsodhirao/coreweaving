"""Local review records. Saved answers are never retrieved as source authority."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from coreweaving.config import ROOT

LIBRARY_PATH = ROOT / ".agent-cache" / "answers.sqlite3"
REVIEW_STATES = ("unreviewed", "useful", "needs_correction")


@contextmanager
def database(path: Path | None = None):
    path = path or LIBRARY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    path.chmod(0o600)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS answers ("
            "id TEXT PRIMARY KEY, created_at TEXT NOT NULL, question TEXT NOT NULL, "
            "result TEXT NOT NULL, review_state TEXT NOT NULL DEFAULT 'unreviewed', "
            "notes TEXT NOT NULL DEFAULT '', review_history TEXT NOT NULL DEFAULT '[]')"
        )
        yield connection
        connection.commit()
    finally:
        connection.close()


def save_answer(question: str, result: dict, path: Path | None = None) -> None:
    with database(path) as db:
        db.execute(
            "INSERT OR IGNORE INTO answers (id, created_at, question, result) VALUES (?, ?, ?, ?)",
            (
                result["answer_id"],
                datetime.now(UTC).isoformat(),
                question,
                json.dumps(result, ensure_ascii=False),
            ),
        )


def list_answers(path: Path | None = None) -> list[dict]:
    with database(path) as db:
        rows = db.execute("SELECT * FROM answers ORDER BY created_at DESC, id").fetchall()
    return [
        {
            **dict(row),
            "result": json.loads(row["result"]),
            "review_history": json.loads(row["review_history"]),
        }
        for row in rows
    ]


def review_answer(answer_id: str, state: str, notes: str, path: Path | None = None) -> None:
    if state not in REVIEW_STATES:
        raise ValueError("Unknown review state.")
    if state == "needs_correction" and not notes.strip():
        raise ValueError("Describe what needs correcting so the next review has context.")
    with database(path) as db:
        row = db.execute("SELECT review_history FROM answers WHERE id = ?", (answer_id,)).fetchone()
        if row is None:
            raise KeyError(answer_id)
        history = json.loads(row["review_history"])
        history.append({"at": datetime.now(UTC).isoformat(), "state": state, "notes": notes})
        db.execute(
            "UPDATE answers SET review_state = ?, notes = ?, review_history = ? WHERE id = ?",
            (state, notes, json.dumps(history), answer_id),
        )
