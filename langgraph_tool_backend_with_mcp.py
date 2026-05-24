from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
import aiosqlite
import os
import requests
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()
print("TOKEN:", os.getenv('MCP_API_KEY'))

# -------------------
# 1. LLM
# -------------------
llm = ChatGroq(model_name="meta-llama/llama-4-scout-17b-16e-instruct", streaming=True)

# -------------------
# 2. Tools
# -------------------
search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """Perform a basic arithmetic operation. Supported: add, sub, mul, div"""
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}

@tool
def get_stock_price(symbol: str) -> dict:
    """Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA')"""
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=Y7O7K95G4BWQBP8G"
    r = requests.get(url)
    return r.json()

tools = [search_tool, get_stock_price, calculator]

# -------------------
# 3. State
# -------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# -------------------
# 4. MCP Client
# -------------------
mcp_client = MultiServerMCPClient({
    "company": {
        "transport": "streamable_http",
        "url": "https://InfinityCodehubLtd.fastmcp.app/mcp",
        "headers": {
            "Authorization": f"Bearer {os.getenv('MCP_API_KEY')}"
        }
    }
})

async def build_graph():
    # -------------------
    # 5. Load MCP Tools
    # -------------------
    try:
        tools2 = await mcp_client.get_tools()
        print("MCP Tools loaded:", [t.name for t in tools2])
    except Exception as e:
        print(f"[MCP] Could not load tools: {e}")
        tools2 = []

    all_tools = tools + tools2
    llm_with_tools = llm.bind_tools(all_tools)

    # Build name→tool lookup for type coercion
    tools_by_name = {t.name: t for t in all_tools}

    def _coerce_tool_args(tool_call: dict) -> dict:
        """Fix string→int/float mismatches the LLM produces for integer schema fields."""
        t = tools_by_name.get(tool_call["name"])
        if t is None:
            return tool_call
        schema = getattr(t, "args_schema", None)
        if isinstance(schema, dict):
            props = schema.get("properties", {})
        elif schema is not None:
            props = schema.schema().get("properties", {})
        else:
            props = {}
        new_args = dict(tool_call["args"])
        for key, val in new_args.items():
            expected = props.get(key, {}).get("type")
            if expected == "integer" and isinstance(val, str):
                try:
                    new_args[key] = int(val)
                except ValueError:
                    pass
            elif expected == "number" and isinstance(val, str):
                try:
                    new_args[key] = float(val)
                except ValueError:
                    pass
        return {**tool_call, "args": new_args}

    system_message = SystemMessage(content=(
        "You are a helpful assistant for InfinityCodehubLtd. "
        "You have access to company member data tools. "
        "Always use list_members tool to answer questions about members or workers. "
        "Never say you cannot access data — always use a tool instead."
    ))

    async def chat_node(state: ChatState):
        messages = [system_message] + state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        if response.tool_calls:
            fixed = [_coerce_tool_args(tc) for tc in response.tool_calls]
            response = response.model_copy(update={"tool_calls": fixed})
        return {"messages": [response]}

    tool_node = ToolNode(all_tools)

    # -------------------
    # 6. Checkpointer
    # -------------------
    conn = await aiosqlite.connect("chatbot.db")
    checkpointer = AsyncSqliteSaver(conn)

    # -------------------
    # 7. Graph
    # -------------------
    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")

    chatbot = graph.compile(checkpointer=checkpointer)

    async def retrieve_all_threads():
        all_threads = set()
        async for checkpoint in checkpointer.alist(None):
            all_threads.add(checkpoint.config["configurable"]["thread_id"])
        return list(all_threads)

    return chatbot, retrieve_all_threads