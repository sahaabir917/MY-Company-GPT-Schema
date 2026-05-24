# import streamlit as st
# import asyncio
# import threading
# import queue as _queue
# from langgraph_tool_backend_with_mcp import build_graph
# from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
# import uuid

# # Single persistent event loop in a background thread so the aiosqlite
# # connection (created inside build_graph) stays valid across all calls.
# _loop = asyncio.new_event_loop()
# threading.Thread(target=_loop.run_forever, daemon=True).start()

# def run_async(coro):
#     return asyncio.run_coroutine_threadsafe(coro, _loop).result()

# chatbot, retrieve_all_threads = run_async(build_graph())

# # =========================== Utilities ===========================
# def generate_thread_id():
#     return uuid.uuid4()

# def reset_chat():
#     thread_id = generate_thread_id()
#     st.session_state["thread_id"] = thread_id
#     add_thread(thread_id)
#     st.session_state["message_history"] = []

# def add_thread(thread_id):
#     if thread_id not in st.session_state["chat_threads"]:
#         st.session_state["chat_threads"].append(thread_id)

# def load_conversation(thread_id):
#     state = run_async(chatbot.aget_state(config={"configurable": {"thread_id": thread_id}}))
#     return state.values.get("messages", [])

# # ======================= Session Initialization ===================
# if "message_history" not in st.session_state:
#     st.session_state["message_history"] = []

# if "thread_id" not in st.session_state:
#     st.session_state["thread_id"] = generate_thread_id()

# if "chat_threads" not in st.session_state:
#     st.session_state["chat_threads"] = run_async(retrieve_all_threads())

# add_thread(st.session_state["thread_id"])

# # ============================ Sidebar ============================
# st.sidebar.title("LangGraph Chatbot")

# if st.sidebar.button("New Chat"):
#     reset_chat()

# st.sidebar.header("My Conversations")
# for thread_id in st.session_state["chat_threads"][::-1]:
#     if st.sidebar.button(str(thread_id)):
#         st.session_state["thread_id"] = thread_id
#         messages = load_conversation(thread_id)

#         temp_messages = []
#         for msg in messages:
#             role = "user" if isinstance(msg, HumanMessage) else "assistant"
#             temp_messages.append({"role": role, "content": msg.content})
#         st.session_state["message_history"] = temp_messages

# # ============================ Main UI ============================

# # Render history
# for message in st.session_state["message_history"]:
#     with st.chat_message(message["role"]):
#         st.text(message["content"])

# user_input = st.chat_input("Type here")

# if user_input:
#     # Show user's message
#     st.session_state["message_history"].append({"role": "user", "content": user_input})
#     with st.chat_message("user"):
#         st.text(user_input)

#     CONFIG = {
#         "configurable": {"thread_id": st.session_state["thread_id"]},
#         "metadata": {"thread_id": st.session_state["thread_id"]},
#         "run_name": "chat_turn",
#     }

#     # Assistant streaming block
#     with st.chat_message("assistant"):
#         status_holder = {"box": None}

#         def ai_only_stream():
#             q = _queue.Queue()

#             async def _run():
#                 async for update in chatbot.astream(
#                     {"messages": [HumanMessage(content=user_input)]},
#                     config=CONFIG,
#                     stream_mode="updates",
#                 ):
#                     if "tools" in update:
#                         for msg in update["tools"].get("messages", []):
#                             if isinstance(msg, ToolMessage):
#                                 tool_name = getattr(msg, "name", "tool")
#                                 q.put(("tool", tool_name))

#                     if "chat_node" in update:
#                         for msg in update["chat_node"].get("messages", []):
#                             if isinstance(msg, AIMessage) and msg.content:
#                                 q.put(("text", msg.content))

#                 q.put(None)  # sentinel — stream finished

#             asyncio.run_coroutine_threadsafe(_run(), _loop)

#             while True:
#                 item = q.get()
#                 if item is None:
#                     break
#                 kind, value = item
#                 if kind == "tool":
#                     if status_holder["box"] is None:
#                         status_holder["box"] = st.status(
#                             f"🔧 Using `{value}` …", expanded=True
#                         )
#                     else:
#                         status_holder["box"].update(
#                             label=f"🔧 Using `{value}` …",
#                             state="running",
#                             expanded=True,
#                         )
#                 else:
#                     yield value

#         ai_message = st.write_stream(ai_only_stream())

#         # Finalize only if a tool was actually used
#         if status_holder["box"] is not None:
#             status_holder["box"].update(
#                 label="✅ Tool finished", state="complete", expanded=False
#             )

#     # Save assistant message
#     st.session_state["message_history"].append(
#         {"role": "assistant", "content": ai_message}
#     )


