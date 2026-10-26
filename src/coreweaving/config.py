"""Configuration contains names and limits; credentials stay in the environment."""

import hashlib
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import weave
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
AGENT_NAME = "coreweaving"
VerifyMode = Literal["off", "support", "support+coverage"]


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
