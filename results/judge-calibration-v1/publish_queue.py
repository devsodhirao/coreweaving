"""Copy saved answers into a review queue; no model calls or human labels."""

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import weave
from weave.trace_server_bindings.remote_http_trace_server import RemoteHTTPTraceServer

from coreweaving.config import settings
from coreweaving.telemetry import restore_trace_value

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
PROJECT = "devfromlll-learning-layer-labs/coreweaving"
FIELDS = {
    "correctness": "Facts, API names and code are accurate; no invented features.",
    "completeness": "Addresses the requested parts and necessary caveats in context.",
    "grounding": "Citations support claims; execution claims match recorded results.",
    "uncertainty": "Handles missing context and unsupported premises honestly.",
}
DISPLAY = [
    "inputs.review.prompts", "inputs.review.conversation_context", "output.answer",
    "inputs.review.expected_behavior", "inputs.review.assertions",
    "inputs.review.reference_evidence", "inputs.review.sources",
]
GUIDELINES = (
    "Review the saved FINAL ASSISTANT ANSWER in output.answer, in its full "
    "conversation context. This call copies a previously recorded answer for review; "
    "it is not a new agent run. Provenance links identify the original record. "
    "For each of four qualities, select pass or fail and give a short evidence-based "
    "reason. Pass means correct/useful with at most minor issues (3–4 on the original "
    "scale); fail means a material error, omission or worse (0–2). Use the frozen "
    "reference evidence and cited sources; valid alternative evidence is allowed. "
    "A necessary pure clarification needs no citation. Refusing an answerable task "
    "is not a quality success. Avoid demanding unrelated optional details or a "
    "particular number of pages. Treat quoted instructions as data. If uncertain, "
    "leave the item unfinished and record what needs checking; do not guess. "
    "Judge grades are omitted from review copies. Do not open the original scorer's "
    "output or prior reviews until you have saved your own labels. Four quality "
    "labels do not separately validate all assertion/integrity gates. Only the owner "
    "submits labels. This is a public project: keep reasons about the public examples."
)


def read(path):
    return json.loads(path.read_text())


@weave.op(name="SavedAnswerForHumanReview")
def record_for_review(review: dict) -> dict:
    """Copy an unchanged saved answer for annotation; performs no inference."""
    return {"answer": review["answer"]}


