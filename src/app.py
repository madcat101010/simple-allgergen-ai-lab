"""
McDonald's Allergen AI Agent Web Application (FastAPI Backend)
--------------------------------------------------------------
Provides REST API endpoints for user prompts, allergen evaluation,
menu item listings, telemetry traces, and static UI serving.
"""

import os
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from src.agent import AllergenAgent
from src.tools import load_allergen_dataset
from src.telemetry import telemetry

app = FastAPI(
    title="McDonald's Allergen AI Agent",
    description="Interactive AI Agent for evaluating McDonald's menu items for Gluten, Dairy, and Nut allergies.",
    version="1.0.0"
)

# Initialize Agent instance
agent = AllergenAgent()

# Static directory setup
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")


class ChatRequest(BaseModel):
    prompt: str
    allergies: List[str] = []


class ChatResponse(BaseModel):
    prompt: str
    user_allergies: List[str]
    status: str
    safety_badge: str
    response: str
    details: Optional[dict] = None
    disclaimer: str
    execution_time_ms: float
    trace: dict


@app.get("/api/health")
def health_check():
    """Health check endpoint for deployment & evaluation."""
    return {"status": "ok", "app": "mcdonalds-allergen-ai-agent", "version": "1.0.0"}


@app.get("/api/menu")
def get_menu():
    """Returns the harvested McDonald's simple allergen table dataset."""
    try:
        data = load_allergen_dataset()
        return {"count": len(data), "items": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/traces")
def get_traces():
    """Returns recent telemetry traces for observability and evaluation."""
    return {"count": len(telemetry.recent_traces), "traces": telemetry.get_recent_traces()}


@app.post("/api/chat", response_model=ChatResponse)
def process_chat(req: ChatRequest):
    """Processes user prompts against allergen safety tools."""
    start_time = time.time()
    
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    try:
        result = agent.process_query(req.prompt, req.allergies)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Tool call record
        tool_calls = [
            {
                "tool": "evaluate_allergen_safety",
                "input": {"item": result.get("evaluated_item"), "allergies": req.allergies},
                "matched_allergens": result.get("details", {}).get("matched_allergens", [])
            }
        ]

        # Record telemetry trace
        trace = telemetry.record_trace(
            prompt=req.prompt,
            user_allergies=req.allergies,
            status=result["status"],
            evaluated_item=result.get("evaluated_item"),
            execution_time_ms=duration_ms,
            tool_calls=tool_calls,
            details=result.get("details")
        )

        return ChatResponse(
            prompt=result["prompt"],
            user_allergies=result["user_allergies"],
            status=result["status"],
            safety_badge=result["safety_badge"],
            response=result["response"],
            details=result.get("details"),
            disclaimer=result.get("disclaimer", "Warning: Shared kitchen prep areas."),
            execution_time_ms=duration_ms,
            trace=trace
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


# Serve static files if directory exists
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def read_root():
        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return JSONResponse({"message": "FastAPI backend running. static/index.html missing."})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)
