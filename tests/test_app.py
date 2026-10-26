"""UI reruns must never turn conversation history into another paid request."""

from concurrent.futures import Future
from types import SimpleNamespace

import streamlit as st
from streamlit.testing.v1 import AppTest

from coreweaving.config import ROOT, Settings


def test_each_submission_runs_once_across_layout_changes_and_reset(monkeypatch, tmp_path):
    requests = []

    class ImmediatePool:
        def __init__(self, **kwargs):
            pass

        def submit(self, function, *args):
            future = Future()
            future.set_result(function(*args))
            return future

    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", ImmediatePool)

    class FakeAgent:
        def __init__(self, *args):
            pass

        def run(self, question, session, update):
            requests.append((question, session.conversation_id))
            verification = {"passed": True, "issues": []}
            if len(requests) == 2:
                verification.update(
                    status="passed",
                    mode="support+coverage",
                    coverage=[
                        {
                            "obligation": "Explain the requested Signal setup.",
                            "status": "covered",
                            "reason": "The answer gives the requested steps.",
                            "source_ids": [],
                        }
                    ],
                )
            elif len(requests) == 3:
                verification.update(passed=False, status="not_run", mode="off")
            elif len(requests) == 4:
                verification.update(passed=False, status="failed")
            return {
                "answer_id": f"test-{len(requests)}",
                "answer": (
                    "Internal research limit diagnostic."
                    if len(requests) == 4
                    else f"Checked answer to: {question}"
                ),
                "kind": "insufficient" if len(requests) in (4, 5) else "answer",
                "recovered_partial": len(requests) == 5,
                "verification": verification,
                "verification_attempts": [],
                "sources": [],
                "all_read_evidence": [
                    {
                        "source_id": "S1",
                        "url": "https://docs.wandb.ai/weave/guides/tracking/agents/",
                        "title": "Tracing agents",
                        "heading": "Conversations",
                        "text": "A passage read during research.",
                    },
                    {"source_id": "C1", "code": "print(1)", "output": "1"},
                ]
                if len(requests) == 4
                else [],
                "actions": [],
                "elapsed_seconds": 0.1,
                "trace_url": "https://example.test/" + session.conversation_id,
                "snapshot_id": "test-snapshot",
            }

    monkeypatch.setattr("coreweaving.agent.Agent", FakeAgent)
    monkeypatch.setattr("coreweaving.library.LIBRARY_PATH", tmp_path / "answers.sqlite3")
    monkeypatch.setattr(
        "coreweaving.corpus.Corpus", lambda: SimpleNamespace(pages={}, snapshot_id="test-snapshot")
    )
    monkeypatch.setattr("coreweaving.config.settings", lambda: Settings(project="test/test"))
    monkeypatch.setattr(
        "coreweaving.config.init_weave", lambda: SimpleNamespace(flush=lambda: None)
    )
    st.cache_resource.clear()
    try:
        app = AppTest.from_file(ROOT / "app.py", default_timeout=10).run()
        assert not app.exception
        assert app.chat_input[0].key == "welcome_question"

        app.chat_input[0].set_value("Explain tracing.").run()
        assert not app.exception
        assert len(requests) == 1
        assert app.chat_input[0].key == "conversation_question"

        app.run()  # An ordinary UI rerun must not replay the previous question.
        assert len(requests) == 1
        app.chat_input[0].set_value("How do I add a Signal?").run()
        assert not app.exception
        assert [text for text, _ in requests] == ["Explain tracing.", "How do I add a Signal?"]
        assert requests[0][1] == requests[1][1]
        assert len(app.chat_input) == 1
        assert not any(x.label == "Did it answer the whole question?" for x in app.expander)
        assert sum(b.label == "Sources & analysis" for b in app.button) == 2
        app.button(key="analysis_test-2").click().run()
        assert not app.exception
        assert any(x.label == "Did it answer the whole question?" for x in app.expander)
        assert any("Explain the requested Signal setup." in x.value for x in app.markdown)
        assert len(requests) == 2  # Inspection must not rerun the agent.

        app.radio[0].set_value("Answer library").run()
        assert not app.exception
        assert len(requests) == 2
        app.button(key="analysis_test-2").click().run()
        assert not app.exception
        assert any("Explain the requested Signal setup." in x.value for x in app.markdown)
        assert len(requests) == 2  # Saved-answer inspection must not submit a new question.
        next(item for item in app.selectbox if item.label == "Your assessment").set_value("useful")
        app.text_area[0].set_value("Reviewed in the isolated UI test.")
        next(button for button in app.button if button.label == "Save my review").click().run()
        assert not app.exception
        from coreweaving.library import list_answers

        saved = list_answers()
        assert len(saved) == 2
        assert sum(item["review_state"] == "useful" for item in saved) == 1
        assert len(requests) == 2
        app.radio[0].set_value("Conversation").run()
        assert len(requests) == 2

        next(button for button in app.button if button.label == "New conversation").click().run()
        assert len(requests) == 2
        assert app.chat_input[0].key == "welcome_question"
        next(button for button in app.button if button.label == "Trace an agent →").click().run()
        assert not app.exception
        assert len(requests) == 3
        assert "multi-turn agent" in requests[-1][0]
        assert requests[-1][1] != requests[0][1]
        assert any("Check not run" in x.value for x in app.caption)
        assert any("Verification was disabled" in x.value for x in app.warning)
        app.run()
        assert len(requests) == 3

        next(button for button in app.button if button.label == "New conversation").click().run()
        app.chat_input[0].set_value("A question the checker cannot resolve.").run()
        assert not app.exception
        assert len(requests) == 4
        assert any("1 document passages found" in x.value for x in app.caption)
        assert not any("0 sources" in x.value for x in app.caption)
        assert any("[Tracing agents]" in x.value for x in app.markdown)
        assert not any("research limit" in x.value for x in app.markdown)
        app.button(key="analysis_test-4").click().run()
        assert not app.exception
        assert any("A passage read during research." in x.value for x in app.text)
        assert len(requests) == 4

        next(button for button in app.button if button.label == "New conversation").click().run()
        app.chat_input[0].set_value("Show the part that can be confirmed.").run()
        assert not app.exception
        assert any("Checked points · partial answer" in x.value for x in app.caption)
        assert not any("Source check passed" in x.value for x in app.caption)
        assert len(requests) == 5
    finally:
        st.cache_resource.clear()


