"""A small interface that shows both the answer and the evidence behind it."""

import json
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import version
from queue import Empty, Queue

import streamlit as st

from coreweaving.agent import Agent, Session
from coreweaving.config import init_weave, redact_sensitive, settings
from coreweaving.corpus import Corpus
from coreweaving.library import list_answers, review_answer, save_answer

st.set_page_config(
    page_title="Coreweaving · Ask the docs",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="auto",
)
st.markdown(
    """<style>
.block-container {max-width:1060px;padding-top:4rem;padding-bottom:3rem}
[data-testid=stHeading] h1 {font-family:Georgia,serif;font-weight:400;
    font-size:clamp(2.25rem,4vw,3.4rem);letter-spacing:-1.5px;line-height:1.13}
[data-testid=stSidebar] {background:#e8eee5}
[data-testid=stChatMessage] {border:1px solid #d7dfd2;border-radius:12px;background:#fffefa;
    padding:1.4rem}
[data-testid=stChatMessage] p {line-height:1.65}
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


def run_question(corpus, config, client, question, session, events):
    """No Streamlit calls: UI reruns cannot interrupt research or persistence."""
    result = redact_sensitive(Agent(corpus, config).run(question, session, events.put))
    warning = None
    try:
        save_answer(result.get("question", question), result)
    except Exception as exc:
        warning = (
            f"The answer is ready, but its local copy could not be saved ({type(exc).__name__})."
        )
    try:
        client.flush()
    except Exception as exc:
        warning = (warning + " " if warning else "") + (
            f"Trace delivery needs checking ({type(exc).__name__})."
        )
    return result, warning


@st.fragment(run_every="1s")
def show_pending_turn():
    job = st.session_state.get("job")
    if job is None:
        return
    if job["future"].done():
        # Remove ownership before a UI rerun so completion is consumed once.
        st.session_state.job = None
        try:
            result, warning = job["future"].result()
        except Exception as exc:
            st.session_state.library_warning = f"This turn could not finish ({type(exc).__name__})."
        else:
            st.session_state.turns.append((job["question"], result))
            if warning:
                st.session_state.library_warning = warning
        st.rerun()
    while True:
        try:
            event = job["events"].get_nowait()
        except Empty:
            break
        stage, detail = event["stage"], event["detail"]
        if stage == "thinking":
            job["progress"] = detail
        elif stage == "search_docs":
            job["progress"] = "Searching: " + detail.get("query", "")
        elif stage == "read_page":
            job["progress"] = "Reading: " + detail.get("page_id", "documentation")
        elif stage == "verification":
            job["progress"] = "Checking finished." if detail["passed"] else "Revising the draft."
    st.info("Working on your question · " + job["progress"])
    st.caption(
        "You can browse the answer library while this finishes. One question runs at a time."
    )


def show_result(result):
    verification = result["verification"]
    passed = verification["passed"]
    status = verification.get("status", "passed" if passed else "failed")
    mode = verification.get("mode", result.get("verify_mode", "support"))
    check_label = (
        "Check not run · experimental answer"
        if status == "not_run"
        else "Source and coverage checks passed"
        if passed and mode == "support+coverage"
        else "Source check passed"
        if passed
        else "Check did not pass"
    )
    st.caption(
        f"{check_label} · {len(result['sources'])} sources · {result['elapsed_seconds']:.1f}s"
    )
    st.markdown(result["answer"])
    if coverage := verification.get("coverage"):
        with st.expander("Did it answer the whole question?"):
            st.caption(
                "Support checks whether the facts match the sources. Coverage checks whether "
                "the answer addresses the requested parts and relevant caveats. Both are model "
                "judgments; your review remains separate."
            )
            for item in coverage:
                label = {
                    "covered": "Addressed",
                    "missing": "Missing",
                    "uncertain": "Needs evidence",
                    "not_applicable": "Outside this question",
                }.get(item["status"], item["status"])
                st.markdown(f"**{label}:** {item['obligation']}")
                st.write(item["reason"])
                if item.get("source_ids"):
                    st.caption("Evidence: " + ", ".join(item["source_ids"]))
    elif status == "not_run":
        st.warning("Verification was disabled for this experimental run.")
    coverage_ids = {sid for item in verification.get("coverage", []) for sid in item["source_ids"]}
    visible_sources = {source["source_id"]: source for source in result["sources"]}
    visible_sources.update(
        {
            source["source_id"]: source
            for source in result.get("all_read_evidence", [])
            if source["source_id"] in coverage_ids
        }
    )
    if visible_sources:
        with st.expander(f"Sources · {len(visible_sources)} sources"):
            st.caption("Match [S1], [S2], and other citations to the passages below.")
            for source in visible_sources.values():
                if "url" in source:
                    st.markdown(f"**[{source['source_id']}] [{source['title']}]({source['url']})**")
                    st.caption(source["heading"])
                    if source.get("page_context") and source["page_context"] != source["text"]:
                        st.caption("Page context (including any workflow warnings)")
                        st.text(source["page_context"])
                    st.text(source["text"])
                else:
                    st.markdown(f"**[{source['source_id']}] Python execution**")
                    st.code(source["code"], language="python")
                    st.text(source.get("output", source.get("error", "")))
    with st.expander("What the check found"):
        st.caption(
            "The verifier compares claims with cited evidence. Coverage mode also looks for "
            "missing requested parts in the research and conversation context. A successful "
            "check can still miss mistakes; it is not a guarantee of correctness."
        )
        for index, check in enumerate(result["verification_attempts"], 1):
            st.markdown(f"**Draft {index}: {'passed' if check['passed'] else 'needs revision'}**")
            for claim in check["claims"]:
                claim_status = claim.get(
                    "status", "supported" if claim.get("supported") else "unsupported"
                )
                st.write(f"{claim_status.capitalize()}: {claim['text']}")
            for issue in check["issues"]:
                st.write(issue)
        if not result["verification_attempts"]:
            st.write(result["verification"]["issues"])
    if metrics := result.get("metrics"):
        amount = metrics["estimated_usd"]
        label = (
            f"Estimated model cost · ${amount:.4f}"
            if amount is not None
            else "Model usage · partial estimate"
        )
        with st.expander(label):
            st.write(
                f"{metrics['model_calls']} model calls · "
                f"{metrics['total_input_tokens']:,} input tokens · "
                f"{metrics['tokens']['output_tokens']:,} output tokens"
            )
            st.caption(
                "Tokens are the pieces of text the model reads and produces. Re-reading context also counts."
            )
            tokens = metrics["tokens"]
            st.caption(
                f"Reused from cache: {tokens.get('cache_read_input_tokens', 0):,} tokens · "
                f"Written to cache: {tokens.get('cache_creation_input_tokens', 0):,}. "
                "Caching reuses an unchanged prompt prefix at a different price; it does not "
                "prove an answer is correct or remove the need for source checks."
            )
            st.table(
                [
                    {
                        "Stage": {
                            "planner": "Research and drafting",
                            "verification": "Source verification",
                        }.get(stage, stage),
                        "Calls": values["calls"],
                        "Known estimate (USD)": f"${values['known_estimated_usd']:.5f}",
                    }
                    for stage, values in metrics["by_purpose"].items()
                ]
            )
            research = metrics["research"]
            st.write(
                f"Research: {research['searches']} searches, {research['passage_reads']} passage reads "
                f"across {research['distinct_pages_read']} pages, "
                f"{research['repeated_tool_requests']} repeated tool requests, "
                f"{research['drafts_submitted']} submitted drafts."
            )
            if metrics["unpriced_calls"]:
                st.warning(
                    f"{metrics['unpriced_calls']} calls lack a complete estimate; they are not counted as free."
                )
            st.caption(metrics["scope"])
            st.caption(
                f"[Pricing source]({metrics['pricing']['source']}) · checked "
                f"{metrics['pricing']['checked_at']}. Returned call usage is also recorded in Weave."
            )
    with st.expander("Which version made this answer?"):
        if not result.get("source_sha256"):
            st.caption(
                "Implementation version unknown. This earlier record predates code, prompt "
                "and configuration fingerprints; its original evidence is preserved."
            )
        else:
            st.caption(
                "These identifiers record the code build, prompts, settings and documentation "
                "used for this answer. A different version does not make an old answer wrong."
            )
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
        st.caption("Your review is separate from this original record and its source check.")
    with st.expander("Research steps"):
        for action in result["actions"]:
            st.markdown(f"**{action['tool']}**")
            st.json(action["input"], expanded=False)
            st.json(action["result"], expanded=False)
    st.link_button("Inspect this conversation in Weave ↗", result["trace_url"])


def show_library(corpus):
    st.caption("COREWEAVING / OUR ANSWER LIBRARY")
    st.title("Keep the evidence. Improve the answer.")
    st.write("Real agent responses, saved locally for us to review together.")
    st.caption(
        "A source check, your review, and source freshness are separate signals. "
        "Saved answers are never fed back to the agent as documentation."
    )
    try:
        records = list_answers()
    except Exception as exc:
        st.error(f"The local library could not open ({type(exc).__name__}).")
        return
    if not records:
        st.info(
            "Ask a question in Conversation. Its answer, sources, and usage will appear here for review."
        )
        return
    estimate = sum(r["result"].get("metrics", {}).get("known_estimated_usd", 0) for r in records)
    unknown = sum(
        not r["result"].get("metrics") or r["result"]["metrics"]["estimated_usd"] is None
        for r in records
    )
    columns = st.columns(3)
    columns[0].metric("Saved turns", len(records))
    columns[1].metric("Marked useful", sum(r["review_state"] == "useful" for r in records))
    columns[2].metric("Known model estimate", f"${estimate:.4f}")
    st.caption(
        f"Across these saved turns only; {unknown} have missing or partial estimates. "
        "Includes research and source checks; excludes Signals and separate evaluation runs."
    )
    query = st.text_input("Find a question")
    choices = {
        "All": None,
        "Unreviewed": "unreviewed",
        "Useful": "useful",
        "Needs correction": "needs_correction",
    }
    selected = st.selectbox("Review status", list(choices))
    visible = [
        r
        for r in records
        if query.casefold() in r["question"].casefold()
        and (choices[selected] is None or r["review_state"] == choices[selected])
    ]
    if not visible:
        st.info("No saved questions match those filters.")
        return
    by_id = {r["id"]: r for r in visible}
    answer_id = st.selectbox(
        "Saved question", list(by_id), format_func=lambda key: by_id[key]["question"]
    )
    row = by_id[answer_id]
    st.markdown(f"**{row['question']}**")
    st.caption(f"Saved {row['created_at']} · Review: {row['review_state'].replace('_', ' ')}")
    if row["result"].get("snapshot_id") != corpus.snapshot_id:
        st.warning(
            "The documentation snapshot differs from this saved answer. Review it against the current sources before reusing it."
        )
    else:
        st.caption(
            "Source snapshot matches the currently loaded documentation; this does not prove the answer is correct."
        )
    if context := row["result"].get("conversation_context"):
        with st.expander("Conversation context used for this answer"):
            for message in context:
                st.markdown(f"**{message['role'].title()}**")
                st.markdown(message["content"])
    show_result(row["result"])
    st.info(
        "Review the whole task: did it answer every part, explain prerequisites, name its assumptions, "
        "and keep legacy and current workflows compatible? A supported sentence can still be part "
        "of an incomplete answer."
    )
    labels = {
        "unreviewed": "Not reviewed yet",
        "useful": "Useful after my review",
        "needs_correction": "Needs a correction",
    }
    with st.form("review_" + answer_id):
        state = st.selectbox(
            "Your assessment",
            list(labels),
            index=list(labels).index(row["review_state"]),
            format_func=labels.get,
        )
        notes = st.text_area(
            "What makes sense, what is missing, or what needs correcting?", value=row["notes"]
        )
        if st.form_submit_button("Save my review"):
            try:
                review_answer(answer_id, state, notes)
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.rerun()
    st.caption(
        "Review notes stay on this computer. Dataset promotion to the public Weave project is a separate, deliberate step."
    )
    st.download_button(
        "Download this answer and its evidence",
        json.dumps(row, ensure_ascii=False, indent=2),
        file_name=f"coreweaving-answer-{answer_id}.json",
        mime="application/json",
    )


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
        "Use VERIFY_MODE=support or support+coverage; off is for evaluation experiments."
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
        st.session_state.workspace_view = "Conversation"
        st.rerun()
    view = st.radio("Workspace", ["Conversation", "Answer library"], key="workspace_view")
    st.markdown("**Keep the conversation going.**")
    st.write("Ask a follow-up, such as ‘How would I add that to my agent?’")
    st.caption("The assistant remembers the last six exchanges in this session.")
    with st.expander("Purpose, permissions & memory"):
        st.write("Purpose: help you understand and use Weave, with evidence you can inspect.")
        st.caption(
            "It can search and read the saved docs, run small offline Python examples, and "
            "submit an answer for checking. It cannot change your accounts, deploy code, "
            "install packages, or read your files."
        )
        st.caption(
            "Conversation memory keeps six exchanges. New conversation clears that working "
            "context; saved answers and public Weave traces remain. Your library review never "
            "silently becomes a model instruction or a documentation fact."
        )
    with st.expander("About this demo"):
        st.caption(f"{len(corpus.pages)} saved Weave documentation pages")
        st.caption(f"Snapshot: {corpus.snapshot_id[:12]}")
        st.caption(f"Answer check: {config.verify_mode}")
        st.caption(f"Model: {config.agent_model}")
        reference_version = getattr(corpus, "docs_sdk_version", "unknown")
        runtime_version = version("weave")
        if reference_version != "unknown" and reference_version != runtime_version:
            st.warning(
                f"Python reference source: {reference_version}; installed Weave: {runtime_version}. "
                "Newer APIs may be covered by guides rather than that reference page."
            )
        st.caption("Code examples run in an offline Python container when needed.")
        st.caption("New conversations and server restarts clear conversation memory.")
        st.caption("The local answer library persists across restarts. It is excluded from Git.")

if busy:
    show_pending_turn()

if view == "Answer library":
    show_library(corpus)
    st.stop()

if warning := st.session_state.pop("library_warning", None):
    st.warning(warning)

st.caption("COREWEAVING / WEAVE DOCUMENTATION")
st.title("Good answers leave a trail.")
st.write("Ask about Weave. See the answer, its sources, and how it was checked.")
st.caption(
    "This demo records conversations in a public Weave project. "
    "Answers are also saved locally for review. Use public examples and keep credentials out of chat."
)
if not st.session_state.turns:
    # An inline welcome field avoids the pinned chat layout scrolling a narrow
    # first screen past its heading. Conversation input stays pinned below.
    with st.container(key="welcome_input"):
        question = st.chat_input("Ask about Weave…", key="welcome_question", disabled=busy)
else:
    question = st.chat_input("Ask about Weave…", key="conversation_question", disabled=busy)

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
        st.markdown(previous_question)
    with st.chat_message("assistant"):
        show_result(previous_result)

question = question or st.session_state.pop("pending_question", None)
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
    }
    st.rerun()
