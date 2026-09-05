import uuid
import asyncio
import json
from contextlib import asynccontextmanager
from typing import Dict, List, Any
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.schemas import (
    ReviewSubmitRequest, ReviewJobResponse, BenchmarkEvaluationReport
)
from app.db.database import (
    init_db, get_review_job, get_all_reviews, get_latest_evaluation
)
from app.agent.reviewer_loop import ReviewerAgent
from app.evaluation.evaluator import BenchmarkEvaluator

# Connection manager for active WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    def disconnect(self, job_id: str, websocket: WebSocket):
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def broadcast_to_job(self, job_id: str, message: Dict[str, Any]):
        if job_id in self.active_connections:
            dead_sockets = []
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    dead_sockets.append(connection)
            for dead in dead_sockets:
                self.disconnect(job_id, dead)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    await init_db()
    # Seed initial evaluation benchmark if not present
    existing_eval = await get_latest_evaluation()
    if not existing_eval:
        evaluator = BenchmarkEvaluator()
        await evaluator.run_evaluation()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Professional Full-Stack AI Code Review Agent Engine. Engineered by Divyansh Mishra.",
    lifespan=lifespan
)

# Enable CORS for frontend Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "engineer": settings.ENGINEER,
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

@app.post("/api/review", response_model=Dict[str, str])
async def submit_review(
    request: ReviewSubmitRequest,
    background_tasks: BackgroundTasks
):
    """
    Submits a repository or diff for multi-step AI code review.
    Returns job_id immediately and processes asynchronously.
    """
    job_id = f"rev_{uuid.uuid4().hex[:8]}"
    agent = ReviewerAgent()

    async def run_in_background():
        async def ws_callback(payload: Dict[str, Any]):
            await manager.broadcast_to_job(job_id, payload)
            
        await agent.run_review(job_id, request, ws_broadcast=ws_callback)

    # Launch in asyncio event loop
    asyncio.create_task(run_in_background())

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Review job queued successfully"
    }

@app.get("/api/review/{job_id}", response_model=ReviewJobResponse)
async def get_review_status(job_id: str):
    """
    Poll review status, summary, and detected findings.
    """
    job = await get_review_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Review job not found")
    return job

@app.get("/api/review/{job_id}/trace")
async def get_review_trace(job_id: str):
    """
    Returns full timeline of agent thoughts, tool invocations, inputs, and outputs.
    """
    job = await get_review_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Review job not found")
    return {
        "job_id": job.job_id,
        "total_steps": len(job.traces),
        "traces": job.traces
    }

@app.get("/api/reviews")
async def list_reviews():
    """
    List all previous reviews with summary counts.
    """
    return await get_all_reviews()

@app.get("/api/evaluation")
async def get_evaluation_metrics():
    """
    Returns latest benchmark evaluation metrics (Precision, Recall, F1).
    """
    eval_data = await get_latest_evaluation()
    if not eval_data:
        evaluator = BenchmarkEvaluator()
        report = await evaluator.run_evaluation()
        return report.model_dump()
    return eval_data

@app.post("/api/evaluation/run")
async def run_evaluation_benchmark():
    """
    Triggers re-run of benchmark suite against all labeled test cases.
    """
    evaluator = BenchmarkEvaluator()
    report = await evaluator.run_evaluation()
    return report.model_dump()

@app.websocket("/ws/review/{job_id}")
async def websocket_review_stream(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint streaming live agent thought process, tool calls, and progress events.
    """
    await manager.connect(job_id, websocket)
    try:
        # Send current job status upon connection
        job = await get_review_job(job_id)
        if job:
            await websocket.send_text(json.dumps({
                "type": "initial_state",
                "job_id": job.job_id,
                "status": job.status,
                "traces_count": len(job.traces),
                "findings_count": len(job.findings)
            }))

        while True:
            # Keep connection alive, listen for ping or client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)
    except Exception:
        manager.disconnect(job_id, websocket)