def test_pending_work_survives_navigation_and_saves_before_display(monkeypatch, tmp_path):
    pending = []
    requests = []

    class DeferredPool:
        def __init__(self, **kwargs):
            pass

        def submit(self, function, *args):
            future = Future()
            pending.append((future, function, args))
            return future

    class FakeAgent:
        def __init__(self, *args):
            pass

        def run(self, question, session, notify):
            requests.append(question)
            notify({"stage": "thinking", "detail": "Research step 1"})
            return {
                "answer_id": "navigation-survivor",
                "answer": "Checked answer.",
                "verification": {"passed": True, "issues": []},
                "verification_attempts": [],
                "sources": [],
                "actions": [],
                "elapsed_seconds": 0.1,
                "trace_url": "https://example.test/trace",
                "snapshot_id": "test-snapshot",
            }

    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", DeferredPool)
    monkeypatch.setattr("coreweaving.agent.Agent", FakeAgent)
    monkeypatch.setattr("coreweaving.library.LIBRARY_PATH", tmp_path / "answers.sqlite3")
    monkeypatch.setattr(
        "coreweaving.corpus.Corpus", lambda: SimpleNamespace(pages={}, snapshot_id="test-snapshot")
    )
    monkeypatch.setattr("coreweaving.config.settings", lambda: Settings(project="test/test"))
    monkeypatch.setattr(
        "coreweaving.config.init_weave", lambda: SimpleNamespace(flush=lambda: None)
    )
    st.cache_resource.clear()
    try:
        app = AppTest.from_file(ROOT / "app.py", default_timeout=10).run()
        app.chat_input[0].set_value("Explain tracing.").run()
        assert not app.exception
        assert len(pending) == 1
        assert app.chat_input[0].disabled
        assert next(b for b in app.button if b.label == "New conversation").disabled
        app.radio[0].set_value("Answer library").run()
        app.run()
        assert not app.exception
        assert len(pending) == 1 and requests == []

        future, function, args = pending[0]
        future.set_result(function(*args))
        from coreweaving.library import list_answers

        assert len(list_answers()) == 1  # Worker persisted before another UI render.
        app.run()
        app.radio[0].set_value("Conversation").run()
        app.run()
        assert not app.exception
        assert requests == ["Explain tracing."]
        assert len(list_answers()) == 1 and len(pending) == 1
        assert any("Checked answer." in item.value for item in app.markdown)
        assert not app.chat_input[0].disabled
    finally:
        st.cache_resource.clear()