# ________________________________________
# import streamlit as st
# import asyncio
# import threading
# import queue as _queue
# from langgraph_tool_backend_with_mcp import build_graph, mcp_client
# from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
# import uuid

# # Single persistent event loop
# _loop = asyncio.new_event_loop()
# threading.Thread(target=_loop.run_forever, daemon=True).start()

# def run_async(coro):
#     return asyncio.run_coroutine_threadsafe(coro, _loop).result()

# # -------------------
# # Build graph — no context manager
# # -------------------
# async def init():
#     chatbot, retrieve_all_threads = await build_graph()
#     threads = await retrieve_all_threads()
#     return chatbot, retrieve_all_threads, threads

# chatbot, retrieve_all_threads, initial_threads = run_async(init())

# # =========================== Utilities ===========================
# def generate_thread_id():
#     return str(uuid.uuid4())

# def reset_chat():
#     thread_id = generate_thread_id()
#     st.session_state["thread_id"] = thread_id
#     add_thread(thread_id)
#     st.session_state["message_history"] = []

# def add_thread(thread_id):
#     if thread_id not in st.session_state["chat_threads"]:
#         st.session_state["chat_threads"].append(thread_id)

# def load_conversation(thread_id):
#     state = run_async(
#         chatbot.aget_state(
#             config={"configurable": {"thread_id": thread_id}}
#         )
#     )
#     return state.values.get("messages", [])

# # ======================= Session Initialization ===================
# if "message_history" not in st.session_state:
#     st.session_state["message_history"] = []

# if "thread_id" not in st.session_state:
#     st.session_state["thread_id"] = generate_thread_id()

# if "chat_threads" not in st.session_state:
#     st.session_state["chat_threads"] = initial_threads

# add_thread(st.session_state["thread_id"])

# # ============================ Sidebar ============================
# st.sidebar.title("LangGraph Chatbot")

# if st.sidebar.button("New Chat"):
#     reset_chat()

# st.sidebar.header("My Conversations")
# for thread_id in st.session_state["chat_threads"][::-1]:
#     label = str(thread_id)[:8] + "..."
#     if st.sidebar.button(label, key=str(thread_id)):
#         st.session_state["thread_id"] = thread_id
#         messages = load_conversation(thread_id)
#         temp_messages = []
#         for msg in messages:
#             if isinstance(msg, (HumanMessage, AIMessage)) and msg.content:
#                 role = "user" if isinstance(msg, HumanMessage) else "assistant"
#                 temp_messages.append({"role": role, "content": msg.content})
#         st.session_state["message_history"] = temp_messages

# # ============================ Main UI ============================
# st.title("InfinityCodehubLtd Assistant")

# for message in st.session_state["message_history"]:
#     with st.chat_message(message["role"]):
#         st.write(message["content"])

# user_input = st.chat_input("Type here")

# if user_input:
#     st.session_state["message_history"].append({
#         "role": "user", "content": user_input
#     })
#     with st.chat_message("user"):
#         st.write(user_input)

#     CONFIG = {
#         "configurable": {"thread_id": st.session_state["thread_id"]},
#         "metadata": {"thread_id": st.session_state["thread_id"]},
#         "run_name": "chat_turn",
#     }

#     with st.chat_message("assistant"):
#         status_holder = {"box": None}

#         def ai_only_stream():
#             q = _queue.Queue()

#             async def _run():
#                 try:
#                     async for update in chatbot.astream(
#                         {"messages": [HumanMessage(content=user_input)]},
#                         config=CONFIG,
#                         stream_mode="updates",
#                     ):
#                         if "tools" in update:
#                             for msg in update["tools"].get("messages", []):
#                                 if isinstance(msg, ToolMessage):
#                                     tool_name = getattr(msg, "name", "tool")
#                                     q.put(("tool", tool_name))

#                         if "chat_node" in update:
#                             for msg in update["chat_node"].get("messages", []):
#                                 if isinstance(msg, AIMessage) and msg.content:
#                                     q.put(("text", msg.content))
#                 except Exception as e:
#                     q.put(("text", f"Error: {str(e)}"))

#                 q.put(None)

#             asyncio.run_coroutine_threadsafe(_run(), _loop)

#             while True:
#                 item = q.get()
#                 if item is None:
#                     break
#                 kind, value = item
#                 if kind == "tool":
#                     if status_holder["box"] is None:
#                         status_holder["box"] = st.status(
#                             f"🔧 Using `{value}` …", expanded=True
#                         )
#                     else:
#                         status_holder["box"].update(
#                             label=f"🔧 Using `{value}` …",
#                             state="running",
#                             expanded=True,
#                         )
#                 else:
#                     yield value

#         ai_message = st.write_stream(ai_only_stream())

#         if status_holder["box"] is not None:
#             status_holder["box"].update(
#                 label="✅ Tool finished",
#                 state="complete",
#                 expanded=False
#             )

