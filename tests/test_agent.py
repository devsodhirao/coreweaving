import pytest

from coreweaving.agent import Agent, Session
from coreweaving.config import Settings
from coreweaving.corpus import Corpus


def response(*calls):
    return {
        "content": [
            {"type": "tool_use", "id": f"call-{i}", "name": name, "input": args}
            for i, (name, args) in enumerate(calls)
        ],
        "stop_reason": "tool_use",
        "usage": {},
    }


def verdict(passed=True):
    return response(
        (
            "record_verdict",
            {
                "passed": passed,
                "claims": [
                    {
                        "text": "Initialize Weave with a team/project.",
                        "source_ids": ["S1"],
                        "supported": passed,
                    }
                ],
                "issues": [] if passed else ["Remove the unsupported claim."],
            },
        )
    )


READ = ("read_page", {"page_id": "custom-agents-quickstart", "section": 5})
ANSWER = (
    "submit_answer",
    {"answer": 'Call weave.init("team/project") first. [S1]', "kind": "answer"},
)


class FakeModel:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def call(self, **kwargs):
        self.requests.append(kwargs)
        return next(self.responses)


@pytest.fixture(scope="module")
def corpus():
    return Corpus()


@pytest.fixture(autouse=True)
def no_network_config(monkeypatch):
    monkeypatch.setattr(
        "coreweaving.agent.conversation_url", lambda cid: "https://example.test/" + cid
    )


def test_invented_citation_is_rejected_and_repaired(corpus):
    fake = FakeModel(
        [
            response(READ, ("submit_answer", {"answer": "A claim. [S999]"})),
            response(ANSWER),
            verdict(),
        ]
    )
    result = Agent(corpus, Settings(project="test/test"), fake).run("How do I initialize it?")
    assert [check["passed"] for check in result["verification_attempts"]] == [False, True]
    assert "S999" not in result["answer"]
    assert result["verification"]["passed"]


def test_semantically_unsupported_draft_cannot_bypass_verifier(corpus):
    fake = FakeModel([response(READ, ANSWER), verdict(False), response(ANSWER), verdict()])
    result = Agent(corpus, Settings(project="test/test"), fake).run("How do I initialize it?")
    assert len(result["verification_attempts"]) == 2
    assert result["verification_attempts"][0]["claims"][0]["supported"] is False
    assert result["verification"]["passed"] is True


def test_research_budget_stops_an_unproductive_loop(corpus):
    fake = FakeModel([response(("search_docs", {"query": "tracing"}))] * 2)
    result = Agent(corpus, Settings(project="test/test", max_steps=2), fake).run("Explain tracing.")
    assert result["kind"] == "insufficient"
    assert not result["verification"]["passed"]
    assert len(fake.requests) == 2
    assert "research limit" in result["answer"]


def test_follow_up_keeps_checked_dialogue_and_conversation_id(corpus):
    fake = FakeModel([response(READ, ANSWER), verdict(), response(ANSWER), verdict()])
    agent, session = Agent(corpus, Settings(project="test/test"), fake), Session()
    first = agent.run("I'm using Python with Anthropic.", session)
    second = agent.run("What should I initialize first?", session)
    assert first["conversation_id"] == second["conversation_id"]
    second_request = fake.requests[2]["messages"]
    assert second_request[0]["content"] == "I'm using Python with Anthropic."
    assert second_request[1]["content"] == first["answer"]
    assert len(session.history) == 4


def test_provider_failure_does_not_leak_a_draft(corpus):
    class Unavailable:
        def call(self, **kwargs):
            raise ConnectionError("provider unavailable")

    result = Agent(corpus, Settings(project="test/test"), Unavailable()).run("A question")
    assert result["kind"] == "error"
    assert result["error_type"] == "ConnectionError"
    assert result["verification"]["passed"] is False


def test_model_cannot_override_execution_limits(corpus):
    agent = Agent(corpus, Settings(project="test/test"), FakeModel([]))
    with pytest.raises(ValueError, match="Expected exactly"):
        agent.execute("run_python", {"code": "while True: pass", "timeout": 999}, Session())


def test_clarification_is_checked_even_without_sources(corpus):
    fake = FakeModel(
        [
            response(
                (
                    "submit_answer",
                    {"answer": "What do you want to monitor?", "kind": "clarification"},
                )
            ),
            response(("record_verdict", {"passed": True, "claims": [], "issues": []})),
        ]
    )
    result = Agent(corpus, Settings(project="test/test"), fake).run("How do I monitor it?")
    assert result["kind"] == "clarification"
    assert result["verification"]["passed"]
    assert fake.requests[1]["purpose"] == "verification"


def test_usage_includes_rejected_verification_and_isolated_follow_up(corpus):
    responses = [
        response(READ, ANSWER),
        verdict(False),
        response(ANSWER),
        verdict(),
        response(ANSWER),
        verdict(),
    ]
    for index, item in enumerate(responses, 1):
        item.update(
            model="claude-sonnet-5-5",
            response_id=f"fixture-{index}",
            usage={"input_tokens": index * 100, "output_tokens": index * 10},
        )
    fake = FakeModel(responses)
    agent, session = Agent(corpus, Settings(project="test/test"), fake), Session()
    first = agent.run("How do I initialize Weave?", session)
    second = agent.run("Remind me what to initialize first.", session)
    receipt = first["metrics"]
    assert first["verification_attempts"][0]["passed"] is False
    assert first["verification"]["passed"] is True
    assert receipt["model_calls"] == 4
    assert receipt["by_purpose"]["planner"]["calls"] == 2
    assert receipt["by_purpose"]["verification"]["calls"] == 2
    assert receipt["tokens"]["input_tokens"] == 1000
    assert receipt["tokens"]["output_tokens"] == 100
    assert receipt["estimated_usd"] == pytest.approx(0.003)
    assert receipt["research"]["drafts_submitted"] == 2
    assert second["metrics"]["model_calls"] == 2
    assert second["metrics"]["tokens"]["input_tokens"] == 1100
    assert second["metrics"]["tokens"]["output_tokens"] == 110
    assert second["metrics"]["estimated_usd"] == pytest.approx(0.0033)
    assert len(first["metrics"]["calls"]) == 4
    assert first["answer_id"] != second["answer_id"]
    assert first["conversation_id"] == second["conversation_id"]
