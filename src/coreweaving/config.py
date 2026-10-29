"""Configuration contains names and limits; credentials stay in the environment."""

import ast
import hashlib
import io
import json
import os
import re
import tokenize
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import weave
from dotenv import load_dotenv
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[2]
AGENT_NAME = "coreweaving"
VerifyMode = Literal["off", "support"]
REDACTED = "[REDACTED_SECRET]"
_SECRET_ENV = ("ANTHROPIC_API_KEY", "WANDB_API_KEY", "OPENAI_API_KEY", "GITHUB_TOKEN", "GH_TOKEN")
_SECRET_KEY = re.compile(
    r"(?i)^(?:(?:anthropic|wandb|openai|github)[_-])?(?:api[_-]?key|access[_-]?token|"
    r"auth[_-]?token|authorization|(?:secret[_-])?password|client[_-]?secret|secret[_-]?key|token)$"
)
_TOKEN = re.compile(
    r"(?<![\w-])(?:sk-[A-Za-z0-9_-]{12,}|agt_[A-Za-z0-9_-]{12,}|"
    r"wandb_v1_[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"github_pat_[A-Za-z0-9_]{20,})(?![\w-])"
)
_ASSIGNMENT = re.compile(
    r"""(?ix)(["']?(?:(?:anthropic|wandb|openai|github)[_-])?
    (?:api[_-]?key|access[_-]?token|auth[_-]?token|authorization|password|client[_-]?secret|secret[_-]?key)
    ["']?\s*[:=]\s*)
    ((?P<quoted>"(?:\\[^\r\n]|[^"\\\r\n])*"|'(?:\\[^\r\n]|[^'\\\r\n])*')|
     (?:Basic|Bearer)[ \t]+(?:<[^>\r\n]+>|\$\{\w+\}|[^\s,"'{};]+)|
     ["'][^\r\n]*|\$\{\w+\}|[^\s,"'{};]+)"""
)
_MARKDOWN = MarkdownIt("commonmark", {"html": False})


def _placeholder(value: str) -> bool:
    scheme = re.match(r"(?i)^(?:Basic|Bearer)[ \t]+", value)
    credential = value[scheme.end() :] if scheme else value
    return bool(
        re.fullmatch(
            r"(?i)(?:\[REDACTED_SECRET\]|REDACTED|<[^>\r\n]+>|\$\{\w+\}|\$[A-Z_]\w*|"
            r"YOUR[_ -](?:API[_ -])?(?:KEY|TOKEN|PASSWORD)|\.\.\.)",
            credential,
        )
        or (
            scheme
            and credential.lower() in {"token", "tokens", "authentication", "credentials", "scheme"}
        )
    )


def _python_redactions(code, redact_assignments):
    """Locate credential literals in valid Python; expressions remain executable code.

    This only recognizes direct bindings, not data flow or constructed secrets.
    Comments and string data still receive the conservative text check.
    """
    try:
        tree = ast.parse(code)
        lexical = list(tokenize.generate_tokens(io.StringIO(code).readline))
    except (SyntaxError, ValueError, tokenize.TokenError, RecursionError):
        return None
    lines = code.splitlines(keepends=True)
    changes = {}

    def position(node, end=False):
        row = node.end_lineno if end else node.lineno
        byte_column = node.end_col_offset if end else node.col_offset
        # AST columns count UTF-8 bytes; tokenizer columns count characters.
        column = len(lines[row - 1].encode()[:byte_column].decode())
        return row, column

    def mask_literal(start, end, fragment):
        if any(lower <= start and end <= upper for lower, upper in changes):
            return
        for span in list(changes):
            if start <= span[0] and span[1] <= end:
                del changes[span]
        quotes = re.match(r"(?i)^([rubf]*)(\"\"\"|'''|\"|')", fragment)
        prefix, quote = quotes.groups() if quotes else ("", '"')
        changes[start, end] = prefix + quote + REDACTED + quote

    def binding(key, value):
        if not isinstance(key, str) or not _SECRET_KEY.fullmatch(key) or value is None:
            return
        if isinstance(value, ast.Constant):
            if value.value is None or value.value is Ellipsis or isinstance(value.value, bool):
                return
            if isinstance(value.value, (str, bytes)) and not value.value:
                return
            if isinstance(value.value, str) and _placeholder(value.value):
                return
        elif isinstance(value, ast.JoinedStr):
            literals = [part.value for part in value.values if isinstance(part, ast.Constant)]
            if all(part.strip().lower() in {"", "basic", "bearer"} for part in literals):
                return  # f"{password}" and f"Bearer {token}" contain references, not secrets.
        else:
            return
        mask_literal(position(value), position(value, True), ast.get_source_segment(code, value))

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                binding(getattr(target, "id", getattr(target, "attr", None)), node.value)
        elif isinstance(node, ast.keyword):
            binding(node.arg, node.value)
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                binding(key.value if isinstance(key, ast.Constant) else None, value)
        elif isinstance(node, ast.arguments):
            positional = node.posonlyargs + node.args
            for arg, value in zip(
                positional[len(positional) - len(node.defaults) :], node.defaults
            ):
                binding(arg.arg, value)
            for arg, value in zip(node.kwonlyargs, node.kw_defaults):
                binding(arg.arg, value)
        elif isinstance(node, ast.JoinedStr):
            # Python 3.12+ tokenizes f-string middles separately from STRING.
            if any(
                isinstance(part, ast.Constant) and redact_assignments(part.value) != part.value
                for part in node.values
            ):
                mask_literal(
                    position(node), position(node, True), ast.get_source_segment(code, node)
                )

    for token in lexical:
        if any(start <= token.start and token.end <= end for start, end in changes):
            continue
        if token.type == tokenize.COMMENT:
            masked = redact_assignments(token.string)
            if masked != token.string:
                changes[token.start, token.end] = masked
        elif token.type == tokenize.STRING:
            # Decode ordinary literals so escaped JSON/credential labels cannot
            # bypass masking. Mask the whole data literal to preserve its syntax.
            try:
                content = ast.literal_eval(token.string)
            except (SyntaxError, ValueError):
                expression = ast.parse(token.string, mode="eval").body
                # Check literal data in f-strings without treating interpolated
                # variable names as pasted credentials.
                content = "\n".join(
                    part.value for part in expression.values if isinstance(part, ast.Constant)
                )
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="replace")
            if isinstance(content, str) and redact_assignments(content) != content:
                mask_literal(token.start, token.end, token.string)
    return changes


