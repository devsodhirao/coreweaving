"""One labelled synthetic Evaluation; deterministic Python, zero provider calls.

prepare freezes identity/checks before writes; emit runs once; read only reads
its saved IDs. Existing receipts are never overwritten and no calls are replayed.
"""

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import weave
from weave.trace_server_bindings.remote_http_trace_server import RemoteHTTPTraceServer

from coreweaving.config import init_weave, settings, source_fingerprint
from coreweaving.telemetry import restore_trace_value

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[1]
LABEL = "Synthetic fixture only: "
LITERAL = "Synthetic deterministic answer."
EXECUTIONS = []


def plain(value):
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json", by_alias=True)
    if isinstance(value, dict):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(item) for item in value]
    return value


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as handle:
        handle.write(json.dumps(value, indent=2) + "\n")


def record(kind):
    call = weave.get_current_call()
    EXECUTIONS.append({"kind": kind, "call_id": call.id, "parent_id": call.parent_id})


@weave.op()
def literal_fixture_echo(question: str) -> str:
    record("literal_echo")
    assert question == LITERAL
    return question


class LiteralIndexFixtureModel(weave.Model):
    @weave.op()
    def predict(self, question: str) -> str:
        record("predict")
        assert question == LABEL + LITERAL
        return literal_fixture_echo(question[len(LABEL) :])


@weave.op()
def literal_fixture_exact(output: str, question: str) -> dict:
    record("score")
    return {"exact": output == question[len(LABEL) :] == LITERAL}


def prepare():
    cfg = settings()
    protocol = {
        "prepared_at": datetime.now(UTC).isoformat(),
        "fixture_id": str(uuid.uuid4()),
        "runtime_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        "source_sha256": source_fingerprint(),
        "script_sha256": sha(Path(__file__)),
        "project": cfg.project,
        "weave_version": weave.__version__,
        "scope": "One synthetic dataset row, deterministic echo Model and deterministic exact-match scorer via real init_weave. Zero provider calls or Agent events. All names exclude the coreweaving agent filter. No real user input, retries, telemetry replay or historical evidence repair.",
        "dataset_row": {"question": LABEL + LITERAL},
        "literal_question_and_output": LITERAL,
        "fixture_variant": "ordinary prose index control; preserves failed v1",
        "table_boundary": "This v2 uses ordinary prose throughout. Failed v1 remains preserved: raw ref-shaped outputs encounter SDK scorer logged-output semantics and EvaluationResults table parsing outside call codecs. v2 isolates dataset-row reference preservation and complete evaluation indexing, without claiming raw-URI table support.",
        "expected": {
            "indexed_rows": 1,
            "model_invocations": 1,
            "echo_invocations": 1,
            "scorer_invocations": 1,
            "provider_calls": 0,
            "exact_score": {"exact": True},
            "dataset_row_ref_preserved": True,
            "call_parentage_and_literal_roundtrip": True,
        },
    }
    save(OUT / "protocol.json", protocol)
    print(
        json.dumps(
            {
                "prepared": "protocol.json",
                "protocol_sha256": sha(OUT / "protocol.json"),
                "source_sha256": protocol["source_sha256"],
            },
            indent=2,
        )
    )


async def emit():
    protocol = read(OUT / "protocol.json")
    assert protocol["source_sha256"] == source_fingerprint()
    assert protocol["script_sha256"] == sha(Path(__file__))
    assert not (OUT / "emission-started.json").exists()
    save(
        OUT / "emission-started.json",
        {
            "started_at": datetime.now(UTC).isoformat(),
            "protocol_sha256": sha(OUT / "protocol.json"),
        },
    )
    receipt = {
        "fixture_id": protocol["fixture_id"],
        "source_sha256": protocol["source_sha256"],
        "protocol_sha256": sha(OUT / "protocol.json"),
        "provider_calls": 0,
        "agent_events": 0,
        "executions": EXECUTIONS,
    }
    try:
        client = init_weave()
        name = "ordinary-index-fixture-" + protocol["fixture_id"][:8]
        dataset = weave.Dataset(name=name + "-dataset", rows=[protocol["dataset_row"]])
        reference = weave.publish(dataset)
        evaluation = weave.Evaluation(
            name=name,
            evaluation_name=name,
            dataset=dataset,
            scorers=[literal_fixture_exact],
            trials=1,
            metadata={
                "synthetic_no_provider_calls": True,
                "source_sha256": protocol["source_sha256"],
                "protocol_sha256": receipt["protocol_sha256"],
            },
        )
        model = LiteralIndexFixtureModel(name=name + "-model")
        result, call = await evaluation.evaluate.call(evaluation, model)
        receipt.update(
            evaluation_call_id=call.id,
            dataset_ref=reference.uri(),
            summary=plain(result),
            evaluation_url=call.ui_url,
            status="executed",
        )
        started = time.monotonic()
        client.flush()
        receipt.update(
            flush_status="returned",
            flush_seconds=round(time.monotonic() - started, 3),
            source_still_matches=source_fingerprint() == protocol["source_sha256"],
        )
    except Exception as exc:
        receipt.update(status="failed", error_type=type(exc).__name__)
        raise
    finally:
        receipt["completed_at"] = datetime.now(UTC).isoformat()
        save(OUT / "execution.json", receipt)
        print(json.dumps(receipt, indent=2), flush=True)


