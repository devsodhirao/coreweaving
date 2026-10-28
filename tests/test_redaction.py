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


@pytest.mark.parametrize(
    "value,secret",
    [
        ('password="synthetic alpha beta"', "alpha beta"),
        ("password='synthetic alpha beta'", "alpha beta"),
        ('"client_secret": "synthetic alpha beta"', "alpha beta"),
        ('password="synthetic \\"quoted\\" value"', "value"),
        ("Authorization: Basic c3ludGhldGljOm9ubHk=", "c3ludGhldGljOm9ubHk="),
        ('"Authorization": "Basic c3ludGhldGljOm9ubHk="', "c3ludGhldGljOm9ubHk="),
        ("Authorization: Bearer synthetic-credential", "synthetic-credential"),
        ('Authorization: "Bearer synthetic credential"', "synthetic credential"),
    ],
)
def test_complete_labelled_credential_values_are_masked(value, secret):
    masked = redact_sensitive(value)
    assert secret not in masked
    assert REDACTED in masked
    assert redact_sensitive(masked) == masked


@pytest.mark.parametrize(
    "value",
    [
        'password="synthetic alpha beta',
        "password='synthetic alpha beta",
        'password="synthetic \\"partial quote',
        'password="synthetic trailing \\"',
        "Authorization: 'Basic synthetic credential",
        'client_secret="synthetic trailing slash\\',
    ],
)
def test_incomplete_quoted_credentials_are_masked_through_end_of_line(value):
    masked = redact_sensitive(value + '\nAn "ordinary" next line.')
    assert "synthetic" not in masked
    assert REDACTED in masked
    assert masked.endswith('\nAn "ordinary" next line.')
    assert redact_sensitive(masked) == masked


@pytest.mark.parametrize(
    "value",
    [
        'api_key="YOUR_API_KEY"',
        'api_key="<your-api-key>"',
        'api_key="${ANTHROPIC_API_KEY}"',
        "api_key=${ANTHROPIC_API_KEY}",
        "Authorization: Bearer <TOKEN>",
        "Authorization: Basic <CREDENTIALS>",
        "Authorization: Bearer token",
        "Authorization: Basic authentication",
        "Select the **Bearer token secret name**.",
    ],
)
def test_credential_placeholders_and_authentication_prose_stay_readable(value):
    assert redact_sensitive(value) == value
