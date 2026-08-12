import os
import uuid
import chromadb
from chromadb.config import Settings

MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chroma")

class VectorDB:
    def __init__(self):
        os.makedirs(MEMORY_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=MEMORY_DIR, settings=Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(name="jarvis_memory")

    def add_memory(self, text: str, metadata: dict = None):
        """Adds a new memory to the vector database."""
        memory_id = str(uuid.uuid4())
        
        self.collection.add(
            documents=[text],
            metadatas=[metadata] if metadata else [{}],
            ids=[memory_id]
        )
        return memory_id

    def search_memory(self, query: str, n_results: int = 5):
        """Searches the vector database for relevant memories."""
        if self.collection.count() == 0:
            return []
            
        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count())
        )
        
        memories = []
        if results['documents'] and len(results['documents']) > 0:
            for i in range(len(results['documents'][0])):
                memories.append({
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                })
                
        return memories

# Singleton instance
vector_db = VectorDB()
