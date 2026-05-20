# from langgraph.graph import StateGraph, START, END
# from typing import TypedDict, Annotated
# from langchain_core.messages import BaseMessage, HumanMessage
# from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
# from langgraph.graph.message import add_messages
# from langgraph.prebuilt import ToolNode, tools_condition
# from langchain_community.tools import DuckDuckGoSearchRun
# from langchain_core.tools import tool
# from langchain_groq import ChatGroq
# from dotenv import load_dotenv
# from langchain_core.messages import SystemMessage
# import aiosqlite
# import os
# import requests
# from langchain_mcp_adapters.client import MultiServerMCPClient

# load_dotenv()
# print("TOKEN:", os.getenv('MCP_API_KEY'))



# # -------------------
# # 1. LLM
# # -------------------
# # llm = ChatOpenAI()
# llm = ChatGroq(model_name="meta-llama/llama-4-scout-17b-16e-instruct", streaming=True)
# # -------------------
# # 2. Tools
# # -------------------
# # Tools
# search_tool = DuckDuckGoSearchRun(region="us-en")

# @tool
# def calculator(first_num: float, second_num: float, operation: str) -> dict:
#     """
#     Perform a basic arithmetic operation on two numbers.
#     Supported operations: add, sub, mul, div
#     """
#     try:
#         if operation == "add":
#             result = first_num + second_num
#         elif operation == "sub":
#             result = first_num - second_num
#         elif operation == "mul":
#             result = first_num * second_num
#         elif operation == "div":
#             if second_num == 0:
#                 return {"error": "Division by zero is not allowed"}
#             result = first_num / second_num
#         else:
#             return {"error": f"Unsupported operation '{operation}'"}
        
#         return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
#     except Exception as e:
#         return {"error": str(e)}




# @tool
# def get_stock_price(symbol: str) -> dict:
#     """
#     Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
#     using Alpha Vantage with API key in the URL.
#     """
#     url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=Y7O7K95G4BWQBP8G"
#     r = requests.get(url)
#     return r.json()



# tools = [search_tool, get_stock_price, calculator]
# # -------------------
# # 3. State
# # -------------------
# class ChatState(TypedDict):
#     messages: Annotated[list[BaseMessage], add_messages]

# async def build_graph():

#     async def test_mcp():
#         client = MultiServerMCPClient({
#             "company": {
#                 "transport": "streamable_http",
#                 "url": "https://InfinityCodehubLtd.fastmcp.app/mcp",
#                 "headers": {
#                     "Authorization": f"Bearer {os.getenv('MCP_API_KEY')}"
#                 }
#             }
#         })

#     try:
#         client = MultiServerMCPClient({
#             "company": {
#                 "transport": "streamable_http",
#                 "url": "https://InfinityCodehubLtd.fastmcp.app/mcp",
#                 "headers": {"Authorization": f"Bearer {os.getenv('MCP_API_KEY')}"}
#             }
#         })
#         tools2 = await client.get_tools()
#     except Exception as e:
#         print(f"[MCP] Could not load tools: {e}")
#         tools2 = []
#     all_tools = tools + tools2
#     llm_with_tools = llm.bind_tools(all_tools)

#     system_message = SystemMessage(content=(
#         "You are a helpful assistant with access to tools. "
#         "Always use the available tools to answer questions about members, stock prices, calculations, or web searches. "
#         "Never say you cannot access data — use a tool instead."
#     ))

#     async def chat_node(state: ChatState):
#         """LLM node that may answer or request a tool call."""
#         messages = [system_message] + state["messages"]
#         response = await llm_with_tools.ainvoke(messages)
#         return {"messages": [response]}

#     tool_node = ToolNode(all_tools)

#     # -------------------
#     # 5. Checkpointer
#     # -------------------
#     conn = await aiosqlite.connect("chatbot.db")
#     checkpointer = AsyncSqliteSaver(conn)

#     # -------------------
#     # 6. Graph
#     # -------------------
#     graph = StateGraph(ChatState)
#     graph.add_node("chat_node", chat_node)
#     graph.add_node("tools", tool_node)

#     graph.add_edge(START, "chat_node")

#     graph.add_conditional_edges("chat_node", tools_condition)
#     graph.add_edge("tools", "chat_node")

#     chatbot = graph.compile(checkpointer=checkpointer)

#     # -------------------
#     # 7. Helper
#     # -------------------
#     async def retrieve_all_threads():
#         all_threads = set()
#         async for checkpoint in checkpointer.alist(None):
#             all_threads.add(checkpoint.config["configurable"]["thread_id"])
#         return list(all_threads)

#     return chatbot, retrieve_all_threads



import logging
import transformers
transformers.logging.set_verbosity_error()
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec
import aiosqlite
import os
import requests
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

# =============================================================
# SINGLE SOURCE OF TRUTH — same values used for upload & query
# =============================================================
PINECONE_API_KEY  = "pcsk_5XCys1_EEurSz1LLiLGLRk69utsQYLGWhEut89gVKDh65hoDUbDy1LzZxzucb9sUn91r27"
PINECONE_INDEX    = "agriagent"
EMBED_MODEL       = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM         = 384
HF_API_KEY        = "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"

