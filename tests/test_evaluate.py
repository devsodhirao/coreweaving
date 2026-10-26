"""Evaluation checks use fake provider responses; they never spend API credit."""

import asyncio
import copy
import json
import uuid
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from coreweaving import evaluate
from coreweaving.budget import model_budget
from coreweaving.metrics import summarize

ASSERTIONS = [
    {"id": "init", "description": "Names weave.init."},
    {"id": "project", "description": "Uses a team/project string."},
]


def grade_payload():
    return {
        "critique": "The initialization and project format are supported by the cited passage.",
        "assertions": [
            {"id": item["id"], "critique": item["description"], "passed": True}
            for item in ASSERTIONS
        ],
        "correctness": 4,
        "completeness": 4,
        "grounding": 4,
        "uncertainty": 4,
        "explanation": "Both required facts are present and sourced.",
        "failures": [],
    }


def judge_response(payload=None):
    return {
        "content": [
            {"type": "tool_use", "name": "record_grade", "input": payload or grade_payload()}
        ],
        "stop_reason": "tool_use",
        "usage": {"input_tokens": 200, "output_tokens": 100},
        "model": "claude-opus-5-5",
        "response_id": "judge-response",
    }


def passage(source_id="S1", page="quickstart", section=2):
    return {
        "source_id": source_id,
        "page_id": page,
        "section": section,
        "text": "Call weave.init with team/project.",
    }


def answer(mode="off"):
    source = passage()
    return {
        "case_id": "01-init",
        "answer": 'Call weave.init("team/project"). [S1]',
        "kind": "answer",
        "sources": [source],
        "all_read_evidence": [source],
        "actions": [],
        "verify_mode": mode,
        "error_type": None,
        "verification": {
            "passed": mode != "off",
            "status": "not_run" if mode == "off" else "passed",
        },
    }


def metered_call(purpose, input_tokens=100, output_tokens=20, usd=0.001):
    return {
        "purpose": purpose,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
        "estimated_usd": usd,
        "error_type": None,
    }


@pytest.fixture(autouse=True)
def prevent_paid_calls(monkeypatch):
    def forbidden(**kwargs):
        raise AssertionError("A test attempted to construct a real provider client.")

    monkeypatch.setattr(evaluate.anthropic, "Anthropic", forbidden)
    monkeypatch.setattr(evaluate, "RUN_DIRECTORY", None)


def test_off_arm_can_pass_without_verification_or_selected_page_minimum():
    output = answer("off")
    checks = evaluate.integrity(output, minimum_pages=7, require_code=False)
    result = evaluate.quality_result(evaluate.parse_grade(judge_response(), ASSERTIONS), checks)
    assert result["passed"] and result["answer_quality_passed"]
    assert not checks["page_coverage_met"]
    assert evaluate.verification_adherence(output)["policy_followed"]
    assert result["assertion_fraction_passed"] == 1
    output["verify_mode"] = "support"
    assert not evaluate.verification_adherence(output)["policy_followed"]
    assert evaluate.quality_result(evaluate.parse_grade(judge_response(), ASSERTIONS), checks)[
        "passed"
    ]


@pytest.mark.parametrize(
    "change",
    ["missing", "duplicate", "unknown", "extra", "string_bool", "float_score", "no_critique"],
)
def test_invalid_judge_contract_is_rejected(change):
    payload = grade_payload()
    if change == "missing":
        payload["assertions"].pop()
    elif change == "duplicate":
        payload["assertions"][1]["id"] = "init"
    elif change == "unknown":
        payload["assertions"][1]["id"] = "new-assertion"
    elif change == "extra":
        payload["assertions"][0]["confidence"] = 1
    elif change == "string_bool":
        payload["assertions"][0]["passed"] = "true"
    elif change == "float_score":
        payload["correctness"] = 4.0
    elif change == "no_critique":
        payload["assertions"][0]["critique"] = ""
    with pytest.raises((ValueError, ValidationError)):
        evaluate.parse_grade(judge_response(payload), ASSERTIONS)


