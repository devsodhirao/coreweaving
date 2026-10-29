import ast
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


def python_fence(code):
    return f"```python\n{code}\n```"


def assert_python_syntax(markdown):
    from markdown_it import MarkdownIt

    for block in MarkdownIt("commonmark").parse(markdown):
        if block.type == "fence" and block.info.startswith("python"):
            ast.parse(block.content)


def test_real_documented_postprocess_example_keeps_its_code():
    from coreweaving.corpus import Corpus

    passage = Corpus().read("guides/tracking/ops", 3)
    assert "secret_password: str" in passage.text
    assert "secret_password=hide_me" in passage.text
    masked = redact_sensitive(passage.text)
    assert masked == passage.text
    assert_python_syntax(masked)


def test_python_annotations_and_credential_expressions_survive_at_every_text_sink():
    code = """import os
from dataclasses import dataclass

@dataclass
class Reply:
    secret_password: str

def login(password: str, api_key: str | None = None) -> Reply:
    headers = {"Authorization": f"Bearer {api_key}"}
    password = f"{password}"
    return Reply(secret_password=password)

api_key = os.environ["ANTHROPIC_API_KEY"]
login(password=password, api_key=os.getenv("ANTHROPIC_API_KEY"))
"""
    snippet = python_fence(code)
    payload = {"sources": [{"text": snippet}], "messages": [snippet], "answer": snippet}
    assert redact_sensitive(payload) == payload
    assert_python_syntax(snippet)


def test_python_empty_and_explicit_placeholder_defaults_are_not_credentials():
    code = """def login(password="", api_key=..., token=None, client_secret="<CLIENT_SECRET>"):
    pass
"""
    assert redact_sensitive(python_fence(code)) == python_fence(code)


@pytest.mark.parametrize(
    "code",
    [
        'password = "synthetic actual credential"',
        "password: str = 'synthetic actual credential'",
        'def login(password: str = "synthetic actual credential"): pass',
        'def login(*, client_secret="synthetic actual credential"): pass',
        'client = Client(api_key="synthetic actual credential")',
        'settings = {"password": "synthetic actual credential"}',
        'settings = {"Authorization": "Bearer synthetic actual credential"}',
        'obj.secret_password = "synthetic actual credential"',
        'if password := "synthetic actual credential": pass',
        'password = r"synthetic actual credential"',
        'password = b"synthetic actual credential"',
        'password = """synthetic actual\ncredential"""',
        'password = f"synthetic actual credential {suffix}"',
        '# password="synthetic actual credential"\nvalue = 1',
        'note = \'{"password": "synthetic actual credential"}\'',
        r'note = "{\"password\": \"synthetic actual credential\"}"',
        'note = f"password=synthetic-actual-credential {suffix}"',
        '''password = f"outer {f'password=synthetic-actual-credential {suffix}'}"''',
    ],
)
def test_python_credential_literals_comments_and_embedded_data_are_masked(code):
    masked = redact_sensitive(python_fence(code))
    assert "synthetic" not in masked and REDACTED in masked
    assert_python_syntax(masked)
    assert redact_sensitive(masked) == masked


def test_python_masking_preserves_quote_style_and_other_syntax():
    code = "client = Client(password='synthetic-secret', api_key=api_key)  # keep me"
    assert redact_sensitive(python_fence(code)) == python_fence(
        f"client = Client(password='{REDACTED}', api_key=api_key)  # keep me"
    )


@pytest.mark.parametrize("fence", ["```python", "~~~python", "```Python", "```py"])
def test_python_fence_variants_and_unicode_columns(fence):
    closing = fence[:3]
    value = (
        f'{fence}\nlabel = "café"; login(password="synthetic-secret", api_key=api_key)\n{closing}'
    )
    masked = redact_sensitive(value)
    assert "synthetic-secret" not in masked
    assert 'label = "café"' in masked and "api_key=api_key" in masked
    assert redact_sensitive(masked) == masked
    ast.parse(masked.split("\n", 1)[1].rsplit("\n", 1)[0])


def test_python_fence_inside_markdown_container_and_crlf_keeps_boundaries():
    value = (
        '> ```python\r\n> password: str = "synthetic-secret"\r\n'
        "> result = login(password=password)\r\n> ```\r\nAfterwards."
    )
    masked = redact_sensitive(value)
    assert "synthetic-secret" not in masked
    assert "login(password=password)" in masked
    assert masked.endswith("> ```\r\nAfterwards.")
    assert_python_syntax(masked)
    assert redact_sensitive(masked) == masked