#     st.session_state["message_history"].append({
#         "role": "assistant", "content": ai_message
#     })
# ________________________________________

import streamlit as st
import asyncio
import threading
import queue as _queue
from langgraph_tool_backend_with_mcp import build_graph
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background: #f5f7fb !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem !important; max-width: 1000px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #111827 !important;
    border-right: 1px solid #1f2937 !important;
}
[data-testid="stSidebar"] * { color: #d1d5db !important; }
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    text-align: left !important;
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #9ca3af !important;
    font-size: 0.82rem !important;
    padding: 0.5rem 0.8rem !important;
    margin-bottom: 4px !important;
    transition: all 0.15s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99,102,241,0.15) !important;
    border-color: rgba(99,102,241,0.4) !important;
    color: #a5b4fc !important;
}

/* ── User chat bubble (right side, indigo/purple) ── */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(135deg, #4f46e5, #6d28d9) !important;
    border-radius: 18px 18px 4px 18px !important;
    margin-left: 14% !important;
    margin-right: 0 !important;
    border: none !important;
    box-shadow: 0 4px 18px rgba(79,70,229,0.3) !important;
    padding: 14px 18px !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) * {
    color: #ede9fe !important;
}

/* ── Assistant chat bubble (left side, white card) ── */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: #ffffff !important;
    border-radius: 4px 18px 18px 18px !important;
    margin-right: 14% !important;
    margin-left: 0 !important;
    border: none !important;
    border-left: 3px solid #6366f1 !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.07) !important;
    padding: 14px 18px !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) * {
    color: #111827 !important;
}