def test_assertion_failures_override_good_ordinal_scores_and_schema_orders_critique_first():
    payload = grade_payload()
    payload["assertions"][1]["passed"] = False
    result = evaluate.quality_result(
        evaluate.parse_grade(judge_response(payload), ASSERTIONS), {"passed": True}
    )
    assert not result["passed"]
    assert result["assertion_count"] == 2 and result["assertions_passed"] == 1
    assert result["assertion_fraction_passed"] == 0.5
    schema = evaluate.grade_schema(ASSERTIONS)
    assert schema["$defs"]["AssertionJudgment"]["properties"]["id"]["enum"] == ["init", "project"]
    fields = list(schema["$defs"]["AssertionJudgment"]["properties"])
    assert fields.index("critique") < fields.index("passed")
    assert schema["properties"]["assertions"]["minItems"] == 2
    with pytest.raises(ValueError):
        evaluate.validate_assertions(ASSERTIONS + [ASSERTIONS[0]])
    truncated = judge_response()
    truncated["stop_reason"] = "max_tokens"
    with pytest.raises(ValueError):
        evaluate.parse_grade(truncated, ASSERTIONS)


def test_reference_recall_distinguishes_reads_citations_and_valid_alternatives():
    output = answer()
    earlier = {**answer(), "all_read_evidence": [passage("S2", "selected", 1)]}
    output["turns"] = [earlier, copy.deepcopy(output)]
    references = [passage("ref", "selected", 1), passage("ref", "selected", 2)]
    diagnostics = evaluate.reference_diagnostics(output, references)
    assert diagnostics["selected_reference_read_recall"] == 0.5
    assert diagnostics["selected_reference_cited_recall"] == 0
    assert diagnostics["alternative_cited_sections"] == [("quickstart", 2)]
    assert evaluate.integrity(output, 3, False)["passed"]
    assert evaluate.reference_diagnostics(output, [])["selected_reference_read_recall"] is None


def test_integrity_catches_unknown_citations_and_prior_turn_failures_but_counts_prior_code():
    output = answer()
    earlier = {
        **answer(),
        "actions": [{"tool": "run_python", "result": {"exit_code": 0, "stopped": False}}],
    }
    output["turns"] = [earlier, copy.deepcopy(output)]
    assert evaluate.integrity(output, 1, True)["passed"]
    earlier["error_type"] = "ConnectionError"
    assert not evaluate.integrity(output, 1, True)["no_runtime_error"]
    output["answer"] += " [S99]"
    assert not evaluate.integrity(output, 1, False)["citations_resolve"]


def test_trial_rows_are_stable_across_arms_and_offsets_not_predictions():
    rows = [{"case_id": "a"}, {"case_id": "b"}]
    first = evaluate.trial_rows(rows, 2, seed=7)
    assert first == evaluate.trial_rows(rows, 2, seed=7)
    assert len({row["example_id"] for row in first}) == 4
    assert all("prediction_id" not in row for row in first)
    offset = evaluate.trial_rows(rows, 1, seed=7, trial_offset=1)
    assert {row["example_id"] for row in offset} == {"a:trial:2", "b:trial:2"}


def test_persistence_retains_repeated_case_attempts_and_refuses_overwrite(tmp_path):
    identity = {
        "case_id": "case/unsafe",
        "verify_mode": "support+coverage",
        "trial_index": 2,
        "prediction_id": str(uuid.uuid4()),
    }
    evaluate.persist_record(tmp_path, "cases", identity, {"original": True})
    with pytest.raises(FileExistsError):
        evaluate.persist_record(tmp_path, "cases", identity, {"original": False})
    next_identity = {**identity, "prediction_id": str(uuid.uuid4())}
    evaluate.persist_record(tmp_path, "cases", next_identity, {"another": True})
    files = list((tmp_path / "cases").glob("*.json"))
    assert len(files) == 2
    assert {"original": True} in [json.loads(path.read_text()) for path in files]


def test_persistence_publishes_only_complete_json(monkeypatch, tmp_path):
    identity = {"case_id": "a", "prediction_id": str(uuid.uuid4())}
    real_link = evaluate.os.link
    observed = []

    def publish(source, destination):
        assert not destination.exists()
        observed.append(json.loads(source.read_text()))
        real_link(source, destination)

    monkeypatch.setattr(evaluate.os, "link", publish)
    record = {"answer": "evidence " * 500}
    evaluate.persist_record(tmp_path, "predictions", identity, record)
    assert observed == [record]
    assert not list((tmp_path / "predictions").glob(".writing-*"))


