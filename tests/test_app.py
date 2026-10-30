"""UI reruns must never turn conversation history into another paid request."""

from concurrent.futures import Future
from copy import deepcopy
from types import SimpleNamespace

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from coreweaving.config import ROOT, Settings


def test_each_submission_runs_once_across_inspection_and_reset(monkeypatch):
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
                    issues=["Explain the requested Signal setup."],
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
                    else "Which framework are you using? That determines the integration steps."
                    if len(requests) == 7
                    else f"Checked answer to: {question}"
                ),
                "kind": (
                    "insufficient" if len(requests) in (4, 5)
                    else "clarification" if len(requests) == 7 else "answer"
                ),
                "task_complete": len(requests) not in (5, 7),
                "verification": verification,
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
        assert not any(x.label == "What the check found" for x in app.expander)
        assert sum(b.label == "Sources & analysis" for b in app.button) == 2
        app.button(key="analysis_test-2").click().run()
        assert not app.exception
        assert any(x.label == "What the check found" for x in app.expander)
        assert any("Explain the requested Signal setup." in x.value for x in app.markdown)
        assert len(requests) == 2  # Inspection must not rerun the agent.

        next(button for button in app.button if button.label == "New conversation").click().run()
        assert len(requests) == 2
        assert app.chat_input[0].key == "welcome_question"
        next(button for button in app.button if button.label == "Trace an agent →").click().run()
        assert not app.exception
        assert len(requests) == 3
        assert "multi-turn agent" in requests[-1][0]
        assert requests[-1][1] != requests[0][1]
        assert any("Answer not checked" in x.value for x in app.caption)
        assert any("skipped the answer check" in x.value for x in app.warning)
        app.run()
        assert len(requests) == 3

        next(button for button in app.button if button.label == "New conversation").click().run()
        app.chat_input[0].set_value("A question the checker cannot resolve.").run()
        assert not app.exception
        assert len(requests) == 4
        assert any("1 document sections found" in x.value for x in app.caption)
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
        assert any("Partial answer · checked against the docs" in x.value for x in app.caption)
        assert not any("Answer checked against the docs" in x.value for x in app.caption)
        assert len(requests) == 5

        # A batched typed submission and preset click must consume the preset
        # even though typed text wins. Later renders cannot submit it silently.
        next(button for button in app.button if button.label == "New conversation").click().run()
        app.chat_input[0].set_value("Prefer this typed question.")
        next(button for button in app.button if button.label == "Trace an agent →").click().run()
        assert not app.exception
        assert len(requests) == 6 and requests[-1][0] == "Prefer this typed question."
        app.run()
        assert not app.exception
        assert len(requests) == 6

        app.chat_input[0].set_value("Give me exact integration steps for my app.").run()
        assert not app.exception
        assert len(requests) == 7
        assert any("Waiting for your reply" in item.value for item in app.caption)
        assert not any("Partial answer · checked against the docs" in item.value for item in app.caption)
    finally:
        st.cache_resource.clear()


def test_pending_work_survives_reruns_and_reports_real_sources(monkeypatch):
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
                "sources": [],
                "actions": [],
                "elapsed_seconds": 0.1,
                "trace_url": "https://example.test/trace",
                "snapshot_id": "test-snapshot",
            }

    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", DeferredPool)
    monkeypatch.setattr("coreweaving.agent.Agent", FakeAgent)
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
        assert app.status[0].state == "running"
        # A queued request is visible once while it runs, before any answer exists.
        assert sum(item.value == "Explain tracing." for item in app.markdown) == 1
        events = app.session_state.job["events"]
        events.put({"stage": "search_docs", "detail": {"query": "tracing"}})
        events.put({"stage": "read_page", "detail": {"page_id": "agents", "section": 0}})
        app.run()
        assert any("Searches: 1 · Pages read: 0" in item.value for item in app.caption)
        events.put(
            {
                "stage": "source_read",
                "detail": {
                    "title": "Tracing agents",
                    "url": "https://docs.wandb.ai/weave/guides/tracking/agents/",
                },
            }
        )
        app.run()
        assert not app.exception
        assert any("Searches: 1 · Pages read: 1" in item.value for item in app.caption)
        assert any("[Tracing agents]" in item.value for item in app.markdown)
        assert len(pending) == 1 and requests == []

        events.put({"stage": "submit_answer", "detail": {}})
        app.run()
        assert app.status[0].state == "running"
        assert "Checking the answer against its sources" in app.status[0].label

        future, function, args = pending[0]
        future.set_result(function(*args))
        app.run()
        app.run()
        assert not app.exception
        assert requests == ["Explain tracing."]
        assert len(pending) == 1
        assert any("Checked answer." in item.value for item in app.markdown)
        assert sum(item.value == "Explain tracing." for item in app.markdown) == 1
        assert not app.chat_input[0].disabled
        assert not app.status
    finally:
        st.cache_resource.clear()


