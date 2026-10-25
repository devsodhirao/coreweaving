"""A small interface that shows both the answer and the evidence behind it."""

import streamlit as st

from coreweaving.agent import Agent, Session
from coreweaving.config import init_weave, settings
from coreweaving.corpus import Corpus

st.set_page_config(page_title="Coreweaving · Ask the docs", page_icon="◉", layout="wide")
st.markdown(
    """<style>
.stApp {background:#f6f4ee} .block-container {max-width:1150px;padding-top:3rem}
h1 {font-family:Georgia,serif;font-weight:500;letter-spacing:-1.5px}
[data-testid=stSidebar] {background:#e9efea}
[data-testid=stChatMessage] {border:1px solid #dce4dd;border-radius:14px;background:#fffefa}
</style>""",
    unsafe_allow_html=True,
)


@st.cache_resource
def resources():
    return Corpus(), init_weave()


def show_result(result):
    st.markdown(result["answer"])
    passed = result["verification"]["passed"]
    st.caption(
        f"{'Source check passed' if passed else 'Source check did not pass'} · "
        f"{result['elapsed_seconds']:.1f}s · {len(result['actions'])} tool calls"
    )
    st.link_button("Inspect this conversation in Weave ↗", result["trace_url"])
    if result["sources"]:
        with st.expander(f"Source passages ({len(result['sources'])})"):
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
    st.write("Ask a question. Follow the evidence.")
    if st.button("New conversation", use_container_width=True):
        st.session_state.session = Session()
        st.session_state.turns = []
        st.rerun()
    st.caption(f"{len(corpus.pages)} documentation pages · snapshot {corpus.snapshot_id[:12]}")
    st.caption(f"Model: {config.agent_model}")
    st.markdown("Try a follow-up such as **‘And how would I monitor that?’**")
    st.caption(
        "Questions, answers, and source passages are recorded in this public Weave project. "
        "Use public examples; keep credentials out of chat."
    )
    st.caption("A source check is useful evidence, not a guarantee of correctness.")

st.caption("WEAVE DOCUMENTATION / AN ASSISTANT YOU CAN INSPECT")
st.title("Good answers leave a trail.")
st.write("Explore the docs with an assistant that searches, reads, and checks its answer.")
if not st.session_state.turns:
    examples = [
        "How do I trace a custom multi-turn agent and add a Signal?",
        "Does adding @weave.op automatically put my agent in the Agents view?",
        "Can Signals guarantee that my agent never hallucinates?",
    ]
    columns = st.columns(3)
    for column, example in zip(columns, examples):
        if column.button(example, use_container_width=True):
            st.session_state.pending_question = example

for question, result in st.session_state.turns:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        show_result(result)

question = st.chat_input("Ask about Weave…") or st.session_state.pop("pending_question", None)
if question:
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
                    st.write(
                        f"{stage}: {detail.get('query', detail.get('page_id', 'offline example'))}"
                    )
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
