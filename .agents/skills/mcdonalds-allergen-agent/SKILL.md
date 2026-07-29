---
name: mcdonalds-allergen-agent
description: Quickstart commands, execution context, architecture layout, and tool specifications for the McDonald's Allergen AI Agent project. Activate when starting the web server, running unit tests, or modifying allergen agent logic.
---

# 🍔 McDonald's Allergen AI Agent Developer & Agent Context

This skill provides operational instructions and architectural context for AI agents working on the **McDonald's Allergen AI Agent** codebase.

---

## ⚡ Quickstart Commands for AI Agents

### 1. Run Simple Data Scraper / Harvester
Generate or refresh the simple table files (`data/mcdonalds_allergens.json` and `data/mcdonalds_allergens.csv`):
```bash
python3 src/scraper.py
```

### 2. Start the Web Server (Zero-Dependency Standalone Mode)
Launch the HTTP web server on `http://localhost:8000`:
```bash
PYTHONPATH=. python3 src/server.py
```
> **Note**: `src/server.py` uses standard library Python modules (`http.server`, `urllib`, `json`) and serves static UI assets from `static/` alongside REST API routes.

### 3. Run FastAPI Web Server (Production / Virtualenv Mode)
If dependencies in `requirements.txt` are installed:
```bash
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

### 4. Execute Full Unit Test Suite
Run all 21 automated unit tests covering scraper, tools, ADK sub-agent, main agent logic, server API, and telemetry:
```bash
python3 -m unittest discover tests
```

---

## 🧩 Codebase Architecture & Key Files

| Directory / File | Purpose & Responsibilities |
| :--- | :--- |
| `data/mcdonalds_allergens.json` | **Simple Table File** containing 24 canonical McDonald's menu items with allergen flags (`contains_gluten`, `contains_dairy`, `contains_nuts`), category, and ingredient summaries. |
| `src/scraper.py` | Data harvester script parsing McDonald's full menu items into the simple table file format. |
| `src/tools.py` | Agent lookup tools (`lookup_item_allergens`, `search_safe_items`, `evaluate_allergen_safety`, `evaluate_category_safety`). Includes `GENERIC_CATEGORY_MAP` for general queries (e.g., *burgers*, *milkshakes*, *fries*, *drinks*, *breakfast*). |
| `src/agent.py` | **ADK Architecture**: `AllergyExtractorAgent` (Gemini Flash sub-agent emitting mentioned allergies) & `McDonaldsAllergenAgent` (Primary orchestrator agent enforcing safety guardrails and medical disclaimers). |
| `src/telemetry.py` | `TelemetryManager` recording structured trace trajectories, execution latency, and maintaining recent trace history. |
| `src/server.py` | Standalone zero-dependency HTTP server serving `static/` UI files and REST API routes (`/api/chat`, `/api/menu`, `/api/traces`, `/api/health`). |
| `src/app.py` | FastAPI alternative server implementation for production/Docker environments. |
| `static/` | Web UI assets (`index.html`, `style.css`, `app.js`) featuring allergy toggles (`Gluten`, `Dairy`, `Nuts`) auto-synced with Gemini Flash outputs, chat input, sample prompt buttons, and live trace telemetry drawer. |
| `tests/` | Automated unit test suite (`test_scraper.py`, `test_tools.py`, `test_agent.py`, `test_app.py`, `test_telemetry.py`). |

---

## 🛡️ Guardrails & Safety Guidelines
1. **Never Hallucinate Ingredients**: Always read menu data from `data/mcdonalds_allergens.json` via tools in `src/tools.py`.
2. **Mandatory Medical Disclaimer**: Every user-facing response must include a disclaimer warning about fast-food cross-contamination and shared prep areas.
3. **No Secrets / Credentials in Git**: Never commit `.env` files or API keys. Verify `git status` before committing changes.