os.environ["PINECONE_API_KEY"]         = PINECONE_API_KEY
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HF_API_KEY

# Load embedding model once at startup
print(f"[RAG] Loading embedding model: {EMBED_MODEL}")
_embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
print("[RAG] Embedding model ready ✓")

# Ensure Pinecone index exists
def _ensure_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    existing = [i.name for i in pc.list_indexes()]
    if PINECONE_INDEX not in existing:
        print(f"[RAG] Creating Pinecone index '{PINECONE_INDEX}' dim={EMBED_DIM}")
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"[RAG] Index '{PINECONE_INDEX}' created ✓")
    else:
        print(f"[RAG] Index '{PINECONE_INDEX}' exists ✓")

_ensure_index()

# -------------------
# LLM
# -------------------
llm = ChatGroq(model_name="meta-llama/llama-4-scout-17b-16e-instruct", streaming=True)

# -------------------
# RAG Tool
# -------------------
@tool
def query_knowledge_base(query: str) -> str:
    """
    Search the Pinecone 'agriagent' knowledge base using cosine similarity.
    ALWAYS call this tool first for every user question.
    Embeds the query → cosine similarity search → returns the 5 most relevant chunks.
    """
    try:
        # Step 1: embed the query with the same model used during upload
        query_vector = _embeddings.embed_query(query)
        print(f"[RAG] Query embedded, dim={len(query_vector)}")

        # Step 2: cosine similarity search in Pinecone
        pc     = Pinecone(api_key=PINECONE_API_KEY)
        index  = pc.Index(PINECONE_INDEX)
        result = index.query(vector=query_vector, top_k=5, include_metadata=True)

        # Pinecone SDK returns an object — use .matches not .get()
        matches = result.matches
        print(f"[RAG] Pinecone returned {len(matches)} matches")

        if not matches:
            return "No relevant information found in the knowledge base."

        # Step 3: extract text from metadata
        # langchain_pinecone stores page_content under metadata['text']
        chunks = []
        for i, m in enumerate(matches, 1):
            meta   = m.metadata or {}
            text   = meta.get("text", "") or meta.get("page_content", "")
            source = meta.get("source", "unknown")
            score  = round(m.score, 4)
            print(f"[RAG]   Chunk {i}: score={score}, chars={len(text)}, source={source}")
            if text.strip():
                chunks.append(
                    f"[Chunk {i} | source: {source} | cosine score: {score}]\n{text.strip()}"
                )

        if not chunks:
            return (
                "Pinecone found vector matches but no text in metadata. "
                "Please re-upload your documents from the Knowledge Base page."
            )

        return "\n\n".join(chunks)

    except Exception as e:
        print(f"[RAG] ERROR: {e}")
        return f"Knowledge base query failed: {e}"

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """Perform arithmetic. Supported operations: add, sub, mul, div."""
    try:
        ops = {"add": first_num + second_num, "sub": first_num - second_num,
               "mul": first_num * second_num}
        if operation in ops:
            return {"result": ops[operation]}
        if operation == "div":
            if second_num == 0:
                return {"error": "Division by zero"}
            return {"result": first_num / second_num}
        return {"error": f"Unknown operation: {operation}"}
    except Exception as e:
        return {"error": str(e)}

@tool
def get_stock_price(symbol: str) -> dict:
    """Get latest stock or commodity price for a symbol like AAPL or CORN."""
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=Y7O7K95G4BWQBP8G"
    return requests.get(url).json()

tools = [query_knowledge_base, calculator, get_stock_price]

# -------------------
# State
# -------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# -------------------
# MCP Client
# -------------------
mcp_client = MultiServerMCPClient({
    "company": {
        "transport": "streamable_http",
        "url": "https://InfinityCodehubLtd.fastmcp.app/mcp",
        "headers": {"Authorization": f"Bearer {os.getenv('MCP_API_KEY')}"}
    }
})

async def build_graph():
    try:
        tools2 = await mcp_client.get_tools()
        print("MCP Tools loaded:", [t.name for t in tools2])
    except Exception as e:
        print(f"[MCP] Could not load: {e}")
        tools2 = []

    all_tools = tools + tools2
    llm_with_tools = llm.bind_tools(all_tools)

    system_message = SystemMessage(content=(
        "You are AgriAgent, an expert agricultural AI assistant.\n"
        "MANDATORY RULE: For EVERY question you receive, you MUST call the "
        "`query_knowledge_base` tool first — no exceptions.\n"
        "After receiving the chunks from the tool, compose a clear answer "
        "based strictly on those chunks.\n"
        "Only use `calculator` for math. Only use `get_stock_price` for prices.\n"
        "Never answer from your own memory — always use `query_knowledge_base` first."
    ))

    async def chat_node(state: ChatState):
        messages = [system_message] + state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    tool_node  = ToolNode(all_tools)
    conn       = await aiosqlite.connect("chatbot.db")
    checkpointer = AsyncSqliteSaver(conn)

    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools",     tool_node)
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")
    chatbot = graph.compile(checkpointer=checkpointer)

    async def retrieve_all_threads():
        threads = set()
        async for cp in checkpointer.alist(None):
            threads.add(cp.config["configurable"]["thread_id"])
        return list(threads)

    return chatbot, retrieve_all_threads