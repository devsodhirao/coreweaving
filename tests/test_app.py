"""UI reruns must never turn conversation history into another paid request."""

from types import SimpleNamespace

import streamlit as st
from streamlit.testing.v1 import AppTest

from coreweaving.config import ROOT, Settings


def test_each_submission_runs_once_across_layout_changes_and_reset(monkeypatch, tmp_path):
    requests = []

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
            return {
                "answer_id": f"test-{len(requests)}",
                "answer": f"Checked answer to: {question}",
                "verification": verification,
                "verification_attempts": [],
                "sources": [],
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
        assert any(x.label == "Did it answer the whole question?" for x in app.expander)
        assert any("Explain the requested Signal setup." in x.value for x in app.markdown)

        app.radio[0].set_value("Answer library").run()
        assert not app.exception
        assert len(requests) == 2
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
    finally:
        st.cache_resource.clear()
