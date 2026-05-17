# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
streamlit run streamlit_frontend_tool.py
```

Opens the chatbot UI at `http://localhost:8501`.

```bash
pip install -r requirements.txt
```

## Architecture

This is a two-file LangGraph + Streamlit chatbot with tool-calling capabilities.

**[langgraph_tool_backend.py](langgraph_tool_backend.py)** — defines the LangGraph state machine:
- `ChatState` holds `messages: List[BaseMessage]`
- `chat_node` binds the LLM (ChatOpenAI) to three tools: `DuckDuckGoSearchRun`, `get_stock_price` (Alpha Vantage API), and `calculator`
- Conditional routing via `tools_condition`: if the LLM emits a tool call, the graph goes to the `tools` node and loops back; otherwise it ends
- `AsyncSqliteSaver` persists conversation state in `chatbot.db` keyed by thread ID

**[streamlit_frontend_tool.py](streamlit_frontend_tool.py)** — the Streamlit UI:
- Manages session state: `thread_id`, `conversations` dict, and `current_conversation`
- Each conversation has its own `thread_id` for isolated SQLite checkpointing
- Streams LLM responses token-by-token and shows a status container while tools are executing
- Renders a sidebar listing all past conversations

## Environment Variables

Required in `.env`:
- `GROQ_API_KEY` — used for LangSmith tracing (not the LLM itself)
- `LANGSMITH_API_KEY` / `LANGCHAIN_API_KEY` — LangSmith observability
- `OPENAI_API_KEY` — ChatOpenAI model
- `ALPHA_VANTAGE_API_KEY` — stock price lookups in `get_stock_price()`

## Key Dependencies

| Package | Role |
|---|---|
| `langgraph` | State machine orchestration |
| `langgraph-checkpoint-sqlite` | Persistent conversation memory |
| `langchain-openai` | LLM integration |
| `langchain-community` | DuckDuckGo search tool |
| `streamlit` | Web UI |
| `python-dotenv` | `.env` loading |
