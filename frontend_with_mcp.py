
import streamlit as st
import asyncio
import threading
import queue as _queue
from langgraph_tool_backend_with_mcp import build_graph
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid

# Single persistent event loop in a background thread so the aiosqlite
# connection (created inside build_graph) stays valid across all calls.
_loop = asyncio.new_event_loop()
threading.Thread(target=_loop.run_forever, daemon=True).start()

def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, _loop).result()

# ✅ FIX: build_graph now returns chatbot and retrieve_all_threads
chatbot, retrieve_all_threads = run_async(build_graph())

# =========================== Utilities ===========================
def generate_thread_id():
    return str(uuid.uuid4())  # ✅ FIX: convert to string

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    add_thread(thread_id)
    st.session_state["message_history"] = []

def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)

def load_conversation(thread_id):
    state = run_async(chatbot.aget_state(config={"configurable": {"thread_id": thread_id}}))
    return state.values.get("messages", [])

# ======================= Session Initialization ===================
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = run_async(retrieve_all_threads())

add_thread(st.session_state["thread_id"])

# ============================ Sidebar ============================
st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")
for thread_id in st.session_state["chat_threads"][::-1]:
    label = str(thread_id)[:8] + "..."  # ✅ FIX: shorter label to avoid duplicates
    if st.sidebar.button(label, key=str(thread_id)):  # ✅ FIX: unique key
        st.session_state["thread_id"] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for msg in messages:
            # ✅ FIX: skip ToolMessages and empty messages
            if isinstance(msg, (HumanMessage, AIMessage)) and msg.content:
                role = "user" if isinstance(msg, HumanMessage) else "assistant"
                temp_messages.append({"role": role, "content": msg.content})
        st.session_state["message_history"] = temp_messages

# ============================ Main UI ============================

# Render history
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.text(message["content"])

user_input = st.chat_input("Type here")

if user_input:
    # Show user's message
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.text(user_input)

    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {"thread_id": st.session_state["thread_id"]},
        "run_name": "chat_turn",
    }

    # Assistant streaming block
    with st.chat_message("assistant"):
        status_holder = {"box": None}

        def ai_only_stream():
            q = _queue.Queue()

            async def _run():
                try:  # ✅ FIX: added error handling
                    async for update in chatbot.astream(
                        {"messages": [HumanMessage(content=user_input)]},
                        config=CONFIG,
                        stream_mode="updates",
                    ):
                        if "tools" in update:
                            for msg in update["tools"].get("messages", []):
                                if isinstance(msg, ToolMessage):
                                    tool_name = getattr(msg, "name", "tool")
                                    q.put(("tool", tool_name))

                        if "chat_node" in update:
                            for msg in update["chat_node"].get("messages", []):
                                if isinstance(msg, AIMessage) and msg.content:
                                    q.put(("text", msg.content))
                except Exception as e:
                    q.put(("text", f"Error: {str(e)}"))

                q.put(None)  # sentinel — stream finished

            asyncio.run_coroutine_threadsafe(_run(), _loop)

            while True:
                item = q.get()
                if item is None:
                    break
                kind, value = item
                if kind == "tool":
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{value}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{value}` …",
                            state="running",
                            expanded=True,
                        )
                else:
                    yield value

        ai_message = st.write_stream(ai_only_stream())

        # Finalize only if a tool was actually used
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )

    # Save assistant message
    st.session_state["message_history"].append(
        {"role": "assistant", "content": ai_message}
    )