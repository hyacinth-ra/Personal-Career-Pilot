# Personal Career Pilot — Project Documentation

## Overview

Personal Career Pilot is an AI-powered job search agent that automates the process of finding relevant job opportunities. It reads the user's resume and preferences, searches for matching jobs in the Greater Toronto Area, evaluates each job against the resume, ranks the results, and saves a structured report.

---

## How It Works — End-to-End Flow

```
Resume PDF / Cached Summary
        ↓
Read DreamRoles.txt + DreamComps.txt
        ↓
Search jobs (once per role via DuckDuckGo)
        ↓
Deduplicate results
        ↓
Evaluate each job (LLM scores 1–10 + missing skills)
        ↓
Filter (score ≥ 6) → Sort → Top 5
        ↓
Save structured Markdown report → output/job_report.md
```

---

## Project Structure

```
Personal-Career-Pilot/
├── main.py                         # Entry point — wires everything together
├── src/
│   ├── graph.py                    # LangGraph agent loop (StateGraph)
│   ├── tools.py                    # search_jobs + evaluate_job_fit tools
│   └── database.py                 # ChromaDB vector store (available, not yet wired)
├── mcp_servers/
│   └── file_server.py              # MCP server: read_local_file + save_job_results
├── knowledge_base/
│   ├── resume.pdf                  # User's resume
│   ├── resume_summary.txt          # Cached resume summary (auto-generated)
│   ├── DreamRoles.txt              # Preferred job titles (one per line)
│   ├── DreamComps.txt              # Preferred companies (one per line)
│   └── Location.txt                # Target location (not yet wired)
└── output/
    └── job_report.md               # Generated job search report
```

---

## Key Components

### 1. `main.py` — Entry Point

- Initialises the Groq LLM (`llama-3.3-70b-versatile`)
- Starts the MCP file server as a subprocess via `stdio_client`
- Combines local tools (`search_jobs`, `evaluate_job_fit`) with MCP tools (`read_local_file`, `save_job_results`)
- Builds and runs the LangGraph agent

**Resume Cache Option:**
```python
USE_CACHED_RESUME = True   # reads knowledge_base/resume_summary.txt (saves tokens)
USE_CACHED_RESUME = False  # reads full resume.pdf and regenerates the cache
```

---

### 2. `src/graph.py` — Agent Loop

Built with LangGraph's `StateGraph`. The agent state holds the full message history.

```
START → agent → tools → agent → tools → ... → END
                  ↑_____________↓ (retry if no results)
```

- **`agent` node**: calls the LLM to decide the next action
- **`tools` node**: executes whichever tool the LLM called
- **`router`**: decides whether to call tools, retry, or finish

---

### 3. `src/tools.py` — Local Tools

#### `search_jobs(query: str)`
- Searches DuckDuckGo for jobs in the Greater Toronto Area
- Targets: `greenhouse.io`, `lever.co`, `linkedin.com/jobs`, `ca.indeed.com`
- Blacklists spam sites: `jooble.org`, `ziprecruiter.com`, `trovit.com`, `talent.com`, `jobrapido.com`, `learn4good.com`, `whatjobs.com`
- Returns up to 5 results per query

#### `evaluate_job_fit(resume_text: str, job_description: str)`
- Makes a direct Groq API call with a structured scoring prompt
- Returns JSON: `{"score": 8, "missing_skills": ["Docker", "Kubernetes"]}`
- Scoring rubric: 1–2 (poor) → 9–10 (exceptional)

---

### 4. `mcp_servers/file_server.py` — MCP File Tools

Runs as a separate subprocess. Exposes two tools to the agent:

#### `read_local_file(filepath: str)`
- Reads `.pdf` (via PyMuPDF), `.md`, or `.txt` files
- Used to read the resume, DreamRoles.txt, DreamComps.txt

#### `save_job_results(filename: str, content: str)`
- Saves content to `./output/{filename}`
- Used to write `job_report.md` and `resume_summary.txt`

---

### 5. `src/database.py` — Vector Store (Available, Not Yet Active)

- Loads documents from `knowledge_base/` (PDF, TXT, MD)
- Chunks text and stores embeddings in ChromaDB (`./chroma_db/`)
- Uses HuggingFace `all-MiniLM-L6-v2` for embeddings
- `initialize_vector_store()` — builds/rebuilds the DB
- `get_retriever()` — returns a semantic search retriever (k=3)

> Not yet wired into `main.py` — the agent reads files directly via `read_local_file` instead.

---

## Agent Protocol (System Prompt)

The agent follows this 4-step protocol on every run:

1. **Read** resume (cached `.txt` or full `.pdf`) + `DreamRoles.txt` + `DreamComps.txt`
2. **Search** once per role in `DreamRoles.txt` → deduplicate results
3. **Evaluate** each job with `evaluate_job_fit` → score + missing skills; +1 bonus for Dream Companies
4. **Rank & Save** top 5 jobs (score ≥ 6, sorted highest first) to `output/job_report.md`

---

## Output Format (`output/job_report.md`)

```markdown
# GTA Job Search Report
Generated: {date}

---

## Rank 1: {Job Title}
- **Company:** {Company Name or "Not listed"}
- **Link:** {URL}
- **Fit Score:** {Score}/10
- **Missing Skills:** {comma-separated list, or "None"}
- **Summary:** {1-2 sentence description}

---
```

---

## Configuration

### `.env`
```
GROQ_API_KEY=your_groq_api_key
```

### `knowledge_base/DreamRoles.txt`
```
Data Scientist
Software Engineer
Software Developer
Machine Learning Engineer
Researcher
```

### `knowledge_base/DreamComps.txt`
```
Google
TD
Huawei
Aviva
RBC
```

---

## Setup & Running

```bash
# Install dependencies
uv sync

# Run the agent
python main.py
```

---

## Known Limitations & Planned Improvements

| # | Improvement | Status |
|---|---|---|
| 1 | `evaluate_job_fit` — real LLM scoring | ✅ Done |
| 2 | Read `DreamRoles.txt` + `DreamComps.txt` | ✅ Done |
| 3 | Search once per role (not just once) | ✅ Done |
| 4 | Rank and return top 5 | ✅ Done |
| 5 | Structured Markdown output format | ✅ Done |
| 6 | Resume caching (`USE_CACHED_RESUME` flag) | ✅ Done |
| 7 | Wire up `Location.txt` dynamically | 🔲 Planned |
| 8 | Wire up RAG vector store | 🔲 Planned |
| 9 | Cover letter generation for top match | 🔲 Planned |
| 10 | Graceful rate limit handling (auto-retry) | 🔲 Planned |

---

## Dependencies

| Package | Purpose |
|---|---|
| `langgraph` | Agent loop (StateGraph) |
| `langchain-groq` | Groq LLM integration |
| `langchain-mcp-adapters` | Load MCP tools into LangChain |
| `fastmcp` | MCP file server |
| `ddgs` | DuckDuckGo job search |
| `groq` | Direct Groq API calls (evaluate_job_fit) |
| `pymupdf` | PDF reading |
| `langchain-chroma` | Vector store (planned) |
| `langchain-huggingface` | Embeddings (planned) |
| `python-dotenv` | Environment variable loading |
