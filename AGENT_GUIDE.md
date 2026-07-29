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
Execute the full test suite (21 unit tests across all modules):
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
│   └── mcdonalds_allergens.csv                     # Simple table file (CSV)
├── src/
│   ├── scraper.py                                  # Data harvester script
│   ├── tools.py                                    # Allergen lookup, category & item evaluation tools
│   ├── agent.py                                    # ADK Architecture: AllergyExtractorAgent & McDonaldsAllergenAgent
│   ├── telemetry.py                                # Structured trace telemetry
│   ├── server.py                                   # Zero-dependency HTTP web server
│   └── app.py                                      # FastAPI web server
├── static/
│   ├── index.html                                  # Web UI layout
│   ├── style.css                                   # Glassmorphism styling
│   └── app.js                                      # Frontend logic & auto-sync UI toggles
└── tests/                                          # Automated unit test suite (21 tests)
```

---

## 🔑 Key Concepts & Data Flow
1. **ADK Multi-Agent Architecture**:
   - `AllergyExtractorAgent`: ADK Sub-Agent powered by **Gemini Flash** (`gemini-2.5-flash`) that emits food allergy categories (`Gluten`, `Dairy`, `Nuts`) mentioned in prompt text.
   - `McDonaldsAllergenAgent`: Primary orchestrator agent equipped with simple table data tools.
2. **Simple Table Data Source**: All allergen information is read directly from `data/mcdonalds_allergens.json`.
3. **Item & Category Evaluation**:
   - Specific items (e.g. *Big Mac*, *Egg McMuffin*, *Coca-Cola*) are evaluated in `evaluate_allergen_safety()`.
   - Generic terms (e.g. *burgers*, *shakes*, *breakfast*, *fries*, *drinks*) are mapped in `GENERIC_CATEGORY_MAP` and evaluated in `evaluate_category_safety()`.
4. **Auto-Sync UI Toggles**: Emitted allergies automatically activate the corresponding UI buttons (`🌾 Gluten-Free`, `🥛 Dairy-Free`, `🥜 Nut-Free`).
5. **Medical Disclaimer**: Every response includes an explicit disclaimer about fast-food shared prep areas and cross-contamination.
