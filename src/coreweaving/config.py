"""Configuration contains names and limits; credentials stay in the environment."""

import hashlib
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import weave
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
AGENT_NAME = "coreweaving"
VerifyMode = Literal["off", "support", "support+coverage"]
REDACTED = "[REDACTED_SECRET]"
_SECRET_ENV = ("ANTHROPIC_API_KEY", "WANDB_API_KEY", "OPENAI_API_KEY", "GITHUB_TOKEN", "GH_TOKEN")
_SECRET_KEY = re.compile(
    r"(?i)^(?:(?:anthropic|wandb|openai|github)[_-])?(?:api[_-]?key|access[_-]?token|"
    r"auth[_-]?token|authorization|password|client[_-]?secret|secret[_-]?key|token)$"
)
_TOKEN = re.compile(
    r"(?<![\w-])(?:sk-[A-Za-z0-9_-]{12,}|agt_[A-Za-z0-9_-]{12,}|"
    r"wandb_v1_[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"github_pat_[A-Za-z0-9_]{20,})(?![\w-])"
)
_ASSIGNMENT = re.compile(
    r"""(?ix)(["']?(?:(?:anthropic|wandb|openai|github)[_-])?
    (?:api[_-]?key|access[_-]?token|auth[_-]?token|authorization|password|client[_-]?secret|secret[_-]?key)
    ["']?\s*[:=]\s*)(["']?)([^\s,"'{};]+)(["']?)"""
)


def redact_sensitive(value):
    """Mask configured secrets and common credential forms before any sink.

    This is deterministic credential masking, not general PII detection. Unknown
    encoded/split secrets may escape it. Credential-labelled example values can
    be false positives; bare 40-hex hashes remain intact unless configured as a
    secret (legacy W&B keys are also caught in labelled assignments).
    """
    secrets = sorted({os.getenv(key, "") for key in _SECRET_ENV} - {""}, key=len, reverse=True)

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
        value = re.sub(
            r"(?i)\bBearer\s+(?!token\b|tokens\b|authentication\b|credentials\b|scheme\b|\[REDACTED_SECRET\])[^\s\"'<>]+",
            "Bearer " + REDACTED,
            value,
        )
        return _ASSIGNMENT.sub(lambda m: m[1] + m[2] + REDACTED + m[4], value)

    def walk(item, depth=0):
        if depth > 40:
            raise ValueError("Input exceeds the sanitization depth limit.")
        if isinstance(item, str):
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
        if isinstance(item, (list, tuple)):
            return type(item)(walk(child, depth + 1) for child in item)
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
    project: str
    agent_model: str = "claude-sonnet-5-5"
    judge_model: str = "claude-opus-5-5"
    max_steps: int = 10
    max_tools: int = 18
    max_revisions: int = 2
    verify_mode: VerifyMode = "support"
    cache_enabled: bool = True

    def __post_init__(self):
        if self.verify_mode not in ("off", "support", "support+coverage"):
            raise ValueError("VERIFY_MODE must be off, support, or support+coverage.")
        if type(self.cache_enabled) is not bool:
            raise ValueError("cache_enabled must be a boolean.")


def settings() -> Settings:
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
        agent_model=os.getenv("AGENT_MODEL", "claude-sonnet-5-5"),
        judge_model=os.getenv("JUDGE_MODEL", "claude-opus-5-5"),
        verify_mode=os.getenv("VERIFY_MODE", "support"),
        cache_enabled=cache_value == "true",
    )


@lru_cache(maxsize=1)
def init_weave():
    config = settings()
    # We emit the new conversation/turn/chat/tool model explicitly. Autopatching
    # would add duplicate legacy Calls for the same provider requests.
    return weave.init(config.project, settings={"implicitly_patch_integrations": False})


def conversation_url(conversation_id: str) -> str:
    from weave.trace.urls import agent_conversation_path

    entity, project = settings().project.split("/", 1)
    return agent_conversation_path(entity, project, conversation_id)