def test_all_turn_and_judge_aggregation_does_not_count_final_turn_twice():
    turns = [
        {"metrics": summarize([metered_call("planner")], []), "actions": []},
        {
            "metrics": summarize([metered_call("planner"), metered_call("verification")], []),
            "actions": [],
        },
    ]
    metrics = evaluate.all_turn_metrics(turns)
    assert metrics["model_calls"] == 3
    prediction = {"prediction_id": "p1", "agent_metrics": metrics}
    orphan_prediction = {
        "prediction_id": "p2",
        "agent_metrics": evaluate.all_turn_metrics(turns[:1]),
    }
    cases = [
        {
            "prediction_id": "p1",
            "scores": {
                "passed": False,
                "judge_error": "ValueError",
                "judge_metrics": summarize([metered_call("evaluation-judge", usd=0.002)], []),
            },
        }
    ]
    result = evaluate.aggregate_records([prediction, orphan_prediction], cases)
    assert result["usage"]["agent"]["model_calls"] == 4
    assert result["usage"]["judge"]["model_calls"] == 1
    assert result["usage"]["combined"]["known_estimated_usd"] == pytest.approx(0.006)
    assert result["judge_failures"] == 1 and result["predictions_recorded"] == 2
    with pytest.raises(ValueError):
        evaluate.aggregate_records([prediction, prediction], cases)


def test_budget_reconciliation_preserves_usage_missing_a_completed_receipt():
    completed = {**metered_call("planner"), "response_id": "completed"}
    interrupted = {**metered_call("evaluation-judge", usd=0.002), "response_id": "interrupted"}
    metrics = summarize([completed], [])
    result = evaluate.reconcile_budget_usage([completed, interrupted], metrics)
    assert not result["matched"]
    assert result["known_estimated_usd"] == pytest.approx(0.003)
    assert result["known_estimate_difference_usd"] == pytest.approx(0.002)
    assert result["usage_without_completed_receipt"] == [interrupted]
    assert evaluate.reconcile_budget_usage([completed], metrics)["matched"]


def test_judge_is_blind_to_mode_and_invalid_verdict_keeps_metered_usage(monkeypatch, tmp_path):
    requests = []
    responses = [
        judge_response(),
        judge_response(),
        judge_response({**grade_payload(), "assertions": []}),
    ]

    class FakeJudge:
        def call(self, **kwargs):
            requests.append(kwargs)
            return responses.pop(0)

    monkeypatch.setattr(evaluate, "JudgeLanguageModel", FakeJudge)
    monkeypatch.setattr(evaluate, "RUN_DIRECTORY", tmp_path)
    judge = evaluate.QualityJudge(judge_model="claude-opus-5-5")

    async def score(mode):
        output = answer(mode)
        output["prediction_id"] = str(uuid.uuid4())
        return await judge.score(
            output, ["How do I initialize?"], "Initialize.", [passage()], 1, False, ASSERTIONS
        )

    off, support, invalid = [asyncio.run(score(mode)) for mode in ("off", "support", "off")]
    assert off["passed"] and support["passed"]
    assert requests[0]["messages"] == requests[1]["messages"]
    assert "verification" not in json.loads(requests[0]["messages"][0]["content"])
    assert not invalid["passed"] and invalid["judge_error"] == "ValueError"
    assert invalid["judge_metrics"]["tokens"]["input_tokens"] == 200
    assert len(list((tmp_path / "cases").glob("*.json"))) == 3


def test_judge_leaf_records_gross_usage_once_with_budget_and_raw_provider_usage(monkeypatch):
    raw = {
        "input_tokens": 100,
        "output_tokens": 30,
        "cache_read_input_tokens": 60,
        "cache_creation_input_tokens": 20,
        "cache_creation": {"ephemeral_5m_input_tokens": 20},
    }
    response = SimpleNamespace(
        model="claude-opus-5-5",
        id="provider-id",
        stop_reason="tool_use",
        usage=SimpleNamespace(model_dump=lambda: raw),
        content=[],
    )
    constructors, closed = [], []

    class FakeClient:
        def __init__(self, **kwargs):
            constructors.append(kwargs)
            self.messages = SimpleNamespace(create=lambda **kw: response)

        def close(self):
            closed.append(True)

    monkeypatch.setattr(evaluate.anthropic, "Anthropic", FakeClient)
    call = SimpleNamespace(summary={})
    monkeypatch.setattr(evaluate, "call_context", SimpleNamespace(get_current_call=lambda: call))
    with model_budget(1) as budget:
        result = evaluate.judge_provider_request(
            model="claude-opus-5-5",
            system="Judge",
            messages=[],
            tools=[],
            max_tokens=100,
            purpose="evaluation-judge",
        )
        assert len(budget.snapshot()["calls"]) == 1
    assert constructors[0]["max_retries"] == 0 and closed == [True]
    assert result["provider_usage"]["input_tokens"] == 100 and "usage" not in result
    assert call.summary["usage"]["claude-opus-5-5"]["input_tokens"] == 180
    assert call.summary["usage"]["claude-opus-5-5"]["requests"] == 1


