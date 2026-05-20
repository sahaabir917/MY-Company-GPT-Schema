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

import logging
import transformers
transformers.logging.set_verbosity_error()
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

import streamlit as st
import asyncio
import threading
import queue as _queue
from AgriagentBackend import build_graph
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid
import os
import base64
import tempfile

# Knowledge Base imports
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from groq import Groq

st.set_page_config(page_title="AgriAgent", layout="wide")

# Single persistent event loop in a background thread so the aiosqlite
# connection (created inside build_graph) stays valid across all calls.
_loop = asyncio.new_event_loop()
threading.Thread(target=_loop.run_forever, daemon=True).start()

def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, _loop).result()

chatbot, retrieve_all_threads = run_async(build_graph())

# =========================== Utilities ===========================
def generate_thread_id():
    return str(uuid.uuid4())

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

if "page" not in st.session_state:
    st.session_state["page"] = "Home"

add_thread(st.session_state["thread_id"])

# ============================ Top Navigation ============================
nav1, nav2, nav3, _ = st.columns([1, 1, 1, 7])

with nav1:
    if st.button("Home", use_container_width=True,
                 type="primary" if st.session_state["page"] == "Home" else "secondary"):
        st.session_state["page"] = "Home"
        st.rerun()

with nav2:
    if st.button("Knowledge Base", use_container_width=True,
                 type="primary" if st.session_state["page"] == "Knowledge Base" else "secondary"):
        st.session_state["page"] = "Knowledge Base"
        st.rerun()

with nav3:
    if st.button("Chat", use_container_width=True,
                 type="primary" if st.session_state["page"] == "Chat" else "secondary"):
        st.session_state["page"] = "Chat"
        st.rerun()

st.divider()

# ============================ Home Page ============================
if st.session_state["page"] == "Home":
    st.title("Welcome to AgriAgent")
    st.write("Your AI-powered agricultural assistant. Use the navigation above to get started.")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.info("**Chat**\n\nAsk questions, get crop advice, and interact with the AI assistant.")
    with col_b:
        st.info("**Knowledge Base**\n\nUpload documents, manuals, and reports to enrich the assistant's knowledge.")
    with col_c:
        st.info("**Tools**\n\nThe assistant can search the web, look up prices, and run calculations automatically.")

