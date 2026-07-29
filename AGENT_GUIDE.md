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

## 📊 Run Golden Dataset Evaluation Benchmark
To run the ground-truth golden dataset evaluator:
```bash
python3 src/evaluator.py
```

---

## 🧪 Running Unit Tests
Execute the full test suite (42 unit tests across all modules):
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
├── terraform/                                      # Infrastructure as Code (IaC) - Terraform
│   ├── main.tf                                     # GCP Cloud Run, Secret Manager, IAM & Probes
│   ├── variables.tf                                # Project ID, region & image variables
│   └── outputs.tf                                  # Cloud Run URI & Secret Manager outputs
├── k8s/                                            # Infrastructure as Code (IaC) - Kubernetes
│   └── deployment.yaml                             # Kubernetes Deployment, SecretKeyRef & Service
├── data/
│   ├── mcdonalds_allergens.json                    # Simple table file (JSON)
│   ├── mcdonalds_allergens.csv                     # Simple table file (CSV)
│   ├── golden_evaluation_dataset.json              # Golden benchmark evaluation dataset
│   └── sessions.db                                 # Dedicated SQLite Database & Vector Store
├── src/
│   ├── cli.py                                      # Agent CLI (chat, menu, traces, evaluate, confirm-hitl)
│   ├── scraper.py                                  # Data harvester script
│   ├── tools.py                                    # Typed tools with explicit parameter docstrings & structured LLM path recovery instructions
│   ├── evaluator.py                                # Golden Dataset benchmark runner & metric exporter
│   ├── db.py                                       # DatabaseSessionStore: SQLite database engine & integrated Vector Store
│   ├── memory.py                                   # SessionMemoryManager: SQLite database storage, vector search, history compaction & async background thread pool
│   ├── model_router.py                             # ModelRouter: dynamic task complexity routing (gemini-2.5-flash vs gemini-2.5-pro)
│   ├── guardrails.py                               # SelfEvaluationEngine: policy plugins & autonomous self-reflection pass
│   ├── hitl.py                                     # HITLConfirmationManager: Human-in-the-Loop confirmation hooks
│   ├── agent.py                                    # ADK Architecture: AllergyExtractorAgent & McDonaldsAllergenAgent
│   ├── secret_manager.py                           # Dedicated Secret Manager for GCP Secret Manager API
│   ├── telemetry.py                                # Structured trace telemetry
│   ├── server.py                                   # Zero-dependency HTTP web server
│   └── app.py                                      # FastAPI web server
├── static/
│   ├── index.html                                  # Web UI layout
│   ├── style.css                                   # Glassmorphism styling
│   └── app.js                                      # Frontend logic & auto-sync UI toggles
├── tests/                                          # Automated unit & benchmark test suite (42 tests)
├── Dockerfile                                      # Container build configuration
└── docker-compose.yml                              # Single-command Docker orchestration
```

---

## 🔑 Key Concepts & Data Flow
1. **Golden Dataset Benchmark (`src/evaluator.py`)**: Ground-truth dataset evaluating accuracy, recall, disclaimer compliance, and latency metrics (**100% Accuracy achieved**).
2. **Multi-Model Routing (`src/model_router.py`)**: Routes low-complexity queries to `gemini-2.5-flash` and high-complexity multi-allergy queries to `gemini-2.5-pro`.
3. **Policy Guardrails & Self-Evaluation (`src/guardrails.py`)**: `SelfEvaluationEngine` runs an autonomous self-reflection pass over generated responses to verify strict policy compliance.
4. **Human-in-the-Loop (HITL) Confirmation Hooks (`src/hitl.py`)**: Generates explicit user confirmation tokens (`POST /api/hitl/confirm`) for high-risk allergen warnings.
5. **Dedicated SQLite Database & Vector Store (`src/db.py` & `src/memory.py`)**: Stores session state, turn logs, and vector memory embeddings in a dedicated ACID-compliant SQLite database (`data/sessions.db`) with semantic vector similarity search and async background writes.
6. **ADK Multi-Agent Architecture**: `AllergyExtractorAgent` (sub-agent) + `McDonaldsAllergenAgent` (orchestrator).
7. **Medical Disclaimer**: Every response includes an explicit disclaimer about fast-food shared prep areas and cross-contamination.