def test_judge_client_failure_releases_budget_reservation(monkeypatch):
    def fail(**kwargs):
        raise RuntimeError("Client initialization failed.")

    monkeypatch.setattr(evaluate.anthropic, "Anthropic", fail)
    with model_budget(1) as budget:
        with pytest.raises(RuntimeError, match="initialization"):
            evaluate.judge_provider_request(
                model="claude-opus-5-5",
                system="Judge",
                messages=[],
                tools=[],
                max_tokens=100,
                purpose="evaluation-judge",
            )
        assert budget.snapshot()["reserved_usd"] == 0
        assert budget.snapshot()["stopped_reason"]


@pytest.fixture
def fake_prediction(monkeypatch, tmp_path):
    calls = []

    class FakeAgent:
        def __init__(self, corpus, config):
            self.config = config

        def run(self, prompt, session, *, eval_attributes):
            calls.append((prompt, eval_attributes, self.config.verify_mode))
            output = answer(self.config.verify_mode)
            output["metrics"] = summarize([metered_call("planner")], [])
            return output

    monkeypatch.setattr(evaluate, "Agent", FakeAgent)
    monkeypatch.setattr(evaluate, "Corpus", lambda: SimpleNamespace(snapshot_id="snapshot"))
    monkeypatch.setattr(evaluate, "settings", lambda: SimpleNamespace(project="test/test"))
    monkeypatch.setattr(evaluate, "source_fingerprint", lambda: "source")
    monkeypatch.setattr(evaluate, "RUN_DIRECTORY", tmp_path)
    monkeypatch.setattr(
        evaluate,
        "evaluation_call_ids",
        lambda: {
            "evaluation_call_id": "evaluation-call",
            "predict_and_score_call_id": "score-call",
            "predict_call_id": "predict-call",
        },
    )
    return calls


def test_prediction_attempts_have_unique_ids_real_parent_metadata_and_all_turn_usage(
    fake_prediction, tmp_path
):
    model = evaluate.DocumentationModel(
        agent_model="fake", snapshot_id="snapshot", source_sha256="source", verify_mode="off"
    )
    first = asyncio.run(model.predict(["First", "Follow-up"], "case-a", 2, "case-a:trial:2"))
    second = asyncio.run(model.predict(["First", "Follow-up"], "case-a", 2, "case-a:trial:2"))
    assert first["prediction_id"] != second["prediction_id"]
    assert first["agent_metrics"]["model_calls"] == 2
    assert len(list((tmp_path / "predictions").glob("*.json"))) == 2
    attrs = fake_prediction[0][1]
    assert attrs["weave.eval.run_id"] == "evaluation-call"
    assert attrs["weave.eval.predict_and_score_call_id"] == "score-call"
    assert attrs["weave.eval.trial_index"] == 1
    assert attrs["weave.eval.example_id"] == "case-a:trial:2"


def test_source_change_preserves_already_produced_turn(fake_prediction, monkeypatch, tmp_path):
    hashes = iter(["source", "changed"])
    monkeypatch.setattr(evaluate, "source_fingerprint", lambda: next(hashes))
    model = evaluate.DocumentationModel(
        agent_model="fake", snapshot_id="snapshot", source_sha256="source"
    )
    with pytest.raises(ValueError, match="changed during"):
        asyncio.run(model.predict(["First", "Follow-up"], "case-a"))
    assert len(list((tmp_path / "turns/1").glob("*.json"))) == 1
    failures = [
        json.loads(path.read_text()) for path in (tmp_path / "prediction-errors").glob("*.json")
    ]
    assert len(failures) == 1 and failures[0]["agent_metrics"]["model_calls"] == 1


