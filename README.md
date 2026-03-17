# Personal Career Pilot

An AI agent that reads your resume, searches for matching jobs and saves the results to the `output/` directory. Built with LangGraph, LangChain, and an MCP file server.

## Setup

This project uses `uv` for dependency management (Python >=3.12).

Create a `.env` file in the project root with your Groq API key.

## Knowledge Base

The `knowledge_base/` folder is where you add your personal files that the agent reads before searching for jobs. You should place the following files inside it:

| File | Description |
|------|-------------|
| `resume.pdf` | Your CV/resume (PDF format) |
| `DreamRoles.txt` | Job titles or roles you are targeting |
| `DreamComps.txt` | Companies you would like to work at |
| `Location.txt` | Your preferred job location |

> These files are listed in `.gitignore` to keep your personal data private — only the empty folder is tracked in the repository.
