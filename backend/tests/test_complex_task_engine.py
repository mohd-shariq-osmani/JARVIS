import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.agent.complexity import ComplexityDetector
from app.agent.planner import TaskPlanner
from app.agent.engine import TaskEngine
from app.agent.models import TaskContext, TaskState
from app.tools.registry import ToolRegistry
from app.tools.system_tools import register_system_tools
from app.tools.files import register_file_tools

# Mock AI provider for structured validation and deterministic testing
class MockAIProvider:
    async def generate_structured(self, messages, schema, model=None):
        prompt_text = str(messages)
        if "Classify this request" in prompt_text:
            if "simple" in prompt_text.lower() or "turn off wi-fi" in prompt_text.lower():
                return {"is_complex": False, "reason": "Single simple action"}
            return {"is_complex": True, "reason": "Multi-step complex workflow"}
        elif "Task Planner" in prompt_text:
            return {
                "objective": "Inspect system resources and save log",
                "steps": [
                    {"id": "step_1", "description": "Check current CPU and GPU usage", "dependencies": []},
                    {"id": "step_2", "description": "Save the resource status to a log file", "dependencies": ["step_1"]}
                ]
            }
        elif "Task Evaluator" in prompt_text:
            return {"verdict": "SUCCESS", "reasoning": "Step executed successfully"}
        elif "Final Verifier" in prompt_text:
            return {"verified": True, "confidence": 0.95, "missing": [], "warnings": [], "reasoning": "All steps met"}
        return {}

    async def generate_with_tools(self, messages, tools, model=None):
        return {"tool_calls": [{"id": "call_1", "function": {"name": "get_cpu_usage", "arguments": "{}"}}]}

    async def chat(self, messages, model=None):
        return "Task finished: Inspected CPU/GPU and created system log report."

async def test_complex_task_workflow():
    print("=== 1. Testing Complexity Detector ===")
    ai = MockAIProvider()
    detector = ComplexityDetector(ai)
    
    is_simple = await detector.detect("Turn off Wi-Fi")
    print("Simple detection result:", is_simple)
    assert is_simple is False
    
    is_complex = await detector.detect("Clean up my Downloads folder and group files by type, and then create a summary report.")
    print("Complex detection result:", is_complex)
    assert is_complex is True

    print("=== 2. Testing Task Planner Decomposition ===")
    planner = TaskPlanner(ai)
    context = TaskContext(state=TaskState.PENDING, memory_context="User is on Windows")
    plan = await planner.plan("Check resources and save report", context, {})
    print(f"Generated Plan: '{plan.objective}' with {len(plan.steps)} steps:")
    for s in plan.steps:
        print(f"  - [{s.id}] {s.description} (deps: {s.dependencies})")
    assert len(plan.steps) == 2
    assert plan.steps[1].dependencies == ["step_1"]

    print("=== 3. Testing Task Engine Execution Loop ===")
    registry = ToolRegistry()
    register_system_tools(registry)
    register_file_tools(registry)
    
    engine = TaskEngine(ai, registry)
    result = await engine.execute_task("Inspect system resources and save log", "User preference: fast")
    print("Complex Task Engine Result:\n", result)
    assert "Task finished" in result

    print("\n ALL COMPLEX TASK ENGINE TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(test_complex_task_workflow())
