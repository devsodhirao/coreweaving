"""Configuration contains names and limits; credentials stay in the environment."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import weave
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
AGENT_NAME = "coreweaving"


@dataclass(frozen=True)
class Settings:
    project: str
    agent_model: str = "claude-sonnet-5-5"
    judge_model: str = "claude-opus-5-5"
    max_steps: int = 10
    max_tools: int = 18
    max_revisions: int = 2


def settings() -> Settings:
    load_dotenv(ROOT / ".env")
    missing = [
        key for key in ("ANTHROPIC_API_KEY", "WANDB_API_KEY", "WEAVE_PROJECT") if not os.getenv(key)
    ]
    if missing:
        raise RuntimeError("Set these names in .env: " + ", ".join(missing))
    return Settings(
        project=os.environ["WEAVE_PROJECT"],
        agent_model=os.getenv("AGENT_MODEL", "claude-sonnet-5-5"),
        judge_model=os.getenv("JUDGE_MODEL", "claude-opus-5-5"),
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
