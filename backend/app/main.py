from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import asyncio

from app.ai.router import AIRouter
from app.tools.registry import ToolRegistry
from app.tools.system_tools import register_system_tools
from app.tools.files import register_file_tools
from app.tools.web_tools import register_web_tools
from app.platform.windows.computer import WindowsComputerProvider, register_windows_tools
from app.memory.vector_memory import MemoryManager, register_memory_tools
from app.tasks.manager import TaskManager
from app.tools.task_tools import register_task_tools
from app.tools.vision import register_vision_tools
from app.agent.orchestrator import AgentOrchestrator
from app.agent.queue_manager import MessageQueueManager
from app.voice.manager import VoiceManager
from app.api import endpoints, diagnostics, telemetry, settings, memory, tasks

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("JARVIS-CORE")

app = FastAPI(title="JARVIS Backend API", version="0.1.0")

# CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VoiceConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

voice_ws_manager = VoiceConnectionManager()

async def voice_state_callback(state_or_data, transcript: str = None):
    if isinstance(state_or_data, dict):
        await voice_ws_manager.broadcast(state_or_data)
    else:
        await voice_ws_manager.broadcast({"state": str(state_or_data), "transcript": transcript})

# Initialize Core Services
ai_provider = AIRouter()
tool_registry = ToolRegistry()
memory_manager = MemoryManager()
task_manager = TaskManager()
computer_provider = WindowsComputerProvider()

# Register Tools
register_system_tools(tool_registry)
register_windows_tools(tool_registry, computer_provider)
register_web_tools(tool_registry)
register_memory_tools(tool_registry, memory_manager)
register_task_tools(tool_registry, task_manager)
register_file_tools(tool_registry)
register_vision_tools(tool_registry, computer_provider, ai_provider)

# Initialize Agent, Voice, and Message Queue
agent = AgentOrchestrator(ai_provider, tool_registry, memory_manager)
voice_manager = VoiceManager()
queue_manager = MessageQueueManager(agent, voice_manager, broadcast_callback=voice_state_callback)
voice_manager.set_queue_manager(queue_manager)

# Inject Agent and Services into endpoints
endpoints.agent = agent
endpoints.queue_manager = queue_manager
memory.memory_manager = memory_manager
tasks.task_manager = task_manager

app.include_router(endpoints.router)
app.include_router(diagnostics.router)
app.include_router(telemetry.router)
app.include_router(settings.router)
app.include_router(memory.router)
app.include_router(tasks.router)

@app.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    await voice_ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        voice_ws_manager.disconnect(websocket)

@app.get("/")
async def root():
    return {"status": "JARVIS Backend is running smoothly", "docs_url": "/docs"}

@app.on_event("startup")
async def startup_event():
    await ai_provider.initialize()
    asyncio.create_task(telemetry.telemetry_loop())
    
    # Start Message Queue Worker
    queue_manager.start()
    
    # Start Background Task Scheduler Loop
    asyncio.create_task(task_manager.run_scheduler(agent=agent, voice_manager=voice_manager))
    
    # Start Voice Listening Loop
    voice_manager.start_listening(voice_state_callback)
    
    logger.info("JARVIS Backend Started with Voice Recognition, Message Queue & Task Scheduler Active")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "JARVIS Core"}

@app.get("/status")
async def get_status():
    return {
        "status": "online",
        "providers": {
            "ai": ai_provider.active_provider_name,
            "ai_active": await ai_provider.health_check()
        },
        "memory": "initialized",
        "tasks_count": len(task_manager.get_tasks())
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
