# 🤖 AI Agent Developer Guide & Server Instructions

This document helps any AI coding assistant or developer quickly understand, run, test, and modify the **McDonald's Allergen AI Agent**.

---

## ⚡ Server Quickstart
To start the local web server immediately:
```bash
PYTHONPATH=. python3 src/server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 🧪 Running Unit Tests
Execute the full test suite (28 unit tests across all modules):
```bash
python3 -m unittest discover tests
```

---

## 📂 Project Architecture & Multi-Agent Flow

```text
simple-allgergen-ai-lab/
├── .agents/
│   ├── AGENTS.md                                   # Workspace AI rules
│   └── skills/
│       └── mcdonalds-allergen-agent/
│           └── SKILL.md                            # Workspace AI skill definition
├── data/
│   ├── mcdonalds_allergens.json                    # Simple table file (JSON)
│   ├── mcdonalds_allergens.csv                     # Simple table file (CSV)
│   └── sessions/                                   # Persistent JSON session memory storage
├── src/
│   ├── scraper.py                                  # Data harvester script
│   ├── tools.py                                    # Typed tools with explicit parameter docstrings
│   ├── memory.py                                   # SessionMemoryManager: persistent storage, history compaction & async background thread pool
│   ├── model_router.py                             # ModelRouter: dynamic task complexity routing (gemini-2.5-flash vs gemini-2.5-pro)
│   ├── guardrails.py                               # SelfEvaluationEngine: policy plugins & autonomous self-reflection pass
│   ├── hitl.py                                     # HITLConfirmationManager: Human-in-the-Loop confirmation hooks
│   ├── agent.py                                    # ADK Architecture: AllergyExtractorAgent & McDonaldsAllergenAgent
│   ├── telemetry.py                                # Structured trace telemetry
│   ├── server.py                                   # Zero-dependency HTTP web server
│   └── app.py                                      # FastAPI web server
├── static/
│   ├── index.html                                  # Web UI layout
│   ├── style.css                                   # Glassmorphism styling
│   └── app.js                                      # Frontend logic & auto-sync UI toggles
└── tests/                                          # Automated unit test suite (28 tests)
```

---

## 🔑 Key Concepts & Data Flow
1. **Multi-Model Routing (`src/model_router.py`)**: Routes low-complexity queries to `gemini-2.5-flash` and high-complexity multi-allergy queries to `gemini-2.5-pro`.
2. **Policy Guardrails & Self-Evaluation (`src/guardrails.py`)**: `SelfEvaluationEngine` runs an autonomous self-reflection pass over generated responses to verify strict policy compliance.
3. **Human-in-the-Loop (HITL) Confirmation Hooks (`src/hitl.py`)**: Generates explicit user confirmation tokens (`POST /api/hitl/confirm`) for high-risk allergen warnings.
4. **Persistent Session Memory & History Compaction (`src/memory.py`)**:
   - Saves session state to disk (`data/sessions/{session_id}.json`).
   - Compacts older turns into high-density executive summaries when turn count exceeds thresholds.
   - Non-blocking async background thread execution (`ThreadPoolExecutor`).
5. **ADK Multi-Agent Architecture**: `AllergyExtractorAgent` (sub-agent) + `McDonaldsAllergenAgent` (orchestrator).
6. **Medical Disclaimer**: Every response includes an explicit disclaimer about fast-food shared prep areas and cross-contamination.
