"""A small interface that shows both the answer and the evidence behind it."""

import streamlit as st

from coreweaving.agent import Agent, Session
from coreweaving.config import init_weave, settings
from coreweaving.corpus import Corpus

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


def show_result(result):
    passed = result["verification"]["passed"]
    st.caption(
        f"{'Source check passed' if passed else 'Source check did not pass'} · "
        f"{len(result['sources'])} sources · {result['elapsed_seconds']:.1f}s"
    )
    st.markdown(result["answer"])
    if result["sources"]:
        with st.expander(f"Sources · {len(result['sources'])} sources"):
            st.caption("Match [S1], [S2], and other citations to the passages below.")
            for source in result["sources"]:
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
            "A separate model call compared the draft with these sources. "
            "This check can miss mistakes; it is not a guarantee of correctness."
        )
        for index, check in enumerate(result["verification_attempts"], 1):
            st.markdown(f"**Draft {index}: {'passed' if check['passed'] else 'needs revision'}**")
            for claim in check["claims"]:
                st.write(("✓ " if claim["supported"] else "✗ ") + claim["text"])
            for issue in check["issues"]:
                st.write(issue)
        if not result["verification_attempts"]:
            st.write(result["verification"]["issues"])
    with st.expander("Research steps"):
        for action in result["actions"]:
            st.markdown(f"**{action['tool']}**")
            st.json(action["input"], expanded=False)
            st.json(action["result"], expanded=False)
    st.link_button("Inspect this conversation in Weave ↗", result["trace_url"])


try:
    corpus, weave_client = resources()
    config = settings()
except Exception as exc:
    st.error(f"Setup needs attention: {type(exc).__name__}: {exc}")
    st.info("Follow the README setup steps, then reload this page.")
    st.stop()

if "session" not in st.session_state:
    st.session_state.session = Session()
    st.session_state.turns = []

with st.sidebar:
    st.markdown("### coreweaving")
    st.write("Your companion to the Weave docs.")
    if st.button("New conversation", width="stretch"):
        st.session_state.session = Session()
        st.session_state.turns = []
        st.rerun()
    st.markdown("**Keep the conversation going.**")
    st.write("Ask a follow-up, such as ‘How would I add that to my agent?’")
    st.caption("The assistant remembers the last six exchanges in this session.")
    with st.expander("About this demo"):
        st.caption(f"{len(corpus.pages)} saved Weave documentation pages")
        st.caption(f"Snapshot: {corpus.snapshot_id[:12]}")
        st.caption(f"Model: {config.agent_model}")
        st.caption("Code examples run in an offline Python container when needed.")
        st.caption("New conversations and server restarts clear conversation memory.")

st.caption("COREWEAVING / WEAVE DOCUMENTATION")
st.title("Good answers leave a trail.")
st.write("Ask about Weave. See the answer, its sources, and how it was checked.")
st.caption(
    "This demo records conversations in a public Weave project. "
    "Use public examples and keep credentials out of chat."
)
if not st.session_state.turns:
    # An inline welcome field avoids the pinned chat layout scrolling a narrow
    # first screen past its heading. Conversation input stays pinned below.
    with st.container(key="welcome_input"):
        question = st.chat_input("Ask about Weave…", key="welcome_question")
else:
    question = st.chat_input("Ask about Weave…", key="conversation_question")

starter_area = st.empty()
if not st.session_state.turns:
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
if question:
    starter_area.empty()
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.status("Finding and checking evidence…", expanded=True) as progress:

            def update(event):
                stage = event["stage"]
                if stage == "thinking":
                    st.write(event["detail"])
                elif stage in ("search_docs", "read_page", "run_python"):
                    detail = event["detail"]
                    if stage == "search_docs":
                        st.write(f"Searching: {detail.get('query', '')}")
                    elif stage == "read_page":
                        page = corpus.pages.get(detail.get("page_id"))
                        st.write(f"Reading: {page[0].title if page else 'a documentation page'}")
                    else:
                        st.write("Trying a small Python example in the offline container.")
                elif stage == "verification":
                    st.write(
                        "Source check passed."
                        if event["detail"]["passed"]
                        else "Draft needs revision; returning feedback to the agent."
                    )

            result = Agent(corpus, config).run(question, st.session_state.session, update)
            progress.update(
                label="Answer checked"
                if result["verification"]["passed"]
                else "Turn finished with a limitation",
                state="complete",
                expanded=False,
            )
        show_result(result)
    st.session_state.turns.append((question, result))
    weave_client.flush()
    st.rerun()
