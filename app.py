"""A conversation, checked answers, and inspectable evidence.

One background job owns each turn. UI reruns only poll its progress or inspect
results; the agent alone chooses tools and decides when its answer is ready.
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import version
from queue import Empty, Queue
from textwrap import dedent

import streamlit as st
from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml

from coreweaving.agent import Agent, Session
from coreweaving.config import init_weave, redact_sensitive, settings
from coreweaving.corpus import Corpus

st.set_page_config(
    page_title="Coreweaving · Ask the docs",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="auto",
)
st.markdown(
    """<style>
.block-container {max-width:1000px;padding-top:3rem;padding-bottom:3rem}
[data-testid=stHeading] h1 {font-family:Georgia,serif;font-weight:400;
    font-size:clamp(2.25rem,4vw,3.4rem);letter-spacing:-1.5px;line-height:1.13}
[data-testid=stSidebar] {background:#e8eee5}
[data-testid=stChatMessage] {border:1px solid #d7dfd2;border-radius:12px;background:#fffefa;
    padding:1.4rem}
[data-testid=stChatMessage] p {line-height:1.65}
[data-testid=stChatMessage] li {line-height:1.65;margin-bottom:.45rem}
[data-testid=stChatMessage] h2,[data-testid=stChatMessage] h3 {margin-top:1.2rem}
[data-testid=stCaptionContainer] p {color:#52655c!important}
button:focus-visible,a:focus-visible,textarea:focus-visible {
    outline:3px solid #236953!important;outline-offset:3px!important}
[data-testid=stButton] button,[data-testid=stPopover] button {min-height:44px}
[data-testid=stChatInput] textarea {min-height:48px}
.st-key-welcome_input {margin:.6rem 0 1.5rem}
.st-key-starter_learn,.st-key-starter_build,.st-key-starter_evaluate {
    background:#fffefa;border-radius:10px}
.st-key-starters [data-testid=stCaptionContainer] {min-height:3.5rem}
@media(max-width:640px) {
    [data-testid=stChatMessage] {padding:1rem}
    .st-key-starters [data-testid=stCaptionContainer] {min-height:0}
}
</style>""",
    unsafe_allow_html=True,
)


@st.cache_resource
def resources():
    return Corpus(), init_weave()


@st.cache_resource
def worker_pool():
    return ThreadPoolExecutor(max_workers=2, thread_name_prefix="coreweaving")


def show_markdown(text):
    """Keep chat formatting and links without automatically fetching images."""
    # Match Streamlit's own Markdown normalization before classifying tokens.
    text = dedent(text).strip()
    parser = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])
    has_images = False

    def image_as_text(tokens, index, options, env):
        nonlocal has_images
        has_images = True
        return escapeHtml(parser.renderer.renderInlineAsText(tokens[index].children, options, env))

    parser.renderer.rules["image"] = image_as_text
    rendered = parser.render(text)
    if has_images:
        # This HTML comes only from the parser with raw HTML disabled. Streamlit
        # also sanitizes it with DOMPurify; scripts remain explicitly disabled.
        st.html(rendered, unsafe_allow_javascript=False)
    else:
        st.markdown(text)


def run_question(corpus, config, client, question, session, events):
    """Finish a turn outside Streamlit's rerun lifecycle, then flush its trace."""
    result = redact_sensitive(Agent(corpus, config).run(question, session, events.put))
    warning = None
    try:
        client.flush()
    except Exception as exc:
        warning = f"Your answer is ready, but its activity record may not have reached Weave ({type(exc).__name__})."
    return result, warning


@st.fragment(run_every="1s")
def show_pending_turn():
    """Poll progress and consume a worker's completed result exactly once."""
    job = st.session_state.get("job")
    if job is None:
        return
    if job["future"].done():
        # Remove ownership before a UI rerun so completion is consumed once.
        st.session_state.job = None
        try:
            result, warning = job["future"].result()
        except Exception as exc:
            st.session_state.turn_warning = f"I couldn't finish this answer. Please try again. Error: {type(exc).__name__}."
        else:
            st.session_state.turns.append((job["question"], result))
            if warning:
                st.session_state.turn_warning = warning
        st.rerun()
    while True:
        try:
            event = job["events"].get_nowait()
        except Empty:
            break
        stage, detail = event["stage"], event["detail"]
        if stage == "search_docs":
            job["searches"] = job.get("searches", 0) + 1
        elif stage == "source_read":
            job.setdefault("pages", {})[detail["url"]] = detail["title"]
        labels = {
            "thinking": "Working on your question",
            "search_docs": "Searching the docs",
            "read_page": "Reading a documentation page",
            "run_python": "Running a small Python example without internet access",
            "submit_answer": "Checking the answer against its sources",
        }
        if stage in labels:
            job["progress"] = labels[stage]
        elif stage == "verification":
            job["progress"] = "Answer checked" if detail["passed"] else "Revising the answer"
    elapsed = int(time.monotonic() - job["started_at"])
    # Report actual work, never a fabricated percentage or an unverified draft.
    with st.status(f"{job['progress']} · {elapsed}s", state="running", expanded=True):
        pages = job.get("pages", {})
        st.caption(f"Searches: {job.get('searches', 0)} · Pages read: {len(pages)}")
        for url, title in pages.items():
            st.markdown(f"- [{title}]({url})")


def show_result(result):
    """Show the checked answer first; keep inspection one click away."""
    verification = result["verification"]
    passed = verification["passed"]
    status = verification.get("status", "passed" if passed else "failed")
    mode = verification.get("mode", result.get("verify_mode", "support"))
    check_label = (
        "Waiting for your reply"
        if passed and result.get("kind") == "clarification"
        else "Partial answer · checked against the docs"
        if result.get("task_complete") is False and passed
        else "Answer not checked · test mode"
        if status == "not_run"
        else "Answer and completeness checked"
        if passed and mode == "support+coverage"
        else "Answer checked against the docs"
        if passed and result.get("task_complete") is True
        else "Sources checked"
        if passed
        else "Couldn't verify the answer"
    )
    failed = not passed and status != "not_run"
    evidence = result.get("all_read_evidence", [])
    passages = [source for source in evidence if source.get("url")]
    if failed and result.get("kind") == "insufficient":
        st.markdown(
            "I found relevant pages, but couldn't confirm an answer from them."
            if passages
            else "I couldn't finish checking an answer to this question."
        )
        pages = {source["url"]: source["title"] for source in passages}
        if pages:
            st.markdown("**The official pages I found:**")
            for url, title in list(pages.items())[:3]:
                st.markdown(f"- [{title}]({url})")
    else:
        show_markdown(result["answer"])
    if missing := result.get("missing_outcomes"):
        show_markdown(
            "**Still to answer:**\n"
            + "\n".join(
                f"- {item['description'] if isinstance(item, dict) else item}" for item in missing
            )
        )
    if status == "not_run":
        st.warning("This test response skipped the answer check.")
    source_label = (
        f"{len(passages)} document sections found"
        if failed
        else f"{len(result['sources'])} cited sources"
    )
    st.caption(
        f"{check_label} · {source_label} · {result['elapsed_seconds']:.1f}s",
        help="An AI checks whether the docs support the answer and whether it answers your question. It can still miss mistakes.",
    )
    # Put citation navigation beside the answer. Exact passages and audit details
    # remain in the analysis window, with no extra model request for inspection.
    if result["sources"]:
        with st.popover(
            "View cited sources",
            key="citations_" + result["answer_id"],
            icon=":material/menu_book:",
        ):
            st.caption("[S1] points to a document section. [C1] points to a Python run.")
            for source in result["sources"]:
                if source.get("url"):
                    st.markdown(f"**[{source['source_id']}]** [{source['title']}]({source['url']})")
                    st.caption(source["heading"])
                else:
                    st.markdown(f"**[{source['source_id']}]** Python run without internet access")
            st.caption("Open Sources & analysis for the exact passages and checks.")
    if st.button(
        "Sources & analysis",
        key="analysis_" + result["answer_id"],
        icon=":material/manage_search:",
        help="See the docs read, answer checks, time and cost. Opening this does not ask the AI again.",
    ):
        show_analysis(result)


@st.dialog("Sources & analysis", width="large")
def show_analysis(result):
    """Observable evidence and checks, separate from the conversational answer."""
    verification = result["verification"]
    st.caption("See the documents read, what was checked, and the work behind this answer.")
    st.link_button("View this conversation's activity in Weave ↗", result["trace_url"])
    st.download_button(
        "Download answer and evidence",
        json.dumps(result, indent=2),
        file_name=f"coreweaving-{result['answer_id']}.json",
        mime="application/json",
        help="Save a JSON file containing this answer, sources, checks and model usage.",
    )
    visible_sources = {
        source["source_id"]: source
        for source in result.get("all_read_evidence", []) + result["sources"]
    }
    if visible_sources:
        with st.expander(f"Documents and Python results · {len(visible_sources)} items"):
            st.caption(
                "Evidence consulted for this answer, including earlier sources reused in this conversation. "
                "Match [S1], [S2] and other labels to the answer. Some items were read but not cited."
            )
            for source in visible_sources.values():
                if "url" in source:
                    st.markdown(f"**[{source['source_id']}] [{source['title']}]({source['url']})**")
                    st.caption(source["heading"])
                    if source.get("page_context") and source["page_context"] != source["text"]:
                        st.caption("Page introduction and important notes")
                        st.text(source["page_context"])
                    st.text(source["text"])
                else:
                    st.markdown(f"**[{source['source_id']}] Python run**")
                    st.code(source["code"], language="python")
                    st.text(source.get("output", source.get("error", "")))
    with st.expander("What the check found"):
        st.caption("An AI checks the answer against the documents and your question. It can miss mistakes.")
        for issue in verification["issues"]:
            show_markdown(issue)
        missing_parts = verification.get("missing_parts", [])
        for part in missing_parts:
            show_markdown(f"**Still to answer:** {part}")
        if not verification["issues"] and not missing_parts:
            st.caption(
                "The check found no unsupported claims or missing answers. It can still miss mistakes."
                if verification["passed"]
                else "The answer check failed without explaining why."
            )
    if metrics := result.get("metrics"):
        amount = metrics["estimated_usd"]
        label = (
            f"Estimated model cost · ${amount:.2f}"
            if amount is not None
            else "AI usage · cost estimate incomplete"
        )
        with st.expander(label):
            st.write(
                f"{metrics['model_calls']} AI requests · "
                f"{metrics['total_input_tokens']:,} tokens sent · "
                f"{metrics['tokens']['output_tokens']:,} tokens generated"
            )
            st.caption("Tokens are the small pieces of text used to measure AI usage.")
            tokens = metrics["tokens"]
            st.caption(
                f"Reused from cache: {tokens.get('cache_read_input_tokens', 0):,} tokens · "
                f"Saved to cache: {tokens.get('cache_creation_input_tokens', 0):,}. "
                "Caching reuses repeated input at different rates. The estimate includes research and answer checks."
            )
            if metrics["unpriced_calls"]:
                st.warning(
                    f"We couldn't fully price {metrics['unpriced_calls']} AI requests, so the total cost is incomplete."
                )
            st.caption(metrics["scope"])
            st.caption(
                f"[Pricing source]({metrics['pricing']['source']}) · checked "
                f"{metrics['pricing']['checked_at']}. Weave also records usage reported by the model provider."
            )
    with st.expander("Model and version details"):
        st.caption("These IDs identify the code, instructions and saved docs used for this answer.")
        st.json(
            {
                "code_build": result.get("source_sha256", "unknown"),
                "prompt_bundle": result.get("prompt_sha256", "unknown"),
                "configuration": result.get("config_sha256", "unknown"),
                "documentation_snapshot": result.get("snapshot_id", "unknown"),
                "model": result.get("model", "unknown"),
                "check_mode": result.get("verify_mode", "unknown"),
            },
            expanded=False,
        )
    with st.expander("How the answer was researched"):
        names = {
            "search_docs": "Search the docs",
            "read_page": "Read a section",
            "run_python": "Run Python",
            "submit_answer": "Check a proposed answer",
        }
        for action in result["actions"]:
            show_markdown(f"**{names.get(action['tool'], action['tool'])}**")
            st.json(action["input"], expanded=False)
            st.json(action["result"], expanded=False)


try:
    corpus, weave_client = resources()
    config = settings()
except Exception as exc:
    st.error(f"Setup needs attention: {type(exc).__name__}: {redact_sensitive(str(exc))}")
    st.info("Follow the README setup steps, then reload this page.")
    st.stop()

if config.verify_mode == "off":
    st.error(
        "The conversational app requires source verification. "
        "Use VERIFY_MODE=support; off is for evaluation experiments."
    )
    st.stop()

if "session" not in st.session_state:
    st.session_state.session = Session()
    st.session_state.turns = []
    st.session_state.job = None

busy = st.session_state.get("job") is not None

with st.sidebar:
    st.markdown("### coreweaving")
    st.write("Your companion to the Weave docs.")
    if st.button("New conversation", width="stretch", disabled=busy):
        st.session_state.session = Session()
        st.session_state.turns = []
        st.rerun()
    st.markdown("**Keep the conversation going.**")
    st.write("Ask a follow-up, such as ‘How would I add that to my agent?’")
    st.caption("The assistant remembers the last six exchanges in this session.")
    with st.expander("What it can do and remember"):
        st.write("Get help using Weave, with links to the documents behind each answer.")
        st.caption(
            "It can search saved docs, read pages, and run small Python examples without internet access. "
            "It checks answers before showing them. It cannot change your accounts, deploy code, "
            "install packages, or read your files."
        )
        st.caption(
            "It remembers the last six question-and-answer exchanges in this chat. "
            "New conversation clears that memory. The public activity records in Weave remain."
        )
    with st.expander("About this demo"):
        st.caption(f"{len(corpus.pages)} saved Weave documentation pages")
        st.caption("Answers use a saved copy of the docs, not a live website search.")
        st.caption(f"Saved-docs ID: {corpus.snapshot_id[:12]}")
        st.caption("Answers are checked against the sources and your question.")
        st.caption(f"Model: {config.agent_model}")
        reference_version = getattr(corpus, "docs_sdk_version", "unknown")
        runtime_version = version("weave")
        if reference_version != "unknown" and reference_version != runtime_version:
            st.warning(
                f"The saved Python API reference is labeled version {reference_version}. "
                f"This app uses Weave {runtime_version}. We haven't tested every generated "
                "example with that installed version."
            )
        st.caption("The Python tool can test basic examples. It cannot run Weave or model-provider libraries.")
        st.caption("New conversations and server restarts clear conversation memory.")

if warning := st.session_state.pop("turn_warning", None):
    st.warning(warning)

st.caption("COREWEAVING / WEAVE DOCUMENTATION")
st.title("Good answers leave a trail.")
st.write("Ask about Weave. See the answer, its sources, and how it was checked.")
st.caption(
    "This demo records conversations in a public Weave project. "
    "Use public examples. Don't enter API keys, passwords or private information."
)
if not st.session_state.turns:
    # An inline welcome field avoids the pinned chat layout scrolling a narrow
    # first screen past its heading. Conversation input stays pinned below.
    with st.container(key="welcome_input"):
        question = st.chat_input(
            "What are you trying to do with Weave?", key="welcome_question", disabled=busy
        )
else:
    question = st.chat_input(
        "Ask a follow-up or add context…", key="conversation_question", disabled=busy
    )

starter_area = st.empty()
if not st.session_state.turns and not busy:
    examples = [
        (
            "learn",
            "Understand Weave",
            "How do tracing, evaluations, and Signals fit together?",
        ),
        (
            "build",
            "Trace an agent",
            "How do I trace a custom multi-turn agent in Python?",
        ),
        (
            "evaluate",
            "Build an evaluation",
            "How do I evaluate my agent using a dataset and an LLM judge?",
        ),
    ]
    with starter_area.container(), st.container(key="starters"):
        st.markdown("**Start with a task, or ask your own question.**")
        for column, (key, label, example) in zip(st.columns(3), examples):
            with column, st.container(border=True, key=f"starter_{key}"):
                if st.button(label + " →", width="stretch", wrap=True):
                    st.session_state.pending_question = example
                st.caption(example)

for previous_question, previous_result in st.session_state.turns:
    with st.chat_message("user"):
        show_markdown(previous_question)
    with st.chat_message("assistant"):
        show_result(previous_result)

if busy:
    with st.chat_message("user"):
        show_markdown(st.session_state.job["question"])
    with st.chat_message("assistant"):
        show_pending_turn()

# Consume both input sources even when typed text takes precedence. A queued
# preset must not survive this interaction and start another request on a rerun.
preset_question = st.session_state.pop("pending_question", None)
question = question or preset_question
if question and not busy:
    question = redact_sensitive(question)
    events = Queue()
    future = worker_pool().submit(
        run_question, corpus, config, weave_client, question, st.session_state.session, events
    )
    st.session_state.job = {
        "question": question,
        "future": future,
        "events": events,
        "progress": "Starting research…",
        "started_at": time.monotonic(),
    }
    st.rerun()
