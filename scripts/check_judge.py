"""Check that the judge rejects a false claim even with valid-looking evidence metadata."""

import asyncio
import copy
import json

from coreweaving.config import ROOT, init_weave, settings
from coreweaving.corpus import Corpus
from coreweaving.evaluate import QualityJudge, dataset_rows


async def main():
    client = init_weave()
    original = json.loads((ROOT / "results/baseline-v1/cases/01-init.json").read_text())["output"]
    row = dataset_rows(Corpus(), ["01-init"])[0]
    invented = copy.deepcopy(original)
    citation = next(source["source_id"] for source in invented["sources"] if "page_id" in source)
    invented["answer"] = (
        'Call weave.init("team/project", hallucination_free=True). This guarantees that your '
        f"agent can never produce a wrong answer, with 100% correctness. [{citation}]"
    )
    invented["turns"][-1]["answer"] = invented["answer"]
    # Keep a passing verifier flag and a real source ID intentionally. The judge
    # must assess semantic support instead of trusting either superficial signal.
    judge = QualityJudge(name="judge-calibration", judge_model=settings().judge_model)
    results = []
    for name, output, expected in [
        ("recorded-answer", original, True),
        ("fabricated-guarantee", invented, False),
    ]:
        score = await judge.score(
            output=output,
            prompts=row["prompts"],
            expected_behavior=row["expected_behavior"],
            reference_evidence=row["reference_evidence"],
            minimum_pages=row["minimum_pages"],
            require_code=False,
        )
        results.append(
            {
                "fixture": name,
                "synthetic": name == "fabricated-guarantee",
                "expected_pass": expected,
                "observed_pass": score["passed"],
                "matched_expectation": score["passed"] == expected,
                "answer": output["answer"],
                "scores": score,
            }
        )
    receipt = {
        "purpose": "Judge calibration; separate from the agent evaluation dataset.",
        "all_matched": all(r["matched_expectation"] for r in results),
        "cases": results,
    }
    (ROOT / "results/judge-calibration.json").write_text(json.dumps(receipt, indent=2) + "\n")
    client.flush()
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
