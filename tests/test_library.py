from copy import deepcopy

import pytest

from coreweaving.library import list_answers, review_answer, save_answer


@pytest.fixture
def answer():
    return {
        "answer_id": "turn-one",
        "answer": "Use the current workflow. [S1]",
        "snapshot_id": "a" * 64,
        "verification": {"passed": True, "issues": []},
        "sources": [{"source_id": "S1", "page_id": "agents", "text": "Original evidence"}],
        "metrics": {"estimated_usd": None, "known_estimated_usd": 0.001},
        "conversation_id": "conversation-one",
        "trace_url": "https://example.test/conversation-one",
    }


def test_save_persists_evidence_without_implicitly_approving_it(tmp_path, answer):
    path = tmp_path / "nested" / "answers.sqlite3"
    original = deepcopy(answer)
    save_answer("Explain Signals — simply.", answer, path)
    answer["sources"][0]["text"] = "Changed in memory"
    saved = list_answers(path)[0]
    assert saved["question"] == "Explain Signals — simply."
    assert saved["result"] == original
    assert saved["review_state"] == "unreviewed"
    assert saved["review_history"] == []
    assert saved["notes"] == ""
    assert path.stat().st_mode & 0o777 == 0o600


def test_repeat_save_is_idempotent_and_cannot_overwrite_review_or_evidence(tmp_path, answer):
    path = tmp_path / "answers.sqlite3"
    save_answer("Original question", answer, path)
    review_answer(answer["answer_id"], "useful", "Checked the sources.", path)
    original = list_answers(path)[0]
    changed = {**answer, "answer": "Different answer", "snapshot_id": "b" * 64}
    save_answer("Replacement question", changed, path)
    rows = list_answers(path)
    assert len(rows) == 1
    assert rows[0] == original


def test_explicit_reviews_keep_history_and_do_not_rewrite_source_check(tmp_path, answer):
    path = tmp_path / "answers.sqlite3"
    save_answer("Question", answer, path)
    review_answer(answer["answer_id"], "useful", "Looks useful", path)
    review_answer(answer["answer_id"], "needs_correction", "Missing the legacy warning", path)
    review_answer(answer["answer_id"], "unreviewed", "Rechecking after feedback", path)
    saved = list_answers(path)[0]
    assert saved["review_state"] == "unreviewed"
    assert [review["state"] for review in saved["review_history"]] == [
        "useful",
        "needs_correction",
        "unreviewed",
    ]
    assert saved["review_history"][1]["notes"] == "Missing the legacy warning"
    assert all(review["at"] for review in saved["review_history"])
    assert saved["result"]["verification"]["passed"] is True
    assert saved["result"] == answer


def test_snapshot_identity_and_original_answers_survive_newer_runs(tmp_path, answer):
    path = tmp_path / "answers.sqlite3"
    save_answer("Same question", answer, path)
    newer = deepcopy(answer)
    newer["answer_id"] = "turn-two"
    newer["snapshot_id"] = "a" * 12 + "b" * 52
    newer["verification"]["passed"] = False
    save_answer("Same question", newer, path)
    rows = {row["id"]: row for row in list_answers(path)}
    assert len(rows) == 2
    assert rows["turn-one"]["result"]["snapshot_id"] == "a" * 64
    assert rows["turn-two"]["result"]["snapshot_id"] == "a" * 12 + "b" * 52
    assert rows["turn-one"]["result"]["sources"] == answer["sources"]
    assert all(row["review_state"] == "unreviewed" for row in rows.values())


def test_invalid_reviews_fail_without_mutating_saved_history(tmp_path, answer):
    path = tmp_path / "answers.sqlite3"
    save_answer("Question", answer, path)
    before = list_answers(path)
    with pytest.raises(ValueError, match="Unknown review state"):
        review_answer(answer["answer_id"], "verified", "", path)
    with pytest.raises(ValueError, match="Describe what needs correcting"):
        review_answer(answer["answer_id"], "needs_correction", " \n ", path)
    with pytest.raises(KeyError):
        review_answer("missing-id", "useful", "", path)
    assert list_answers(path) == before
