import os
import shutil
import logging

logger = logging.getLogger("FileTools")

# Safe Sandbox Directory
SANDBOX_DIR = os.path.join(os.path.expanduser("~"), "JARVIS_SANDBOX")
os.makedirs(SANDBOX_DIR, exist_ok=True)

def _is_safe(path: str) -> bool:
    """Ensure the path resolves to somewhere inside the sandbox."""
    abs_path = os.path.abspath(path)
    return abs_path.startswith(os.path.abspath(SANDBOX_DIR))

async def read_file(filename: str) -> str:
    path = os.path.join(SANDBOX_DIR, filename)
    if not _is_safe(path): return "Error: Access denied outside sandbox."
    if not os.path.exists(path): return "Error: File not found."
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

async def write_file(filename: str, content: str) -> str:
    path = os.path.join(SANDBOX_DIR, filename)
    if not _is_safe(path): return "Error: Access denied outside sandbox."
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {filename}"
    except Exception as e:
        return f"Error writing file: {e}"

async def list_files() -> str:
    try:
        files = os.listdir(SANDBOX_DIR)
        if not files: return "Sandbox is empty."
        return "\n".join(files)
    except Exception as e:
        return f"Error listing directory: {e}"

def register_file_tools(registry):
    registry.register(
        name="read_file",
        description="Reads a file from the JARVIS safe sandbox directory",
        parameters={"type": "object", "properties": {"filename": {"type": "string"}}, "required": ["filename"]},
        func=read_file,
        permission_level=1
    )
    
    registry.register(
        name="write_file",
        description="Writes content to a file in the JARVIS safe sandbox directory",
        parameters={"type": "object", "properties": {"filename": {"type": "string"}, "content": {"type": "string"}}, "required": ["filename", "content"]},
        func=write_file,
        permission_level=2
    )

    registry.register(
        name="list_sandbox_files",
        description="Lists all files in the JARVIS safe sandbox directory",
        parameters={"type": "object", "properties": {}},
        func=list_files,
        permission_level=0
    )
