# Work Assistant

A Telegram bot powered by an [Agno](https://docs.agno.com) AI agent with access to **Notion** and **Google** through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io).

---

## Architecture

```
work-assistant/
├── src/
│   ├── agent/
│   │   └── agent.py           # Agno agent with MCP tools
│   ├── tools/
│   │   ├── notion_mcp.py      # Notion MCP tool
│   │   └── google_mcp.py      # Google MCP tool
│   ├── interfaces/
│   │   └── telegram/
│   │       └── bot.py         # Telegram bot interface
│   ├── config.py              # Configuration from environment variables
│   └── main.py                # Entry point
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

The architecture is intentionally layered so that new interfaces (WhatsApp, Teams, …) can be added under `src/interfaces/` without touching the agent or tool logic.

---

## Prerequisites

| Tool | Minimum version | Purpose |
|------|----------------|---------|
| Python | 3.12 | Runtime |
| Node.js | 20 | MCP servers launched via `npx` |
| Docker | 24 | Containerisation (optional for local dev) |

---

## Quick start (local)

1. **Clone and install dependencies**

   ```bash
   git clone https://github.com/Jsancmot/work-assistant.git
   cd work-assistant
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env and fill in all required values
   ```

3. **Run**

   ```bash
   python -m src.main
   ```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key used by the agent |
| `OPENAI_MODEL` | — | Model name (default: `gpt-4o`) |
| `TELEGRAM_BOT_TOKEN` | ✅ | Token from [@BotFather](https://t.me/BotFather) |
| `NOTION_API_KEY` | ✅ | Notion integration secret |
| `GOOGLE_CREDENTIALS_FILE` | ✅ | Path to the Google OAuth 2.0 credentials JSON file |
| `AGENT_NAME` | — | Display name for the agent (default: `Work Assistant`) |
| `AGENT_INSTRUCTIONS` | — | System prompt override |

---

## Docker

### Build and run with Docker Compose

```bash
cp .env.example .env   # fill in values
docker compose up --build
```

### Deploy to Render

1. Push this repository to GitHub.
2. Create a new **Web Service** on [Render](https://render.com) and point it at the repository.
3. Set the **Environment** to **Docker**.
4. Add all required environment variables in the Render dashboard.
5. Deploy.

> **Tip:** Use Render's *Secret Files* feature to mount `credentials.json` securely.

---

## Tools

### Notion MCP

Uses the official [`@notionhq/notion-mcp-server`](https://github.com/makenotion/notion-mcp-server) package. The agent can search, read, and update Notion pages and databases.

### Google MCP

Uses [`@modelcontextprotocol/server-gdrive`](https://github.com/modelcontextprotocol/servers/tree/main/src/gdrive) to give the agent access to Google Drive. Additional Google services (Calendar, Gmail, …) can be added by extending `src/tools/google_mcp.py`.

---

## Adding a new interface

1. Create a new directory under `src/interfaces/` (e.g. `src/interfaces/whatsapp/`).
2. Import `create_agent` from `src.agent.agent` and implement the messaging loop.
3. Call your new interface's `run` function from `src/main.py`.