def test_chat_images_become_text_without_losing_code_or_links(monkeypatch):
    content = r"""## Example

- A list item.

[Read docs](https://docs.wandb.ai/weave/)

![Inline alt](https://image.example.test/inline.png)

![Reference alt][picture]

[picture]: https://image.example.test/reference.png

\![Escaped image](https://image.example.test/escaped.png)

`![Inline code](https://image.example.test/code.png)`

```markdown
![Fenced code](https://image.example.test/fenced.png)
```

<img src="https://image.example.test/html.png">
<script>alert("synthetic")</script>
"""
    result = {
        "answer_id": "markdown-images",
        "answer": content,
        "verification": {"passed": True, "issues": []},
        "sources": [],
        "actions": [],
        "elapsed_seconds": 0.1,
        "snapshot_id": "test-snapshot",
        "conversation_context": [{"role": "user", "content": content}],
    }

    def unexpected_agent(*args, **kwargs):
        raise AssertionError("Rendering saved text must not call the agent.")

    monkeypatch.setattr("coreweaving.agent.Agent", unexpected_agent)
    monkeypatch.setattr(
        "coreweaving.corpus.Corpus", lambda: SimpleNamespace(pages={}, snapshot_id="test-snapshot")
    )
    monkeypatch.setattr("coreweaving.config.settings", lambda: Settings(project="test/test"))
    monkeypatch.setattr(
        "coreweaving.config.init_weave", lambda: SimpleNamespace(flush=lambda: None)
    )

    def check_rendered(app, expected_count):
        assert not app.exception
        rendered = app.get("html")
        assert len(rendered) == expected_count
        for element in rendered:
            html = element.proto.body
            assert not element.proto.unsafe_allow_javascript
            assert "<img" not in html and "<script" not in html
            assert "Inline alt" in html and "Reference alt" in html
            assert "&lt;img src=" in html and "&lt;script&gt;" in html
            assert '<a href="https://docs.wandb.ai/weave/">Read docs</a>' in html
            assert "<li>A list item.</li>" in html
            assert "<code>![Inline code](https://image.example.test/code.png)</code>" in html
            assert '<code class="language-markdown">![Fenced code]' in html
            assert '!<a href="https://image.example.test/escaped.png">Escaped image</a>' in html
        # Both conversation messages retain headings and ordinary formatting.
        assert sum("<h2>Example</h2>" in item.proto.body for item in rendered) == 2
        assert not any(content in element.value for element in app.markdown)

    st.cache_resource.clear()
    try:
        app = AppTest.from_file(ROOT / "app.py", default_timeout=10).run()
        app.session_state.turns = [(content, result)]
        app.run()
        check_rendered(app, 2)  # The user question and assistant answer.

        # Streamlit dedents Markdown. Classification must use those same bytes
        # or an indented image could be mistaken for a harmless code block.
        indented = "    ![Indented alt](https://image.example.test/indented.png)"
        app.session_state.turns = [(indented, {**result, "answer": indented})]
        app.run()
        assert not app.exception
        assert len(app.get("html")) == 2
        assert all(item.proto.body == "<p>Indented alt</p>" for item in app.get("html"))

        literal = "`![Literal image](https://image.example.test/literal.png)`"
        app.session_state.turns = [(literal, {**result, "answer": literal})]
        app.run()
        assert not app.exception and not app.get("html")
        assert sum(item.value == literal for item in app.markdown) == 2
    finally:
        st.cache_resource.clear()


@pytest.mark.parametrize("as_objects", [False, True])
def test_partial_answer_keeps_unresolved_question_visible_without_new_calls(
    monkeypatch, as_objects
):
    def unexpected_agent(*args, **kwargs):
        raise AssertionError("Inspecting task checks must not call the agent.")

    monkeypatch.setattr("coreweaving.agent.Agent", unexpected_agent)
    monkeypatch.setattr(
        "coreweaving.corpus.Corpus", lambda: SimpleNamespace(pages={}, snapshot_id="test-snapshot")
    )
    monkeypatch.setattr("coreweaving.config.settings", lambda: Settings(project="test/test"))
    monkeypatch.setattr(
        "coreweaving.config.init_weave", lambda: SimpleNamespace(flush=lambda: None)
    )
    description = "Explain when the workflow runs."
    missing = [{"description": description}] if as_objects else [description]
    original = deepcopy(missing)
    result = {
        "answer_id": "task-partial",
        "answer": "The documented role is established, but timing remains unresolved.",
        "kind": "insufficient",
        "task_complete": False,
        "missing_outcomes": missing,
        "verification": {
            "passed": True,
            "issues": [],
            "missing_parts": [description],
        },
        "sources": [],
        "actions": [],
        "elapsed_seconds": 0.1,
        "snapshot_id": "test-snapshot",
        "trace_url": "https://example.test/task-partial",
    }
    st.cache_resource.clear()
    try:
        app = AppTest.from_file(ROOT / "app.py", default_timeout=10).run()
        app.session_state["turns"] = [("Explain its role and when it runs.", result)]
        app.run()
        assert not app.exception
        assert any("Still to answer:" in item.value for item in app.markdown)
        assert any(description in item.value for item in app.markdown)
        assert any("Partial answer · checked against the docs" in item.value for item in app.caption)
        app.button(key="analysis_task-partial").click().run()
        assert not app.exception
        assert sum(description in item.value for item in app.markdown) == 2
        assert not any("The check found no unsupported claims" in item.value for item in app.caption)
        assert result["missing_outcomes"] == original
    finally:
        st.cache_resource.clear()


def test_analysis_distinguishes_clean_audit_from_rejection_without_details(monkeypatch):
    def unexpected_agent(*args, **kwargs):
        raise AssertionError("Inspecting a verdict must not call the agent.")

    monkeypatch.setattr("coreweaving.agent.Agent", unexpected_agent)
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
        for passed in (True, False):
            result = {
                "answer_id": f"audit-{passed}",
                "answer": "An answer to inspect.",
                "verification": {"passed": passed, "issues": [], "missing_parts": []},
                "sources": [],
                "actions": [],
                "elapsed_seconds": 0.1,
                "trace_url": "https://example.test/audit",
            }
            app.session_state.turns = [("Question.", result)]
            app.run()
            app.button(key=f"analysis_audit-{passed}").click().run()
            assert not app.exception
            clean = "The check found no unsupported claims or missing answers. It can still miss mistakes."
            rejected = "The answer check failed without explaining why."
            assert any(item.value == clean for item in app.caption) is passed
            assert any(item.value == rejected for item in app.caption) is not passed
    finally:
        st.cache_resource.clear()