def readback():
    protocol, execution = read(OUT / "protocol.json"), read(OUT / "execution.json")
    assert not (OUT / "backend-readback.json").exists()
    cfg = settings()
    assert cfg.project == protocol["project"]
    server = RemoteHTTPTraceServer.from_env(should_batch=False)
    server.set_auth(("api", os.environ["WANDB_API_KEY"]))
    call_id = execution["evaluation_call_id"]
    rows = plain(
        server.eval_results_query(
            {
                "project_id": cfg.project,
                "evaluation_call_ids": [call_id],
                "include_rows": True,
                "include_summary": True,
                "include_raw_data_rows": False,
                "include_predict_and_score_children": True,
                "limit": 2,
                "offset": 0,
            }
        )
    )
    trials = [
        trial
        for row in rows.get("rows", [])
        for entry in row["evaluations"]
        if entry["evaluation_call_id"] == call_id
        for trial in entry["trials"]
    ]
    trial = trials[0] if len(trials) == 1 else {}
    recorded = {entry["kind"]: entry for entry in execution["executions"]}
    pas_id = recorded["predict"]["parent_id"]
    ids = list(
        dict.fromkeys([call_id, pas_id, *(entry["call_id"] for entry in execution["executions"])])
    )
    calls = plain(
        server.calls_query(
            {
                "project_id": cfg.project,
                "filter": {"call_ids": ids},
                "limit": 6,
                "columns": [
                    "id",
                    "parent_id",
                    "op_name",
                    "ended_at",
                    "exception",
                    "inputs",
                    "output",
                ],
            }
        ).calls
    )
    by_id = {call["id"]: call for call in calls}
    parent, pas, predict, echo, score = [
        by_id.get(i, {})
        for i in [
            call_id,
            pas_id,
            recorded["predict"]["call_id"],
            recorded["literal_echo"]["call_id"],
            recorded["score"]["call_id"],
        ]
    ]
    example_ref = (pas.get("inputs") or {}).get("example")
    scalar_row_output = restore_trace_value(trial.get("model_output"))
    score_key = "literal_fixture_exact"
    checks = {
        "one_indexed_row_and_trial": rows.get("total_rows")
        == len(rows.get("rows", []))
        == len(trials)
        == 1,
        "all_five_calls_present_and_completed": len(calls) == len(ids) == 5
        and all(call.get("ended_at") and not call.get("exception") for call in calls),
        "dataset_row_reference_preserved": isinstance(example_ref, str)
        and example_ref.startswith(execution["dataset_ref"] + "/attr/rows/id/"),
        "indexed_predict_and_score_matches": trial.get("predict_and_score_call_id") == pas_id,
        "indexed_predict_matches": trial.get("predict_call_id") == recorded["predict"]["call_id"],
        "indexed_scorer_matches": (trial.get("scorer_call_ids") or {}).get(score_key)
        == recorded["score"]["call_id"],
        "indexed_output_literal_roundtrip": scalar_row_output == LITERAL,
        "indexed_score_matches": restore_trace_value((trial.get("scores") or {}).get(score_key))
        == {"exact": True},
        "echo_input_literal_roundtrip": restore_trace_value(
            (echo.get("inputs") or {}).get("question")
        )
        == LITERAL,
        "echo_output_literal_roundtrip": restore_trace_value(echo.get("output")) == LITERAL,
        "predict_output_literal_roundtrip": restore_trace_value(predict.get("output")) == LITERAL,
        "scorer_received_original_literal": restore_trace_value(
            (score.get("inputs") or {}).get("output")
        )
        == LITERAL,
        "scorer_output_exact": restore_trace_value(score.get("output")) == {"exact": True},
        "parent_summary_matches": restore_trace_value(parent.get("output")) == execution["summary"],
        "parentage": pas.get("parent_id") == call_id
        and predict.get("parent_id") == pas_id
        and echo.get("parent_id") == predict.get("id")
        and score.get("parent_id") == pas_id,
        "one_each_deterministic_execution": len(execution["executions"]) == len(recorded) == 3,
    }
    receipt = {
        "checked_at": datetime.now(UTC).isoformat(),
        "status": "verified" if all(checks.values()) else "unverified",
        "fixture_id": protocol["fixture_id"],
        "runtime_commit": protocol["runtime_commit"],
        "source_sha256": protocol["source_sha256"],
        "protocol_sha256": sha(OUT / "protocol.json"),
        "execution_sha256": sha(OUT / "execution.json"),
        "scope": "Two read-only queries: one indexed evaluation query, one exact-ID call query. Zero provider calls, Agent events, retries, mutations or replay.",
        "evaluation_call_id": call_id,
        "evaluation_url": execution["evaluation_url"],
        "indexed_rows": rows.get("total_rows"),
        "dataset_row_ref": example_ref,
        "checks": checks,
        "calls": [
            {key: call.get(key) for key in ["id", "parent_id", "op_name", "ended_at"]}
            for call in calls
        ],
        "limitations": [
            "One synthetic transport/indexing check, not an answer-quality experiment.",
            "Raw ref-shaped table/output support is not tested; failed v1 and protocol document that limitation.",
            "Historical evaluation records were not modified or replayed.",
        ],
    }
    save(OUT / "backend-readback.json", receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "emit", "read"])
    mode = parser.parse_args().mode
    if mode == "prepare":
        prepare()
    elif mode == "emit":
        asyncio.run(emit())
    else:
        readback()