def test_library_duplicate_questions_keep_selected_answer_when_inspecting(monkeypatch):
    """Given duplicate questions, inspecting the newest answer keeps its identity."""
    agent_calls = []

    class UnexpectedAgent:
        def __init__(self, *args, **kwargs):
            agent_calls.append("constructed")
            raise AssertionError("Inspecting a saved answer must not call the agent.")

    records = []
    for answer_id in ("newer-answer", "older-answer"):
        records.append(
            {
                "id": answer_id,
                "created_at": "2026-10-26T01:00:00+00:00",
                "question": "How do I trace a custom multi-turn agent in Python?",
                "review_state": "unreviewed",
                "notes": "",
                "result": {
                    "answer_id": answer_id,
                    "answer": f"Saved response: {answer_id}",
                    "kind": "answer",
                    "verification": {"passed": True, "issues": []},
                    "verification_attempts": [],
                    "sources": [],
                    "actions": [],
                    "elapsed_seconds": 0.1,
                    "trace_url": f"https://example.test/{answer_id}",
                    "snapshot_id": "test-snapshot",
                },
            }
        )

    monkeypatch.setattr("coreweaving.agent.Agent", UnexpectedAgent)
    monkeypatch.setattr("coreweaving.library.list_answers", lambda: records)
    monkeypatch.setattr(
        "coreweaving.corpus.Corpus", lambda: SimpleNamespace(pages={}, snapshot_id="test-snapshot")
    )
    monkeypatch.setattr("coreweaving.config.settings", lambda: Settings(project="test/test"))
    monkeypatch.setattr(
        "coreweaving.config.init_weave", lambda: SimpleNamespace(flush=lambda: None)
    )
    st.cache_resource.clear()
    try:
        app = AppTest.from_file(ROOT / "app.py", default_timeout=10).run()
        app.radio[0].set_value("Answer library").run()
        assert not app.exception
        selected = next(item for item in app.selectbox if item.label == "Saved question")
        assert selected.value == "newer-answer"
        selected_wire_label = selected.options[selected.index]

        # A background request can finish while the library is open. Prepending
        # another matching question must not reuse the selected record's label.
        records.insert(
            0,
            {
                **records[0],
                "id": "background-answer",
                "result": {
                    **records[0]["result"],
                    "answer_id": "background-answer",
                    "answer": "Saved response: background-answer",
                    "trace_url": "https://example.test/background-answer",
                },
            },
        )
        app.run()
        assert not app.exception
        selected = next(item for item in app.selectbox if item.label == "Saved question")
        assert selected.value == "newer-answer"
        assert selected.options[selected.index] == selected_wire_label

        # When inspection reruns the app, the identical question must not select
        # the other record and discard the clicked answer's button event.
        app.button(key="analysis_newer-answer").click().run()

        # Then the chosen record, rendered response and trace all stay together.
        assert not app.exception
        selected = next(item for item in app.selectbox if item.label == "Saved question")
        assert selected.value == "newer-answer"
        assert any(item.value == "Saved response: newer-answer" for item in app.markdown)
        assert not any(item.value == "Saved response: older-answer" for item in app.markdown)
        assert not any(item.value == "Saved response: background-answer" for item in app.markdown)
        dialogs = app.get("dialog")
        assert len(dialogs) == 1 and dialogs[0].proto.dialog.is_open
        links = app.get("link_button")
        assert len(links) == 1 and links[0].proto.url == "https://example.test/newer-answer"
        assert agent_calls == []
    finally:
        st.cache_resource.clear()