/* markdown inside assistant message */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) p {
    line-height: 1.65 !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) code {
    background: #f3f4f6 !important;
    border-radius: 4px !important;
    padding: 1px 5px !important;
    font-size: 0.88em !important;
    color: #4f46e5 !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) pre {
    background: #1f2937 !important;
    border-radius: 8px !important;
    padding: 1rem !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) pre code {
    background: transparent !important;
    color: #e5e7eb !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] textarea {
    background: #fff !important;
    border: 1.5px solid #e0e4f0 !important;
    border-radius: 14px !important;
    font-size: 0.95rem !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

/* ── Status / tool indicator ── */
[data-testid="stStatus"] {
    border-radius: 10px !important;
    border: 1px solid #c7d2fe !important;
    background: #eef2ff !important;
    font-size: 0.84rem !important;
    color: #4338ca !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #f5f7fb; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #6366f1; }

/* ── Divider ── */
hr { border-color: #e5e7eb !important; margin: 1rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# EVENT LOOP — cached so reruns don't create a new loop (bug fix)
# ─────────────────────────────────────────────────────────────────
@st.cache_resource
def _get_loop():
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    return loop

_loop = _get_loop()

def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, _loop).result()

@st.cache_resource
def get_chatbot():
    return run_async(build_graph())

chatbot, retrieve_all_threads = get_chatbot()

# ─────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────
def generate_thread_id():
    return str(uuid.uuid4())

def reset_chat():
    tid = generate_thread_id()
    st.session_state["thread_id"] = tid
    _add_thread(tid)
    st.session_state["message_history"] = []

def _add_thread(tid):
    if tid not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(tid)

def load_conversation(tid):
    state = run_async(chatbot.aget_state(config={"configurable": {"thread_id": tid}}))
    result = []
    for msg in state.values.get("messages", []):
        if isinstance(msg, (HumanMessage, AIMessage)) and msg.content:
            result.append({
                "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                "content": msg.content,
            })
    return result

# ─────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()
if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = run_async(retrieve_all_threads())

_add_thread(st.session_state["thread_id"])

# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 8px 4px 16px 4px;'>
        <div style='font-size:1.3rem; font-weight:700; color:#818cf8; letter-spacing:-0.5px;'>
            🤖 AI Assistant
        </div>
        <div style='font-size:0.75rem; color:#6b7280; margin-top:2px;'>
            Powered by LangGraph + MCP
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("＋  New Chat", use_container_width=True):
        reset_chat()
        st.rerun()

    st.markdown("<hr style='border-color:#1f2937; margin:12px 0;'>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em;"
        "color:#4b5563; margin-bottom:8px; padding-left:2px;'>Conversations</div>",
        unsafe_allow_html=True,
    )

    for tid in st.session_state["chat_threads"][::-1]:
        is_active = tid == st.session_state["thread_id"]
        label = ("▶  " if is_active else "💬  ") + str(tid)[:10] + "…"
        if st.button(label, key=f"t_{tid}"):
            st.session_state["thread_id"] = tid
            st.session_state["message_history"] = load_conversation(tid)
            st.rerun()

# ─────────────────────────────────────────────────────────────────
# MAIN CHAT AREA — header
# ─────────────────────────────────────────────────────────────────
col_title, col_badge = st.columns([5, 1])
with col_title:
    st.markdown(
        "<h2 style='margin:0; color:#111827; font-size:1.5rem; font-weight:700;'>"
        "Chat with AI Assistant</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='margin:2px 0 16px; color:#6b7280; font-size:0.84rem;'>"
        "Ask me anything — I can search, calculate, and reason.</p>",
        unsafe_allow_html=True,
    )
with col_badge:
    thread_short = str(st.session_state["thread_id"])[:6]
    st.markdown(
        f"<div style='margin-top:8px; text-align:right;'>"
        f"<span style='background:#eef2ff; color:#4f46e5; font-size:0.72rem;"
        f"font-weight:600; padding:3px 10px; border-radius:20px; letter-spacing:0.05em;'>"
        f"#{thread_short}</span></div>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────────────────────────
if not st.session_state["message_history"]:
    st.markdown("""
    <div style='text-align:center; padding:3rem 2rem; background:#fff;
                border-radius:18px; border:1.5px dashed #e0e4f0; margin:0.5rem 0 1.5rem;'>
        <div style='font-size:3rem; margin-bottom:0.8rem;'>💬</div>
        <div style='font-size:1.15rem; font-weight:600; color:#111827; margin-bottom:0.4rem;'>
            Start a conversation
        </div>
        <div style='font-size:0.85rem; color:#6b7280; max-width:360px;
                    margin:0 auto; line-height:1.6;'>
            Ask me to search the web, calculate something, look up stock prices,
            or just chat about any topic.
        </div>
    </div>
    <div style='display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:1.5rem;'>
        <div style='background:#fff; border:1px solid #e0e4f0; border-left:3px solid #6366f1;
                    border-radius:10px; padding:10px 14px; font-size:0.84rem; color:#374151;'>
            💹 "What is the current stock price of AAPL?"
        </div>
        <div style='background:#fff; border:1px solid #e0e4f0; border-left:3px solid #6366f1;
                    border-radius:10px; padding:10px 14px; font-size:0.84rem; color:#374151;'>
            🔍 "Search for the latest AI news"
        </div>
        <div style='background:#fff; border:1px solid #e0e4f0; border-left:3px solid #6366f1;
                    border-radius:10px; padding:10px 14px; font-size:0.84rem; color:#374151;'>
            🧮 "What is 15% of 47,500?"
        </div>
        <div style='background:#fff; border:1px solid #e0e4f0; border-left:3px solid #6366f1;
                    border-radius:10px; padding:10px 14px; font-size:0.84rem; color:#374151;'>
            🌍 "Tell me about climate change trends"
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# MESSAGE HISTORY
# ─────────────────────────────────────────────────────────────────
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ─────────────────────────────────────────────────────────────────
# CHAT INPUT + STREAMING
# ─────────────────────────────────────────────────────────────────
user_input = st.chat_input("Message AI Assistant…")

if user_input:
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata":     {"thread_id": st.session_state["thread_id"]},
        "run_name":     "chat_turn",
    }

    with st.chat_message("assistant"):
        status_holder = {"box": None, "count": 0}

        def ai_only_stream():
            q = _queue.Queue()

            async def _run():
                try:
                    async for update in chatbot.astream(
                        {"messages": [HumanMessage(content=user_input)]},
                        config=CONFIG,
                        stream_mode="updates",
                    ):
                        if "tools" in update:
                            for msg in update["tools"].get("messages", []):
                                if isinstance(msg, ToolMessage):
                                    q.put(("tool", getattr(msg, "name", "tool")))

                        if "chat_node" in update:
                            for msg in update["chat_node"].get("messages", []):
                                if isinstance(msg, AIMessage) and msg.content:
                                    q.put(("text", msg.content))
                except Exception as e:
                    q.put(("text", f"⚠️ Error: {e}"))
                q.put(None)

            asyncio.run_coroutine_threadsafe(_run(), _loop)

            while True:
                item = q.get()
                if item is None:
                    break
                kind, value = item
                if kind == "tool":
                    status_holder["count"] += 1
                    n = status_holder["count"]
                    lbl = f"🔍 Running tool: `{value}`" + (f" (pass {n})" if n > 1 else "")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(lbl, expanded=True)
                    else:
                        status_holder["box"].update(label=lbl, state="running", expanded=True)
                else:
                    yield value

        ai_message = st.write_stream(ai_only_stream())

        if status_holder["box"] is not None:
            n = status_holder["count"]
            status_holder["box"].update(
                label=f"✅ Done — {n} tool call{'s' if n > 1 else ''}",
                state="complete",
                expanded=False,
            )

    st.session_state["message_history"].append(
        {"role": "assistant", "content": ai_message}
    )