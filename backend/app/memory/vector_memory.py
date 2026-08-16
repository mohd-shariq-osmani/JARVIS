import os
import uuid
import time
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

logger = logging.getLogger("VectorMemory")
MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chroma")

class MemoryManager:
    def __init__(self):
        os.makedirs(MEMORY_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=MEMORY_DIR, settings=Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(name="jarvis_memory")
        self.session_context: List[str] = []

    async def add_memory(self, content: Optional[str] = None, memory_type: str = "fact", importance: int = 1, **kwargs) -> str:
        """
        Flexible memory addition accepting multiple parameter aliases (content, text, fact, type, etc.)
        """
        # Resolve content from aliases
        actual_content = content or kwargs.get("text") or kwargs.get("fact") or kwargs.get("memory") or kwargs.get("query")
        if not actual_content:
            return "Error: No memory content provided."

        actual_type = kwargs.get("type") or memory_type or "fact"
        actual_importance = kwargs.get("importance", importance)

        try:
            memory_id = str(uuid.uuid4())
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            self.collection.add(
                documents=[actual_content],
                metadatas=[{
                    "type": actual_type,
                    "importance": int(actual_importance),
                    "created_at": timestamp,
                    "source": kwargs.get("source", "user")
                }],
                ids=[memory_id]
            )
            logger.info(f"Saved memory [{memory_id}]: {actual_content}")
            return f"Successfully saved to memory: '{actual_content}'"
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            return f"Error saving memory: {e}"

    async def search_memory(self, query: Optional[str] = None, n_results: int = 5, **kwargs) -> str:
        actual_query = query or kwargs.get("text") or kwargs.get("search_term") or kwargs.get("content") or kwargs.get("q")
        if not actual_query:
            return "Error: No search query provided."

        try:
            if self.collection.count() == 0:
                return "No memories stored yet."
            
            results = self.collection.query(
                query_texts=[actual_query],
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

    async def get_all_memories(self) -> List[Dict[str, Any]]:
        try:
            count = self.collection.count()
            if count == 0:
                return []
            
            # Fetch all items
            results = self.collection.get()
            memories = []
            if results and results.get("ids"):
                for i in range(len(results["ids"])):
                    memories.append({
                        "id": results["ids"][i],
                        "content": results["documents"][i] if results.get("documents") else "",
                        "metadata": results["metadatas"][i] if results.get("metadatas") else {},
                        "type": results["metadatas"][i].get("type", "fact") if results.get("metadatas") else "fact",
                        "created_at": results["metadatas"][i].get("created_at", "") if results.get("metadatas") else ""
                    })
            return memories
        except Exception as e:
            logger.error(f"Failed to get all memories: {e}")
            return []

    async def delete_memory(self, memory_id: str) -> bool:
        try:
            self.collection.delete(ids=[memory_id])
            logger.info(f"Deleted memory: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False

    async def clear_all_memories(self) -> bool:
        try:
            self.client.delete_collection(name="jarvis_memory")
            self.collection = self.client.get_or_create_collection(name="jarvis_memory")
            logger.info("Cleared all memories.")
            return True
        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")
            return False

    async def get_context(self, query: str = "") -> str:
        context_str = "--- Session Context ---\n"
        if self.session_context:
            for item in self.session_context[-10:]:
                context_str += f"- {item}\n"
        else:
            context_str += "- None\n"
            
        context_str += "\n--- Long Term Memory ---\n"
        try:
            if self.collection.count() > 0:
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
            context_str += "- None\n"
            
        return context_str

    async def add_session_context(self, text: str):
        self.session_context.append(text)
        if len(self.session_context) > 50:
            self.session_context.pop(0)

def register_memory_tools(registry, memory: MemoryManager):
    registry.register(
        name="remember",
        description="Save an important fact, user preference, instruction, or detail to long-term memory",
        parameters={
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The exact fact or preference to remember"},
                "type": {"type": "string", "enum": ["fact", "preference", "instruction", "person", "device"], "description": "Category of memory"}
            },
            "required": ["content"]
        },
        func=memory.add_memory,
        permission_level=0
    )
    
    registry.register(
        name="search_memory",
        description="Search past long-term memory for semantic matches. Use this when asked to recall past facts, preferences, or details.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Semantic search query to look for in memory"}
            },
            "required": ["query"]
        },
        func=memory.search_memory,
        permission_level=0
    )
