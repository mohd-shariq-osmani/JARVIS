from app.memory.vector_db import vector_db

def remember_fact(fact: str) -> str:
    """
    Saves a crucial piece of information or user preference to long-term memory.
    Use this when the user explicitly asks you to remember something, or when they share
    important context that you should know for future interactions.
    
    Args:
        fact: The information to remember. Be descriptive and detailed.
    """
    try:
        vector_db.add_memory(fact, metadata={"source": "agent_tool"})
        return f"Successfully saved to long-term memory: '{fact}'"
    except Exception as e:
        return f"Failed to save memory: {str(e)}"

def search_memory(query: str) -> str:
    """
    Searches the long-term memory for relevant past conversations, facts, or preferences.
    Use this when you need context about the user or past events that is not in your immediate context.
    
    Args:
        query: The semantic search query to look for in memory.
    """
    try:
        results = vector_db.search_memory(query, n_results=5)
        if not results:
            return "No relevant memories found."
            
        formatted_results = "Retrieved Memories:\n"
        for i, res in enumerate(results):
            formatted_results += f"{i+1}. {res['text']}\n"
        return formatted_results
    except Exception as e:
        return f"Failed to search memory: {str(e)}"
