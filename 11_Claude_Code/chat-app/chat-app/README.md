# Codebase Concierge

A chat web app for querying codebases using the Anthropic Agent SDK.

## Project Structure

```
chat-app/
├── app.py              # FastAPI application with routes
├── static/
│   ├── index.html      # Chat UI (HTML)
│   ├── style.css       # Chat styling
│   └── app.js          # Chat client (vanilla JS)
├── pyproject.toml      # uv project configuration
└── uv.lock             # Locked dependencies
```

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

## Running

Start the server:
```bash
uv run uvicorn app:app --reload
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

## API

### GET /
Returns the chat UI (static/index.html).

### POST /api/chat
Accepts a JSON payload:
```json
{
  "message": "your question here",
  "conversation_id": "uuid-string"
}
```

Returns:
```json
{
  "reply": "response text"
}
```

## Next Steps

- Replace the stub `generate_agent_reply()` function with real agent logic using the Anthropic Agent SDK
- Add persistence for conversation history
- Integrate code search and analysis tools
