"""Offline runner contracts: synthetic references and fake live dependencies only."""

import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def runner(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root))
    spec = importlib.util.spec_from_file_location(
        "retrieval_compare_test", root / "scripts/experiments/retrieval_compare.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reference_case(*groups):
    return {
        "nuggets": [
            {
                "id": str(index),
                "acceptable_passages": [
                    {"page_id": page, "section": section} for page, section in references
                ],
            }
            for index, references in enumerate(groups)
        ]
    }


def hits(*identities):
    return [{"page_id": page, "section": section} for page, section in identities]


def test_metrics_count_nuggets_not_hits(runner):
    case = reference_case([("a", 0), ("b", 2)], [("b", 2)])
    metrics = runner.nugget_metrics(case, hits(("irrelevant", 0), ("b", 2), ("a", 0), ("b", 2)))
    assert metrics == {
        "covered": ["0", "1"],
        "nugget_recall": 1,
        "all_nuggets": True,
        "first_relevant_rank": 2,
        "reciprocal_rank": 0.5,
    }
    empty = runner.nugget_metrics(case, [])
    assert empty["nugget_recall"] == empty["reciprocal_rank"] == 0
    assert empty["first_relevant_rank"] is None
    assert not empty["all_nuggets"]


@pytest.mark.parametrize(
    "groups,k,expected",
    [
        ([[("a", 0)], [("a", 1)], [("a", 2)]], 6, 2 / 3),
        ([[("a", 0)], [("a", 1)], [("a", 2), ("b", 0)]], 6, 1),
        ([[("a", 0)], [("b", 0)], [("c", 0)]], 2, 2 / 3),
        ([[("a", 0)], [("a", 0)], [("b", 0)]], 1, 2 / 3),
    ],
)
def test_exact_ceiling_respects_page_cap_alternatives_and_shared_support(
    runner, groups, k, expected
):
    assert runner.ceiling(reference_case(*groups), k) == expected


def test_selection_uses_sorted_ids_and_distinct_information_needs(runner):
    rows = []
    for category, prefix, groups in [
        ("plain_language", "p", ["a", "b", "c"]),
        ("exact_api", "e", ["a", "b", "c", "d"]),
        ("workflow", "w", ["c", "d", "e", "f"]),
    ]:
        rows.extend(
            {"id": prefix + str(i), "category": category, "group_id": group}
            for i, group in enumerate(groups)
        )
    selected = runner.selected_cases({"cases": list(reversed(rows))})
    assert [row["id"] for row in selected] == ["p0", "p1", "e2", "e3", "w2", "w3"]


@pytest.fixture
def fake_live(runner, monkeypatch, tmp_path):
    # Import the real modules before replacing the SDK entry points. No init or
    # provider methods are called; only the experiment's actual live() is exercised.
    from coreweaving import agent, config, evaluate

    state = SimpleNamespace(
        agent_calls=[], judge_calls=[], errors=[], sessions=[], scenario="success", changed=False
    )
    results = tmp_path / "results"
    results.mkdir()
    probe = tmp_path / "probe.json"
    probe.write_text("{}")
    backend = tmp_path / "backend.py"
    backend.write_text("# immutable test backend\n")
    (results / "protocol.md").write_text("synthetic protocol")
    cases = [
        {
            "id": f"{category}-{i}",
            "category": category,
            "group_id": f"{category}-{i}",
            "query": f"synthetic question {category} {i}",
            "nuggets": [{"acceptable_passages": [{"page_id": "fake", "section": 0}]}],
            "assertions": [{"id": "a1", "description": "synthetic expected behavior"}],
        }
        for category in ("plain_language", "exact_api", "workflow")
        for i in range(2)
    ]
    manifest = {
        "dataset_sha256": runner.sha(probe),
        "backend_sha256": runner.sha(backend),
        "source_sha256": "source",
        "runner_sha256": runner.sha(runner.__file__),
        "protocol_sha256": runner.sha(results / "protocol.md"),
    }
    offline = {
        "manifest": manifest,
        "selected_candidate": "contextual",
        "arms": {mode: {"identity": {"mode": mode}} for mode in ("baseline", "contextual")},
    }
    (results / "offline.json").write_text(json.dumps(offline))
    monkeypatch.setattr(runner, "RESULTS", results)
    monkeypatch.setattr(runner, "DATA", probe)
    monkeypatch.setattr(runner, "BACKEND", backend)
    monkeypatch.setattr(
        runner, "source_fingerprint", lambda: "changed" if state.changed else "source"
    )
    monkeypatch.setattr(runner, "load_probe", lambda: {"cases": cases})
    monkeypatch.setattr(
        runner,
        "build",
        lambda mode, model_dir: (
            SimpleNamespace(
                identity={"mode": mode},
                read=lambda *args: SimpleNamespace(
                    evidence=lambda source_id: {"source_id": source_id}
                ),
            ),
            0,
        ),
    )
    monkeypatch.setattr(
        config,
        "settings",
        lambda: SimpleNamespace(
            verify_mode="support", agent_model="fake", judge_model="fake", cache_enabled=True
        ),
    )
    monkeypatch.setattr(config, "init_weave", lambda: SimpleNamespace(flush=lambda: None))
    monkeypatch.setattr(evaluate, "RUN_DIRECTORY", None)
    monkeypatch.setattr(evaluate, "evaluation_call_ids", lambda: {})
    original_persist = evaluate.persist_record

    def persist(directory, area, output, record):
        if state.scenario == "persistence_error" and area == "predictions":
            raise OSError("synthetic disk failure")
        original_persist(directory, area, output, record)

    monkeypatch.setattr(evaluate, "persist_record", persist)

    class FakeAgent:
        def __init__(self, corpus, config):
            self.mode = corpus.identity["mode"]

        def run(self, question, session, *, eval_attributes):
            state.agent_calls.append((question, self.mode))
            state.sessions.append(session)
            if state.scenario == "agent_exception":
                raise RuntimeError("synthetic agent failure")
            if state.scenario == "source_changed":
                state.changed = True
            if state.scenario == "backend_changed":
                backend.write_text("# changed during the turn\n")
            return {
                "answer": "synthetic answer",
                "metrics": {},
                "kind": "error" if state.scenario == "agent_error_return" else "answer",
                "error_type": "SyntheticError" if state.scenario == "agent_error_return" else None,
            }

    class FakeObject:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class FakeJudge(FakeObject):
        async def score(self, output, *args):
            state.judge_calls.append(output["case_id"])
            if state.scenario == "judge_exception":
                raise ValueError("synthetic scorer failure")
            scores = {
                "judge_error": "InvalidVerdict" if state.scenario == "judge_error_return" else None
            }
            persist(evaluate.RUN_DIRECTORY, "cases", output, {"scores": scores})
            return scores

    class FakeEvaluation(FakeObject):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.evaluate = SimpleNamespace(call=self.run)

        async def run(self, evaluation, model):
            # The installed SDK catches prediction/scorer exceptions and advances
            # to later rows. Simulate that behavior to test the shared halt gate.
            for row in self.dataset.rows:
                try:
                    output = await model.predict(
                        prompts=row["prompts"],
                        case_id=row["case_id"],
                        question_id=row["question_id"],
                        retrieval_mode=row["retrieval_mode"],
                    )
                    await self.scorers[0].score(
                        output,
                        row["prompts"],
                        row["expected_behavior"],
                        row["reference_evidence"],
                        0,
                        False,
                        row["assertions"],
                    )
                except Exception as exc:
                    state.errors.append(type(exc).__name__)
            return {}, SimpleNamespace(id="fake-evaluation", ui_url="https://example.invalid/eval")

    monkeypatch.setattr(agent, "Agent", FakeAgent)
    monkeypatch.setattr(agent, "Session", object)
    monkeypatch.setattr(evaluate, "QualityJudge", FakeJudge)
    monkeypatch.setitem(
        sys.modules,
        "weave",
        SimpleNamespace(
            Model=FakeObject,
            Dataset=FakeObject,
            Evaluation=FakeEvaluation,
            op=lambda **kwargs: lambda function: function,
        ),
    )
    return state, results


@pytest.mark.parametrize(
    "scenario,expected_judges",
    [
        ("agent_exception", 0),
        ("agent_error_return", 0),
        ("persistence_error", 0),
        ("source_changed", 0),
        ("backend_changed", 0),
        ("judge_exception", 1),
        ("judge_error_return", 1),
    ],
)
def test_operational_failure_withholds_every_later_paid_cell(
    runner, fake_live, scenario, expected_judges
):
    state, results = fake_live
    state.scenario = scenario
    asyncio.run(runner.live(SimpleNamespace(model_dir=Path("unused"))))
    assert len(state.agent_calls) == 1
    assert len(state.judge_calls) == expected_judges
    summary = json.loads((results / "live/summary.json").read_text())
    assert summary["status"] == "incomplete"
    assert summary["halted"]
    if scenario in {"agent_error_return", "source_changed", "backend_changed"}:
        assert len(list((results / "live/predictions").glob("*.json"))) == 1


def test_success_preserves_paired_order_and_fresh_sessions(runner, fake_live):
    state, results = fake_live
    asyncio.run(runner.live(SimpleNamespace(model_dir=Path("unused"))))
    assert len(state.agent_calls) == len(state.judge_calls) == 12
    assert len({id(session) for session in state.sessions}) == 12
    for index in range(6):
        pair = state.agent_calls[index * 2 : index * 2 + 2]
        assert pair[0][0] == pair[1][0]
        assert [mode for _, mode in pair] == (
            ["baseline", "contextual"] if index % 2 == 0 else ["contextual", "baseline"]
        )
    summary = json.loads((results / "live/summary.json").read_text())
    assert summary["status"] == "complete"
    assert not summary["halted"]