def _redact_code_aware(text, redact_assignments):
    """Preserve valid Python fences; all other text uses conservative masking."""
    if "```" not in text and "~~~" not in text:
        return redact_assignments(text)
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    blocks = []
    for token in _MARKDOWN.parse(text):
        language = token.info.split(maxsplit=1)[:1]
        if (
            token.type != "fence"
            or not language
            or language[0].lower() not in {"python", "py", "python3"}
        ):
            continue
        changes = _python_redactions(token.content, redact_assignments)
        if changes is None:
            continue
        start_row = token.map[0] + 1
        code_lines = token.content.splitlines(keepends=True)
        starts = []
        for index, code_line in enumerate(code_lines):
            raw = lines[start_row + index].rstrip("\r\n")
            code_line = code_line.rstrip("\r\n")
            if not raw.endswith(code_line):
                break  # Unusual Markdown container: keep the conservative fallback.
            starts.append(offsets[start_row + index] + len(raw) - len(code_line))
        else:
            begin, end = offsets[start_row], offsets[start_row + len(code_lines)]
            body = text[begin:end]
            edits = [
                (starts[a[0] - 1] + a[1] - begin, starts[b[0] - 1] + b[1] - begin, replacement)
                for (a, b), replacement in changes.items()
            ]
            for lower, upper, replacement in sorted(edits, reverse=True):
                body = body[:lower] + replacement + body[upper:]
            blocks.append((begin, end, body))
    output, previous = [], 0
    for begin, end, body in blocks:
        output.extend((redact_assignments(text[previous:begin]), body))
        previous = end
    output.append(redact_assignments(text[previous:]))
    return "".join(output)