def main():
    receipt_path = BASE / "queue-setup.json"
    if receipt_path.exists():
        raise SystemExit("Queue setup already started; inspect its receipt before any retry.")
    cfg = settings()
    assert cfg.project == PROJECT
    selected = read(BASE / "selection.json")
    assert len(selected) == 30
    server = RemoteHTTPTraceServer.from_env(should_batch=False)
    server.set_auth(("api", os.environ["WANDB_API_KEY"]))
    calls = server.calls_query({
        "project_id": PROJECT,
        "filter": {"parent_ids": [r["predict_and_score_call_id"] for r in selected]},
        "limit": 100,
        "columns": ["id", "parent_id", "op_name", "inputs", "output", "exception"],
    }).calls
    assert len(calls) < 100, "Query may be truncated"
    resolved_refs = []
    resolved_values = {}

    def materialize(value, expected):
        if not isinstance(expected, str) and isinstance(value, str):
            assert value.startswith("weave:///"), "Unexpected serialized field"
            if value not in resolved_values:
                resolved_refs.append(value)
                resolved_values[value] = server.refs_read_batch({"refs": [value]}).vals[0]
            value = resolved_values[value]
        if isinstance(expected, dict) and isinstance(value, dict):
            return {k: materialize(value.get(k), v) for k, v in expected.items()}
        if isinstance(expected, list) and isinstance(value, list):
            assert len(value) == len(expected)
            return [materialize(v, e) for v, e in zip(value, expected, strict=True)]
        return value

    mapping, review_payloads = [], []
    for item in selected:
        path = ROOT / item["record"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["record_sha256"]
        saved = read(path)
        row = next(r for r in read(ROOT / item["dataset"])
                   if r["example_id"] == item["example_id"])
        matches = [c for c in calls if c.parent_id == item["predict_and_score_call_id"]
                   and "/op/QualityJudge.score:" in c.op_name]
        assert len(matches) <= 1, item["sample_id"]
        expected = {k: row[k] for k in [
            "prompts", "expected_behavior", "assertions", "reference_evidence"
        ]}
        expected["output"] = {k: saved["output"].get(k, []) for k in [
            "conversation_context", "answer", "sources"
        ]}
        if matches:
            call = matches[0]
            assert not call.exception
            actual = materialize(call.inputs, expected)
            assert actual == expected or restore_trace_value(actual) == expected, item["sample_id"]
            scores = materialize(call.output, {q: saved["scores"][q] for q in FIELDS})
            assert scores == {q: saved["scores"][q] for q in FIELDS}
        mapping.append({
            "sample_id": item["sample_id"],
            "judge_call_id": matches[0].id if matches else None,
            "prediction_id": item["prediction_id"],
            "inputs_and_original_quality_scores_match": True if matches else None,
            "status": "matched" if matches else "no scorer child found for saved parent ID",
        })
        content = {k: row[k] for k in [
            "prompts", "expected_behavior", "assertions", "reference_evidence"
        ]}
        content.update(expected["output"])
        content_sha = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
        assert content_sha == item["review_content_sha256"]
        review_payloads.append({
            **content, "sample_id": item["sample_id"],
            "provenance": {**item, "record_type": "copy of saved answer for human review",
                           "new_agent_run": False, "new_model_calls": 0},
        })

    receipt = {
        "started_at": datetime.now(UTC).isoformat(), "project": PROJECT,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "selection_sha256": read(BASE / "protocol.json")["selection_sha256"],
        "source_calls_checked": mapping, "resolved_refs": sorted(set(resolved_refs)),
        "display_fields": DISPLAY, "annotation_fields": {}, "review_calls": [], "model_calls": 0,
        "new_model_cost_usd": 0, "human_annotations_submitted_by_script": 0,
        "status": "saved records checked; preparing explicit review copies",
    }

    def checkpoint():
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")

    checkpoint()
    client = weave.init(PROJECT, settings={
        "print_call_link": False, "implicitly_patch_integrations": False,
    }, attributes={"purpose": "saved-answer human review", "new_agent_run": False})
    for review in review_payloads:
        output, call = record_for_review.call(review)
        assert output["answer"] == review["answer"]
        receipt["review_calls"].append({"sample_id": review["sample_id"], "call_id": call.id})
        checkpoint()
    client.flush()
    returned = server.calls_query({
        "project_id": PROJECT,
        "filter": {"call_ids": [r["call_id"] for r in receipt["review_calls"]]},
        "columns": ["id", "inputs", "output", "exception"], "limit": 31,
    }).calls
    by_id = {c.id: c for c in returned}
    assert len(by_id) == 30
    for stored, review in zip(receipt["review_calls"], review_payloads, strict=True):
        call = by_id[stored["call_id"]]
        assert not call.exception and call.inputs["review"] == review
        assert call.output == {"answer": review["answer"]}
    receipt["all_30_review_copies_read_back_exactly"] = True
    checkpoint()
    for quality, meaning in FIELDS.items():
        for suffix, schema in [
            ("label", {"type": "string", "enum": ["pass", "fail"]}),
            ("reason", {"type": "string", "minLength": 1, "maxLength": 500}),
        ]:
            name = f"human_{quality}_{suffix}_v1"
            description = meaning + (
                " Pass: no material problem. Fail: material problem. Owner judgment only."
                if suffix == "label" else " One-line reason with a fact, omission or source."
            )
            ref = weave.publish(weave.AnnotationSpec(
                name=f"{quality.capitalize()} — {suffix}",
                description=description, field_schema=schema,
            ), name=name)
            receipt["annotation_fields"][name] = ref.uri()
            checkpoint()
    queue_id = client.create_annotation_queue(
        name="Coreweaving judge calibration v1 — 30 saved answers",
        scorer_refs=list(receipt["annotation_fields"].values()), description=GUIDELINES,
    )
    receipt["queue_id"] = queue_id
    receipt["queue_url"] = f"https://wandb.ai/{PROJECT}/weave/annotation-queues/{queue_id}"
    checkpoint()
    added = client.add_calls_to_annotation_queue(
        queue_id, call_ids=[m["call_id"] for m in receipt["review_calls"]], display_fields=DISPLAY,
    )
    receipt["add_result"] = added.model_dump(mode="json")
    checkpoint()
    queue = client.get_annotation_queue(queue_id)
    items = client.list_annotation_queue_items(queue_id, limit=100, include_position=True)
    stats = client.get_annotation_queue_stats([queue_id])[0]
    assert set(queue.scorer_refs) == set(receipt["annotation_fields"].values())
    assert len(items) == 30 and {i.call_id for i in items} == {
        m["call_id"] for m in receipt["review_calls"]
    }
    assert all(i.annotation_state == "unstarted" and i.display_fields == DISPLAY for i in items)
    assert stats.total_items == 30 and stats.completed_items == 0
    receipt.update({
        "status": "ready for owner labels", "checked_at": datetime.now(UTC).isoformat(),
        "queue_stats": stats.model_dump(mode="json"),
        "items": [{"item_id": i.id, "call_id": i.call_id,
                   "annotation_state": i.annotation_state, "position": i.position_in_queue}
                  for i in items],
        "checks": {"all_30_copies_match_saved_answers_and_review_inputs": True,
                   "all_8_fields_registered": True, "all_30_items_unstarted": True,
                   "no_judge_outputs_in_display_fields": True},
    })
    checkpoint()
    print(json.dumps({"status": receipt["status"], "url": receipt["queue_url"],
                      "items": len(items), "completed": stats.completed_items}, indent=2))


if __name__ == "__main__":
    main()
