# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

Install dependencies and run the development server:
```bash
uv sync
uv run uvicorn app:app --reload
```

Open http://localhost:8000 in your browser.

## Project Overview

**Codebase Concierge** is a chat web app that lets users query codebases using the Anthropic Agent SDK.

### Architecture

**Backend (FastAPI):**
- `app.py` — Single FastAPI app with two routes:
  - `GET /` — Serves the chat UI from `static/index.html`
  - `POST /api/chat` — Accepts `{message, conversation_id}` and returns `{reply}`

**Frontend (Vanilla HTML/CSS/JS):**
- `static/index.html` — Chat UI with message history and text input
- `static/style.css` — Styling (gradient header, message bubbles, responsive layout)
- `static/app.js` — Client-side message handling using `fetch()` to call `/api/chat`

### Key Integration Point

The `generate_agent_reply()` function in `app.py` is the stub where agent logic will go. Currently echoes the message; future work replaces this with real Anthropic Agent SDK calls for code analysis.

### Data Flow

1. User types in the chat UI and clicks Send
2. Frontend calls `POST /api/chat` with message + conversation_id
3. `generate_agent_reply()` processes it (stub: echoes back)
4. Response rendered in chat bubble on frontend

## Common Commands

| Task | Command |
|------|---------|
| Install dependencies | `uv sync` |
| Run dev server (with reload) | `uv run uvicorn app:app --reload` |
| Run server (prod-like) | `uv run uvicorn app:app` |
| Add a package | `uv add <package-name> --system-certs` |

## Next Steps (Integration Roadmap)

1. Replace `generate_agent_reply()` stub with Anthropic Agent SDK integration
2. Add tools for code search (Read, Glob, Grep from Agent SDK)
3. Add conversation history persistence
4. Add error handling and streaming responses

## Notes

- Project uses Python 3.12+ with `uv` for dependency management
- FastAPI automatically serves static files from the `static/` directory
- Frontend uses browser's `crypto.randomUUID()` to generate conversation IDs
- CSS uses CSS Grid and Flexbox; no framework dependencies on frontend
