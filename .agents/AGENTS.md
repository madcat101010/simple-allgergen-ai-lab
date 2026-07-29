# McDonald's Allergen AI Agent — Workspace AI Rules & Context

This document provides guidelines for AI agents working in this repository.

## 🚀 Quick Server Execution
To start the local server, run:
```bash
PYTHONPATH=. python3 src/server.py
```
Server runs at `http://localhost:8000`.

## 🧪 Testing Guidelines
Always run unit tests before committing code changes:
```bash
python3 -m unittest discover tests
```

## 🔒 Security Constraints
- Never commit credentials or API keys. Keep `.env` and `*.pdf` files in `.gitignore`.
- Always preserve medical disclaimers in agent responses.
