from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from app.ai.lmstudio import LMStudioProvider
from app.tools.registry import ToolRegistry
from app.tools.system_tools import register_system_tools
from app.tools.files import register_file_tools
from app.platform.windows.computer import WindowsComputerProvider, register_windows_tools
from app.memory.vector_memory import MemoryManager, register_memory_tools
from app.tools.vision import register_vision_tools
from app.agent.orchestrator import AgentOrchestrator
from app.voice.manager import VoiceManager
from app.api import endpoints, diagnostics, telemetry, settings, memory
import asyncio

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

# Initialize Core Services
ai_provider = LMStudioProvider()
tool_registry = ToolRegistry()
memory_manager = MemoryManager()
computer_provider = WindowsComputerProvider()

# Register Tools
register_system_tools(tool_registry)
register_windows_tools(tool_registry, computer_provider)
register_memory_tools(tool_registry, memory_manager)
register_file_tools(tool_registry)
register_vision_tools(tool_registry, computer_provider, ai_provider)

# Initialize Agent and Voice
agent = AgentOrchestrator(ai_provider, tool_registry, memory_manager)
voice_manager = VoiceManager()

async def voice_callback(text: str):
    logger.info(f"Voice Callback received: {text}")
    # Process through agent
    response = await agent.handle_request(text)
    if response:
        # Speak the response
        await voice_manager.speak(response)

# Inject Agent and Services into endpoints
endpoints.agent = agent
memory.memory_manager = memory_manager
app.include_router(endpoints.router)
app.include_router(diagnostics.router)
app.include_router(telemetry.router)
app.include_router(settings.router)
app.include_router(memory.router)

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

@app.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    await voice_ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        voice_ws_manager.disconnect(websocket)

async def voice_state_callback(state: str, transcript: str = None):
    await voice_ws_manager.broadcast({"state": state, "transcript": transcript})


@app.get("/")
async def root():
    return {"status": "JARVIS Backend is running smoothly", "docs_url": "/docs"}


@app.on_event("startup")
async def startup_event():
    await ai_provider.initialize()
    asyncio.create_task(telemetry.telemetry_loop())
    
    # Start Voice Listening Loop
    voice_manager.start_listening(voice_callback, voice_state_callback)
    
    logger.info("JARVIS Backend Started with Voice Recognition Active")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "JARVIS Core"}

@app.get("/status")
async def get_status():
    return {
        "status": "online",
        "providers": {
            "ai": "connected" if ai_provider.active else "disconnected"
        },
        "memory": "initialized"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
