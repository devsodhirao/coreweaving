import json
from collections import namedtuple

import pytest
from weave.trace.vals import WeaveDict, WeaveList

from coreweaving.config import REDACTED, redact_sensitive


@pytest.mark.parametrize(
    "value",
    [
        "sk-ant-" + "x" * 30,
        "agt_" + "x" * 30,
        "wandb_v1_" + "x" * 30,
        "WANDB_API_KEY=" + "a" * 40,
        '"api_key": "legacy-secret-value"',
        "Authorization: Bearer synthetic-secret-value",
        "password=examplepassword",
        "-----BEGIN PRIVATE KEY-----\nsynthetic material\n-----END PRIVATE KEY-----",
    ],
)
def test_credentials_are_masked_idempotently(value):
    masked = redact_sensitive(value)
    assert masked != value and REDACTED in masked
    assert redact_sensitive(masked) == masked


def test_nested_structures_preserve_shape_and_safe_hashes(monkeypatch):
    secret = "synthetic-runtime-secret"
    monkeypatch.setenv("WANDB_API_KEY", secret)
    payload = ({"history": [secret], "token": secret, "commit": "a" * 40}, secret)
    result = redact_sensitive(payload)
    assert isinstance(result, tuple)
    assert secret not in json.dumps(result)
    assert result[0]["commit"] == "a" * 40
    assert payload[1] == secret


def test_weave_containers_are_redacted_without_reconstructing_trace_wrappers(monkeypatch):
    secret = "synthetic-runtime-secret"
    monkeypatch.setenv("WANDB_API_KEY", secret)
    payload = (
        WeaveDict(
            {"prompts": WeaveList([secret, "ordinary question"], server=None), "token": secret},
            server=None,
        ),
    )
    result = redact_sensitive(payload)
    assert type(result) is tuple
    assert type(result[0]) is dict
    assert type(result[0]["prompts"]) is list
    assert result == ({"prompts": [REDACTED, "ordinary question"], "token": REDACTED},)
    assert redact_sensitive(result) == result
    assert payload[0]["prompts"][0] == secret and payload[0]["token"] == secret


def test_tuple_subclasses_normalize_without_calling_their_constructor():
    pair = namedtuple("Pair", ["question", "credential"])
    secret = "sk-ant-" + "x" * 30
    payload = pair("ordinary question", secret)
    result = redact_sensitive(payload)
    assert type(result) is tuple and result == ("ordinary question", REDACTED)
    assert redact_sensitive(result) == result
    assert payload.credential == secret


def test_deep_or_cyclic_data_fails_without_echoing_input():
    value = []
    value.append(value)
    with pytest.raises(ValueError, match="depth limit"):
        redact_sensitive(value)


def test_documented_bearer_token_label_is_not_a_credential():
    assert (
        redact_sensitive("Select the **Bearer token secret name**.")
        == "Select the **Bearer token secret name**."
    )
