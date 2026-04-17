**Work Assistant**

Un bot de Telegram que usa un agente AI (Agno) con acceso a **Notion** y **Google** vía el Model Context Protocol (MCP). Este repositorio contiene la integración del agente, las herramientas MCP y la interfaz de Telegram.

**Contenido rápido**

- [Quick start](#quick-start)
- [Requisitos](#requisitos)
- [Variables de entorno](#variables-de-entorno)
- [Ejecución local](#ejecuci%C3%B3n-local)
- [Docker y despliegue](#docker-y-despliegue)
- [Herramientas MCP](#herramientas-mcp)
- [Desarrollo](#desarrollo)
- [Cómo contribuir](#c%C3%B3mo-contribuir)

---

## Quick start

Sigue estos pasos para ejecutar el bot localmente.

Windows (PowerShell):

```powershell
git clone https://github.com/Jsancmot/work-assistant.git
cd work-assistant
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edita .env y añade las credenciales necesarias
python -m src.main
```

Unix / macOS:

```bash
git clone https://github.com/Jsancmot/work-assistant.git
cd work-assistant
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edita .env y añade las credenciales necesarias
python -m src.main
```

Nota: Algunos flujos requieren lanzar servidores MCP (Notion / Google). Se puede usar `npx` para iniciar servidores MCP locales si hace falta.

---

## Requisitos

- Python 3.12+
- Node.js 20+ (solo para lanzar servidores MCP con `npx`, opcional en producción)
- Docker 24+ (opcional, para despliegues y pruebas locales con containers)

Estructura principal del repo:

```
work-assistant/
├── src/
│   ├── agent/                # Agente y lógica principal
│   ├── tools/                # Integraciones MCP (Notion, Google)
│   └── interfaces/           # Interfaces (Telegram, etc.)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Variables de entorno

Rellena `.env` basándote en `.env.example`. Variables importantes:

| Variable | Obligatoria | Descripción |
|---|---:|---|
| `GROQ_API_KEY` | ✅ | API key para el proveedor de LLM (Groq) |
| `GROQ_MODEL` | — | Nombre del modelo (ej: `llama-3.3-70b-versatile`) |
| `TELEGRAM_BOT_TOKEN` | ✅ | Token del bot desde @BotFather |
| `NOTION_API_KEY` | ✅ | Secreto de integración de Notion |
| `GOOGLE_CREDENTIALS_FILE` | ✅ | Ruta al JSON de credenciales OAuth de Google |
| `AGENT_NAME` | — | Nombre que mostrará el agente (ej: "Work Assistant") |
| `AGENT_INSTRUCTIONS` | — | Prompt del sistema (override opcional) |

Ejemplo mínimo en `.env`:

```
GROQ_API_KEY=your_groq_key_here
TELEGRAM_BOT_TOKEN=123456:ABC-DEF
NOTION_API_KEY=secret_notion_token
GOOGLE_CREDENTIALS_FILE=./gcp-oauth.keys.json
```

---

## Ejecución local

1. Asegúrate de tener las variables en `.env` correctamente configuradas.
2. Si usas servidores MCP locales, lánzalos con `npx` según la documentación de cada servidor.
3. Ejecuta el bot:

```bash
python -m src.main
```

Flujo de ejemplo: Telegram -> `src/interfaces/telegram/bot.py` -> agente (`src/agent/agent.py`) -> herramientas MCP (`src/tools/*`) -> Notion/Drive.

---

## Docker y despliegue

Construir y ejecutar con Docker Compose:

```bash
copy .env.example .env # Windows
cp .env.example .env   # Unix
docker compose up --build
```

Desplegar en Render:

1. Subir el repo a GitHub.
2. Crear un servicio Web en Render y seleccionar Docker.
3. Añadir variables de entorno en el panel de Render.
4. Usar Secret Files para montar `gcp-oauth.keys.json` de forma segura.

---

## Herramientas MCP

- Notion MCP: usa `@notionhq/notion-mcp-server` para permitir búsquedas, lecturas y actualizaciones en Notion.
- Google MCP: usa `@modelcontextprotocol/server-gdrive` para acceso a Google Drive; se puede extender a Calendar/Gmail.

Consulta `src/tools/notion_mcp.py` y `src/tools/google_mcp.py` para ver cómo están integradas.

---

## Desarrollo

- Ejecuta `pip install -r requirements.txt` para dependencias Python.
- Añade linters/tests según convenga (no incluidos por defecto).

Recomendación para contribuir: abre PRs pequeñas y descriptivas; documenta cambios en `CHANGELOG.md` si aplicas cambios notables.

---

## Cómo contribuir

1. Fork del repositorio.
2. Crea una rama con un nombre descriptivo.
3. Haz cambios y añade tests si aplican.
4. Abre un Pull Request describiendo el propósito del cambio.

---

## Licencia y contacto

Proyecto: Work Assistant — licencia por determinar (añade `LICENSE` si quieres especificarla).
Para dudas o soporte, abre un issue o contacta al mantenedor en el repositorio.
