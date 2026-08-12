import os
import uuid
import logging
from typing import List
import chromadb
from chromadb.config import Settings

logger = logging.getLogger("VectorMemory")
MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chroma")

class MemoryManager:
    def __init__(self):
        os.makedirs(MEMORY_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=MEMORY_DIR, settings=Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(name="jarvis_memory")
        self.session_context = []

    async def add_memory(self, content: str, memory_type: str = "fact", importance: int = 1):
        try:
            memory_id = str(uuid.uuid4())
            self.collection.add(
                documents=[content],
                metadatas=[{"type": memory_type, "importance": importance}],
                ids=[memory_id]
            )
            return f"Saved to memory: {content}"
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            return f"Error saving memory: {e}"

    async def search_memory(self, query: str, n_results: int = 5):
        try:
            if self.collection.count() == 0:
                return "No memories stored yet."
            
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, self.collection.count())
            )
            
            if not results['documents'] or len(results['documents'][0]) == 0:
                return "No relevant memories found."
                
            formatted = "Retrieved Memories:\n"
            for doc in results['documents'][0]:
                formatted += f"- {doc}\n"
            return formatted
        except Exception as e:
            logger.error(f"Search memory failed: {e}")
            return f"Error searching memory: {e}"

    async def get_context(self, query: str = "") -> str:
        context_str = "--- Session Context ---\n"
        for item in self.session_context[-10:]:
            context_str += f"- {item}\n"
            
        context_str += "\n--- Long Term Memory ---\n"
        try:
            if self.collection.count() > 0:
                # If we have a query, search semantically. Otherwise, fetch generic context.
                search_term = query if query else "user preferences facts"
                results = self.collection.query(
                    query_texts=[search_term],
                    n_results=min(5, self.collection.count())
                )
                if results['documents'] and len(results['documents'][0]) > 0:
                    for doc in results['documents'][0]:
                        context_str += f"- {doc}\n"
                else:
                    context_str += "- None\n"
            else:
                context_str += "- None\n"
        except Exception as e:
            logger.error(f"Failed to retrieve memory context: {e}")
            
        return context_str

    async def add_session_context(self, text: str):
        self.session_context.append(text)
        if len(self.session_context) > 50:
            self.session_context.pop(0)

def register_memory_tools(registry, memory: MemoryManager):
    registry.register(
        name="remember",
        description="Save an important fact or preference to long-term memory",
        parameters={"type": "object", "properties": {"content": {"type": "string"}, "type": {"type": "string", "enum": ["fact", "preference", "instruction"]}}, "required": ["content"]},
        func=memory.add_memory,
        permission_level=0
    )
    
    registry.register(
        name="search_memory",
        description="Search past long-term memory for semantic matches. Use this when asked to recall past facts.",
        parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        func=memory.search_memory,
        permission_level=0
    )