def test_configured_secrets_and_token_shapes_are_masked_even_in_python(monkeypatch):
    configured = "synthetic_runtime_secret"
    token = "sk-ant-" + "x" * 30
    monkeypatch.setenv("WANDB_API_KEY", configured)
    code = f'ordinary = "{configured}"\nother = "{token}"\n# {configured}\n'
    masked = redact_sensitive(python_fence(code))
    assert configured not in masked and token not in masked
    assert_python_syntax(masked)
    assert redact_sensitive(masked) == masked


@pytest.mark.parametrize(
    "value",
    [
        '```python\npassword="synthetic partial value\n```',
        '```python\ndef broken(:\n    password="synthetic secret"\n```',
        '```javascript\nconst password = "synthetic secret";\n```',
        '```\npassword="synthetic secret"\n```',
    ],
)
def test_unparseable_or_other_code_retains_conservative_credential_masking(value):
    masked = redact_sensitive(value)
    assert "synthetic" not in masked and REDACTED in masked
    assert redact_sensitive(masked) == masked


@pytest.mark.parametrize(
    "code",
    [
        "def login(password: str) -> str:\n    return password",
        "result = login(password=password, api_key=os.environ['API_KEY'])",
        'password = """[REDACTED_SECRET]"""',
    ],
)
@pytest.mark.parametrize("encoding", ["object", "string", "nested_tool_result"])
def test_json_encoded_python_preserves_source_and_serialization(code, encoding):
    snippet = python_fence(code)
    if encoding == "object":
        payload = {"text": snippet, "title": "café"}
    elif encoding == "string":
        payload = snippet
    else:
        payload = {
            "type": "tool_result",
            "content": json.dumps({"sources": [{"text": snippet}]}, indent=2),
        }
    serialized = json.dumps(payload, indent=4, ensure_ascii=True) + "\n"
    assert redact_sensitive(serialized) == serialized
    assert json.loads(serialized) == payload
    assert_python_syntax(snippet)


def test_serialized_official_source_is_unchanged_after_repeated_sink_redaction():
    from coreweaving.corpus import Corpus

    passage = Corpus().read("guides/tracking/ops", 3)
    tool_result = json.dumps({"source_id": "S1", "text": redact_sensitive(passage.text)})
    request = {"messages": [{"content": [{"type": "tool_result", "content": tool_result}]}]}
    assert redact_sensitive(request) == request
    assert redact_sensitive(json.dumps(request)) == json.dumps(request)


def test_json_encoded_credential_literals_keep_json_and_python_valid():
    snippet = python_fence('password = """synthetic actual\ncredential"""')
    payload = {"content": json.dumps({"text": snippet})}
    masked = redact_sensitive(json.dumps(payload))
    inner = json.loads(json.loads(masked)["content"])
    assert "synthetic" not in masked and REDACTED in masked
    assert inner["text"] == python_fence(f'password = """{REDACTED}"""')
    assert_python_syntax(inner["text"])
    assert redact_sensitive(masked) == masked


def test_json_escaped_credentials_and_keys_are_masked_before_reserialization(monkeypatch):
    configured = 'synthetic "configured" secret'
    monkeypatch.setenv("WANDB_API_KEY", configured)
    payload = {
        "nested": json.dumps({"password": "synthetic spaced value"}),
        "note": configured,
        configured: "ordinary value",
        "values": ["Authorization: Basic c3ludGhldGljOm9ubHk="],
    }
    serialized = json.dumps(payload).replace("password", r"pass\u0077ord")
    masked = redact_sensitive(serialized)
    decoded = json.loads(masked)
    assert "synthetic" not in masked and "c3ludGhldGljOm9ubHk=" not in masked
    assert json.loads(decoded["nested"]) == {"password": REDACTED}
    assert decoded[REDACTED] == "ordinary value"
    assert redact_sensitive(masked) == masked


def test_json_duplicate_keys_cannot_preserve_a_discarded_credential():
    serialized = '{"password": "synthetic secret", "password": ""}'
    masked = redact_sensitive(serialized)
    assert "synthetic" not in masked
    assert json.loads(masked) == {"password": ""}
    assert redact_sensitive(masked) == masked


def test_malformed_json_keeps_conservative_credential_masking():
    malformed = '{"password": "synthetic partial secret'
    masked = redact_sensitive(malformed)
    assert "synthetic" not in masked and REDACTED in masked
    assert redact_sensitive(masked) == masked


@pytest.mark.parametrize("encoded_strings", [False, True])
def test_json_nesting_shares_the_sanitization_depth_bound(encoded_strings):
    payload = "ordinary value"
    for _ in range(42):
        payload = [payload]
    serialized = json.dumps(payload)
    if encoded_strings:
        # Three serialization layers are sufficient to exercise recursive JSON
        # strings; avoid exponential quoting merely to build a depth fixture.
        for _ in range(3):
            serialized = json.dumps(serialized)
    with pytest.raises(ValueError, match="depth limit"):
        redact_sensitive(serialized)
