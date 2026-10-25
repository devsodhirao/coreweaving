"""Recover a completed evaluation whose eager parent-call end was not ingested.

This reuses the original call ID, original start fields, recorded end timestamp,
and actual summary. It does not rerun the model or manufacture scores.
"""

import argparse
import json
from datetime import UTC, datetime

from coreweaving.config import ROOT, init_weave, settings
from coreweaving.evaluate import sync_completed_evaluation


def repair(run_name: str) -> dict:
    client = init_weave()
    path = ROOT / "results" / run_name / "summary.json"
    result = json.loads(path.read_text())
    call_id = result["evaluation_call_id"]
    delivery = sync_completed_evaluation(client, settings().project, result)
    result["remote_sync"] = delivery
    path.write_text(json.dumps(result, indent=2) + "\n")
    receipt = {
        "call_id": call_id,
        "recovered_at": datetime.now(UTC).isoformat(),
        "method": "Replay original completed record through calls_complete",
        "verified": delivery["verified"],
        "original_ended_at": result["evaluation_ended_at"],
    }
    (path.parent / "remote-recovery.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", help="Name under results/ containing a saved completion timestamp.")
    repair(parser.parse_args().run)
