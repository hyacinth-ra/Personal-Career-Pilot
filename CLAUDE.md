# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal Career Pilot is an AI agent that reads a user's resume, searches for matching jobs via DuckDuckGo, and saves results to the `output/` directory. It is built with LangGraph, LangChain, and an MCP file server.

## Setup & Running

This project uses `uv` for dependency management (Python >=3.12).

```bash
# Install dependencies
uv sync

# Run the agent
uv run python main.py
# or
python main.py
```

Requires a `.env` file with:
```
GROQ_API_KEY=your_key_here
```

## Architecture

The system has three layers working together:

### 1. LangGraph Agent Loop (`src/graph.py`)
A `StateGraph` with two nodes — `agent` (the LLM) and `tools` (tool executor). The `router` function decides whether to call tools, loop back for a retry (when search returns no results), or terminate. The state accumulates the full message history via `operator.add`.

### 2. Tools (`src/tools.py`, `mcp_servers/file_server.py`)
- **`search_jobs`** (local LangChain tool): Uses `ddgs` (DuckDuckGo) to search for London job postings, filtering out spam domains.
- **`read_local_file`** (MCP tool): Reads `.pdf`, `.md`, or `.txt` files using `pymupdf`.
- **`save_job_results`** (MCP tool): Saves content to the `./output/` directory.

The MCP file server (`mcp_servers/file_server.py`) runs as a subprocess via `stdio_client`. Tools from both sources are merged and bound to the LLM in `main.py`.

### 3. Knowledge Base & Vector Store (`src/database.py`, `knowledge_base/`)
- `knowledge_base/` contains the user's resume (`resume.pdf`), `DreamRoles.txt`, `DreamComps.txt`, and `Location.txt`.
- `src/database.py` provides `initialize_vector_store()` and `get_retriever()` using ChromaDB + HuggingFace `all-MiniLM-L6-v2` embeddings. The vector store is persisted at `./chroma_db/`.
- **Note:** The vector store/RAG retriever is not currently wired into `main.py` — the agent reads the resume directly via the `read_local_file` MCP tool instead.

## Key Conventions

- The agent is instructed (via `SystemMessage` in `main.py`) to always: (1) read `./knowledge_base/resume.pdf`, (2) search for jobs, (3) save results.
- Job search is hardcoded to London. To change location, update the `advanced_query` string in `src/tools.py`.
- Output files are written to `./output/` (created automatically if missing).
- The LLM is Groq's `llama-3.3-70b-versatile` with `temperature=0`.