def test_actual_call_id_lookup_uses_stack_names(monkeypatch):
    stack = [
        SimpleNamespace(func_name="Evaluation.evaluate", id="eval"),
        SimpleNamespace(func_name="Evaluation.predict_and_score", id="pair"),
        SimpleNamespace(func_name="DocumentationModel.predict", id="prediction"),
    ]
    monkeypatch.setattr(evaluate, "call_context", SimpleNamespace(get_call_stack=lambda: stack))
    assert evaluate.evaluation_call_ids() == {
        "evaluation_call_id": "eval",
        "predict_and_score_call_id": "pair",
        "predict_call_id": "prediction",
    }


def test_dataset_rejects_missing_assertions_and_unknown_selected_ids(monkeypatch, tmp_path):
    (tmp_path / "evals").mkdir()
    case = {
        "id": "a",
        "category": "basic",
        "prompts": ["Question"],
        "references": [],
        "expected_behavior": "Answer",
        "minimum_pages": 0,
        "require_code": False,
    }
    (tmp_path / "evals/cases.json").write_text(json.dumps([case]))
    monkeypatch.setattr(evaluate, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="Missing frozen assertions"):
        evaluate.dataset_rows(None)
    with pytest.raises(ValueError, match="Unknown case"):
        evaluate.dataset_rows(None, ["absent"])


def test_run_returns_summary_and_preserves_unscored_prediction_on_failure(monkeypatch, tmp_path):
    (tmp_path / "evals").mkdir()
    (tmp_path / "evals/cases.json").write_text("[]")
    monkeypatch.setattr(evaluate, "ROOT", tmp_path)
    monkeypatch.setattr(
        evaluate,
        "settings",
        lambda: SimpleNamespace(
            project="test/test",
            agent_model="claude-sonnet-5-5",
            judge_model="claude-opus-5-5",
            cache_enabled=True,
        ),
    )
    monkeypatch.setattr(evaluate, "Corpus", lambda: SimpleNamespace(snapshot_id="snapshot"))
    monkeypatch.setattr(evaluate, "source_fingerprint", lambda: "source")
    monkeypatch.setattr(evaluate.subprocess, "check_output", lambda *a, **kw: "commit")
    monkeypatch.setattr(
        evaluate, "dataset_rows", lambda *a: [{"case_id": "a", "assertions": ASSERTIONS}]
    )
    monkeypatch.setattr(evaluate, "init_weave", lambda: SimpleNamespace(flush=lambda: None))
    monkeypatch.setattr(evaluate.weave, "Dataset", lambda **kw: SimpleNamespace(**kw))
    monkeypatch.setattr(
        evaluate.weave, "publish", lambda dataset: SimpleNamespace(uri=lambda: "weave://dataset")
    )

    class BrokenEvaluation:
        def __init__(self, **kwargs):
            assert kwargs["trials"] == 1
            self.evaluate = SimpleNamespace(call=self.run)

        async def run(self, evaluation, model):
            prediction = {
                "case_id": "a",
                "prediction_id": str(uuid.uuid4()),
                "example_id": "a:trial:1",
                "verify_mode": "off",
                "agent_metrics": summarize([metered_call("planner")], []),
            }
            evaluate.persist_record(evaluate.RUN_DIRECTORY, "predictions", prediction, prediction)
            raise ConnectionError("Transport failed after a prediction.")

    monkeypatch.setattr(evaluate.weave, "Evaluation", BrokenEvaluation)
    args = SimpleNamespace(
        only=None, name="partial", suite="regression", verify_mode="off", trials=1, budget_usd=1
    )
    result = asyncio.run(evaluate.run_evaluation(args))
    assert result["run_error"] == "ConnectionError" and result["status"] == "partial"
    assert result["predictions_recorded"] == 1 and result["completed_cases"] == 0
    assert result["usage"]["agent"]["model_calls"] == 1
    assert result["missing_example_ids"] == ["a:trial:1"]
    assert (tmp_path / "results/partial/summary.json").exists()
    with pytest.raises(FileExistsError):
        asyncio.run(evaluate.run_evaluation(args))