# ============================ Knowledge Base Page ============================
elif st.session_state["page"] == "Knowledge Base":
    st.title("Knowledge Base")
    st.write("Upload files and push them into Pinecone as vector embeddings.")

    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base_files")
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # ---- API key inputs in sidebar ----
    st.sidebar.header("API Keys")
    hf_api_key = st.sidebar.text_input("HuggingFace API Key", type="password",
                                        value="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",
                                        key="hf_key")
    groq_key   = st.sidebar.text_input("Groq API Key (for images/Excel)", type="password",
                                        key="groq_key")

    # ---- Helper functions ----
    def extract_text_from_file(file_path: str, fname: str, groq_client) -> list:
        ext = os.path.splitext(fname)[1].lower()

        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
            return loader.load()

        elif ext == ".txt" or ext == ".md":
            loader = TextLoader(file_path, encoding="utf-8")
            return loader.load()

        elif ext == ".docx":
            loader = Docx2txtLoader(file_path)
            return loader.load()

        elif ext in (".csv", ".xlsx", ".xls"):
            if ext == ".csv":
                loader = CSVLoader(file_path)
                return loader.load()
            else:
                # Excel — use Groq to summarise sheet content
                import pandas as pd
                df = pd.read_excel(file_path)
                table_text = df.to_string(index=False)
                prompt = f"Extract and summarise all useful information from this table:\n\n{table_text}"
                resp = groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": prompt}],
                )
                from langchain_core.documents import Document
                return [Document(page_content=resp.choices[0].message.content,
                                 metadata={"source": fname})]

        elif ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
            # Image — encode to base64 and send to Groq vision
            with open(file_path, "rb") as img_f:
                b64 = base64.b64encode(img_f.read()).decode("utf-8")
            mime = "image/jpeg" if ext in (".jpg", ".jpeg") else f"image/{ext.lstrip('.')}"
            resp = groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text",  "text": "Extract all text and describe all information visible in this image."},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                }],
            )
            from langchain_core.documents import Document
            return [Document(page_content=resp.choices[0].message.content,
                             metadata={"source": fname})]

        elif ext == ".json":
            import json
            with open(file_path, "r", encoding="utf-8") as jf:
                content = json.dumps(json.load(jf), indent=2)
            from langchain_core.documents import Document
            return [Document(page_content=content, metadata={"source": fname})]

        else:
            return []

    def split_documents(docs: list) -> list:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        return splitter.split_documents(docs)

    # ============================================================
    # MUST match AgriagentBackend.py exactly
    # ============================================================
    KB_PINECONE_KEY   = "pcsk_5XCys1_EEurSz1LLiLGLRk69utsQYLGWhEut89gVKDh65hoDUbDy1LzZxzucb9sUn91r27"
    KB_PINECONE_INDEX = "agriagent"
    KB_EMBED_MODEL    = "sentence-transformers/all-MiniLM-L6-v2"
    KB_EMBED_DIM      = 384

    def _ensure_kb_index():
        pc = Pinecone(api_key=KB_PINECONE_KEY)
        if KB_PINECONE_INDEX not in [i.name for i in pc.list_indexes()]:
            pc.create_index(
                name=KB_PINECONE_INDEX, dimension=KB_EMBED_DIM,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
        return pc.Index(KB_PINECONE_INDEX)

    def upload_chunks_to_pinecone(chunks: list, hf_key: str):
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = hf_key
        os.environ["PINECONE_API_KEY"]          = KB_PINECONE_KEY
        embeddings = HuggingFaceEmbeddings(model_name=KB_EMBED_MODEL)
        PineconeVectorStore.from_documents(
            chunks,
            embeddings,
            index_name=KB_PINECONE_INDEX,
            pinecone_api_key=KB_PINECONE_KEY,
        )

    # ---- File uploader — auto-saves on upload ----
    uploaded_files = st.file_uploader(
        "Upload files",
        accept_multiple_files=True,
        type=["pdf", "txt", "docx", "csv", "xlsx", "xls", "md", "json",
              "png", "jpg", "jpeg", "webp", "gif"],
        help="PDF, TXT, DOCX, CSV, Excel, Markdown, JSON, Images",
    )

    if uploaded_files:
        saved = []
        for f in uploaded_files:
            save_path = os.path.join(UPLOAD_DIR, f.name)
            with open(save_path, "wb") as out:
                out.write(f.read())
            saved.append(f.name)
        st.success(f"Saved {len(saved)} file(s): {', '.join(saved)}")

    # ---- Load to Pinecone button ----
    load_button = st.button("Load to Pinecone", key="load_button")

    if load_button:
        existing_files = os.listdir(UPLOAD_DIR)
        if not existing_files:
            st.warning("No files found. Upload files first.")
        else:
            groq_client = Groq(api_key=groq_key) if groq_key else None
            all_chunks  = []

            for fname in existing_files:
                file_path = os.path.join(UPLOAD_DIR, fname)
                st.write(f"Processing `{fname}`...")
                docs = extract_text_from_file(file_path, fname, groq_client)
                if not docs:
                    st.warning(f"  Skipped: `{fname}`")
                    continue
                st.write(f"  Extracted {len(docs)} page(s)")
                chunks = split_documents(docs)
                st.write(f"  Split into {len(chunks)} chunk(s)")
                all_chunks.extend(chunks)

            if all_chunks:
                st.write(f"Ensuring Pinecone index `{KB_PINECONE_INDEX}` exists...")
                _ensure_kb_index()
                st.write(f"Embedding {len(all_chunks)} chunks with `{KB_EMBED_MODEL}` and uploading...")
                upload_chunks_to_pinecone(all_chunks, hf_api_key)
                st.success(f"Done! {len(all_chunks)} chunks uploaded to Pinecone index `{KB_PINECONE_INDEX}`.")
            else:
                st.error("No text content found in uploaded files.")

    # ---- List saved files ----
    st.subheader("Saved Files")
    existing = os.listdir(UPLOAD_DIR)
    if existing:
        for fname in existing:
            col_name, col_del = st.columns([6, 1])
            col_name.write(fname)
            if col_del.button("Delete", key=f"del_{fname}"):
                os.remove(os.path.join(UPLOAD_DIR, fname))
                st.rerun()
    else:
        st.info("No files saved yet.")

# ============================ Chat Page ============================
elif st.session_state["page"] == "Chat":
    st.sidebar.title("Conversations")

    if st.sidebar.button("New Chat"):
        reset_chat()

    st.sidebar.header("History")
    for thread_id in st.session_state["chat_threads"][::-1]:
        label = str(thread_id)[:8] + "..."
        if st.sidebar.button(label, key=str(thread_id)):
            st.session_state["thread_id"] = thread_id
            messages = load_conversation(thread_id)
            temp_messages = []
            for msg in messages:
                if isinstance(msg, (HumanMessage, AIMessage)) and msg.content:
                    role = "user" if isinstance(msg, HumanMessage) else "assistant"
                    temp_messages.append({"role": role, "content": msg.content})
            st.session_state["message_history"] = temp_messages

    st.title("Chat")

    for message in st.session_state["message_history"]:
        with st.chat_message(message["role"]):
            st.text(message["content"])

    user_input = st.chat_input("Type here")

    if user_input:
        st.session_state["message_history"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.text(user_input)

        CONFIG = {
            "configurable": {"thread_id": st.session_state["thread_id"]},
            "metadata": {"thread_id": st.session_state["thread_id"]},
            "run_name": "chat_turn",
        }

        with st.chat_message("assistant"):
            status_holder = {"box": None}

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
                                        tool_name = getattr(msg, "name", "tool")
                                        q.put(("tool", tool_name))

                            if "chat_node" in update:
                                for msg in update["chat_node"].get("messages", []):
                                    if isinstance(msg, AIMessage) and msg.content:
                                        q.put(("text", msg.content))
                    except Exception as e:
                        q.put(("text", f"Error: {str(e)}"))

                    q.put(None)

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

            if status_holder["box"] is not None:
                status_holder["box"].update(
                    label="✅ Tool finished", state="complete", expanded=False
                )

        st.session_state["message_history"].append(
            {"role": "assistant", "content": ai_message}
        )