def redact_sensitive(value):
    """Mask configured secrets and common credential forms before any sink.

    This is deterministic credential masking, not general PII detection. Unknown
    encoded/split secrets may escape it. Valid fenced Python keeps annotations
    and variable expressions while credential literals are masked. Other code
    and malformed fences use conservative text masking and can lose syntax.
    Bare 40-hex hashes remain intact unless configured or credential-labelled.
    """
    secrets = sorted({os.getenv(key, "") for key in _SECRET_ENV} - {""}, key=len, reverse=True)

    def assignment(match):
        value = match[2]
        quote = value[0] if value[0] in "\"'" else ""
        closing_quote = quote if match["quoted"] else ""
        credential = value[1:] if quote else value
        if closing_quote:
            credential = credential[:-1]
        # Keep explicit documentation placeholders and the ordinary names of
        # authentication concepts; they are not pasted credential values.
        if _placeholder(credential):
            return match[0]
        return match[1] + quote + REDACTED + closing_quote

    def text(value):
        for secret in secrets:
            value = value.replace(secret, REDACTED)
        value = re.sub(
            r"-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----.*?-----END (?:[A-Z ]+)?PRIVATE KEY-----",
            REDACTED,
            value,
            flags=re.S,
        )
        value = _TOKEN.sub(REDACTED, value)

        def labelled(content):
            content = re.sub(
                r"(?i)\bBearer\s+(?!token\b|tokens\b|authentication\b|credentials\b|scheme\b|\[REDACTED_SECRET\])[^\s\"'<>]+",
                "Bearer " + REDACTED,
                content,
            )
            return _ASSIGNMENT.sub(assignment, content)

        return _redact_code_aware(value, labelled)

    def walk(item, depth=0):
        if depth > 40:
            raise ValueError("Input exceeds the sanitization depth limit.")
        if isinstance(item, str):
            # Provider tool results/verifier evidence can contain JSON inside a
            # text block. Decode before inspecting code, then escape replacements
            # through the serializer rather than running regexes on JSON syntax.
            if item.lstrip().startswith(("{", "[", '"')):
                duplicate_keys = False

                def object_pairs(pairs):
                    nonlocal duplicate_keys
                    decoded = dict(pairs)
                    duplicate_keys |= len(decoded) != len(pairs)
                    return decoded

                try:
                    decoded = json.loads(item, object_pairs_hook=object_pairs)
                except json.JSONDecodeError:
                    pass  # Malformed JSON keeps conservative text masking.
                except RecursionError:
                    raise ValueError("Input exceeds the sanitization depth limit.") from None
                else:
                    masked = walk(decoded, depth + 1)
                    # Preserve source bytes and formatting when nothing changes.
                    # Duplicate keys must serialize: discarded values could hide
                    # credentials that are absent from the decoded dictionary.
                    if masked == decoded and not duplicate_keys:
                        return item
                    return json.dumps(masked, ensure_ascii=False)
            return text(item)
        if isinstance(item, dict):
            return {
                text(key) if isinstance(key, str) else key: REDACTED
                if isinstance(key, str)
                and _SECRET_KEY.fullmatch(key)
                and isinstance(child, str)
                and child
                else walk(child, depth + 1)
                for key, child in item.items()
            }
        # Trace wrappers can require constructor metadata (for example WeaveList's
        # server). Sanitized values are plain containers, as with dictionaries above.
        if isinstance(item, list):
            return [walk(child, depth + 1) for child in item]
        if isinstance(item, tuple):
            return tuple(walk(child, depth + 1) for child in item)
        return item

    return walk(value)


def safe_exception(error: Exception) -> RuntimeError:
    """A fresh exception has no original traceback/body attached for tracing."""
    return RuntimeError(f"{type(error).__name__}: {redact_sensitive(str(error))[:500]}")


def source_fingerprint() -> str:
    """Bind evaluation evidence to the implementation bytes, even in a dirty checkout."""
    paths = sorted((ROOT / "src/coreweaving").glob("*.py")) + [ROOT / "app.py"]
    content = b"\n".join(
        str(path.relative_to(ROOT)).encode() + b"\0" + path.read_bytes() for path in paths
    )
    return hashlib.sha256(content).hexdigest()


@dataclass(frozen=True)
class Settings:
    """Immutable turn policy and model names; no credentials are stored here."""

    project: str
    agent_model: str = "claude-opus-5-5"
    judge_model: str = "claude-opus-5-5"
    max_steps: int = 10
    max_tools: int = 18
    max_revisions: int = 2
    verify_mode: VerifyMode = "support"
    cache_enabled: bool = True
    verifier_model: str = "claude-opus-5-5"

    def __post_init__(self):
        if self.verify_mode not in ("off", "support"):
            raise ValueError("VERIFY_MODE must be off or support.")
        if type(self.cache_enabled) is not bool:
            raise ValueError("cache_enabled must be a boolean.")


def settings() -> Settings:
    """Load local credentials into the environment and return validated settings."""
    load_dotenv(ROOT / ".env")
    missing = [
        key for key in ("ANTHROPIC_API_KEY", "WANDB_API_KEY", "WEAVE_PROJECT") if not os.getenv(key)
    ]
    if missing:
        raise RuntimeError("Set these names in .env: " + ", ".join(missing))
    cache_value = os.getenv("CACHE_ENABLED", "true").lower()
    if cache_value not in ("true", "false"):
        raise ValueError("CACHE_ENABLED must be true or false.")
    return Settings(
        project=os.environ["WEAVE_PROJECT"],
        agent_model=os.getenv("AGENT_MODEL", "claude-opus-5-5"),
        judge_model=os.getenv("JUDGE_MODEL", "claude-opus-5-5"),
        verifier_model=os.getenv("VERIFIER_MODEL", "claude-opus-5-5"),
        verify_mode=os.getenv("VERIFY_MODE", "support"),
        cache_enabled=cache_value == "true",
    )


@lru_cache(maxsize=1)
def init_weave():
    """Initialize once per process before emitting explicit agent spans."""
    from coreweaving.telemetry import trace_value

    config = settings()
    # We emit the new conversation/turn/chat/tool model explicitly. Autopatching
    # would add duplicate legacy Calls for the same provider requests.
    return weave.init(
        config.project,
        settings={"implicitly_patch_integrations": False},
        postprocess_inputs=trace_value,
        postprocess_output=trace_value,
    )


def conversation_url(conversation_id: str) -> str:
    from weave.trace.urls import agent_conversation_path

    entity, project = settings().project.split("/", 1)
    return agent_conversation_path(entity, project, conversation_id)
