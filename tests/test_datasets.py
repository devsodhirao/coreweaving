"""Validate the frozen evaluation inputs independently of model-generated answers."""

import hashlib
import json
import re

import pytest

from coreweaving.config import ROOT
from coreweaving.corpus import Corpus

# Rubric 2.3 changes only case03 grading expectations; questions and references stay frozen.
REGRESSION_SHA256 = "8a573923782d9dbf3876ffb5f117fea39c93f5ffa86a19147d9067d1b6d83a51"
REGRESSION_QUESTIONS_SHA256 = "b482982f25be6e699cef1e61c6788766be504be7e4c3bde7c8b72ee813a8cd19"
FAMILIES = {
    "non-jargon-paraphrase",
    "real-api-false-premise",
    "workflow-compatibility",
    "whole-workflow",
    "context-change",
    "obscure-real-api",
}


def load(name):
    return json.loads((ROOT / "evals" / name).read_text())


@pytest.fixture(scope="module")
def corpus():
    return Corpus()


def test_regression_v23_inputs_remain_byte_for_byte_frozen():
    assert hashlib.sha256((ROOT / "evals/cases.json").read_bytes()).hexdigest() == REGRESSION_SHA256


def test_regression_questions_and_references_match_original_suite():
    tasks = [{key: case[key] for key in ("id", "prompts", "references")} for case in load("cases.json")]
    assert hashlib.sha256(json.dumps(tasks, sort_keys=True).encode()).hexdigest() == REGRESSION_QUESTIONS_SHA256


def test_capability_suite_has_six_distinct_families_and_one_context_switch():
    cases = load("capability.json")
    assert len(cases) == 6
    assert len({case["id"] for case in cases}) == 6
    assert {case["family"] for case in cases} == FAMILIES
    for case in cases:
        expected_count = 2 if case["family"] == "context-change" else 1
        assert len(case["prompts"]) == expected_count
        assert all(isinstance(prompt, str) and prompt.strip() for prompt in case["prompts"])
        assert isinstance(case["require_code"], bool)
        assert type(case["minimum_pages"]) is int and case["minimum_pages"] >= 0
        assert case["expected_behavior"].strip()


def test_assertions_cover_both_suites_with_unique_stable_ids():
    regression = load("cases.json")
    mapping = load("regression-assertions.json")
    assert set(mapping) == {case["id"] for case in regression}
    assert len(mapping) == 13
    all_ids = []
    assertion_sets = list(mapping.values()) + [
        case["assertions"] for case in load("capability.json")
    ]
    for assertions in assertion_sets:
        assert 3 <= len(assertions) <= 6
        assert len({assertion["description"] for assertion in assertions}) == len(assertions)
        for assertion in assertions:
            assert set(assertion) == {"id", "description"}
            assert re.fullmatch(r"(?:cap|reg)-\d{2}-a\d+", assertion["id"])
            assert len(assertion["description"].strip()) > 20
            all_ids.append(assertion["id"])
    assert len(all_ids) == len(set(all_ids))


@pytest.mark.parametrize("filename", ["cases.json", "capability.json"])
def test_every_reference_section_exists_in_the_checked_corpus(filename, corpus):
    for case in load(filename):
        references = case["references"]
        assert references
        assert case["minimum_pages"] <= len({reference["page_id"] for reference in references})
        selected = set()
        for reference in references:
            assert reference["sections"]
            for section in reference["sections"]:
                assert type(section) is int and section >= 0
                identity = (reference["page_id"], section)
                assert identity not in selected
                selected.add(identity)
                passage = corpus.read(*identity)
                assert passage.text.strip() and passage.heading.strip()
                assert passage.url.startswith("https://")
                assert re.fullmatch(r"[a-f0-9]{64}", passage.page_sha256)


def test_questions_do_not_embed_answer_keys_or_scoring_metadata():
    """Check accidental metadata leakage; semantic fairness is reviewed separately."""
    mapping = load("regression-assertions.json")
    for case in load("cases.json") + load("capability.json"):
        prompts = "\n".join(case["prompts"])
        assertions = case.get("assertions", mapping.get(case["id"]))
        assert case["expected_behavior"] not in prompts
        assert not re.search(r"\[(?:S|C)\d+\]", prompts)
        for field in ("expected_behavior", "reference_evidence", "assertion_results"):
            assert field not in prompts
        for assertion in assertions:
            assert assertion["description"] not in prompts
            assert assertion["id"] not in prompts


def test_whole_workflow_references_tracing_evaluation_and_live_scoring(corpus):
    case = next(case for case in load("capability.json") if case["family"] == "whole-workflow")
    pages = {reference["page_id"] for reference in case["references"]}
    assert {
        "guides/tracking/trace-agents",
        "guides/core-types/evaluations",
        "guides/tracking/remote-scorer-signals",
    }.issubset(pages)
    assert "multi-tenant" in case["prompts"][0].lower()
    assert "prerequisites" in case["prompts"][0].lower()
    remote = next(
        reference
        for reference in case["references"]
        if reference["page_id"] == "guides/tracking/remote-scorer-signals"
    )
    support = "\n".join(
        corpus.read(remote["page_id"], section).text for section in remote["sections"]
    )
    assert "Enable remote scoring" in support
    assert "Allowed hosts" in support
    assert "asynchronous" in support
