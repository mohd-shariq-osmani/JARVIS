from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class TaskState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    WAITING_FOR_USER = "WAITING_FOR_USER"

class TaskStep(BaseModel):
    id: str = Field(description="Unique identifier for the step (e.g. step_1)")
    description: str = Field(description="Actionable description of what to accomplish")
    dependencies: List[str] = Field(default_factory=list, description="IDs of steps that must complete before this one")
    completed: bool = Field(default=False)
    result: Optional[str] = None
    error: Optional[str] = None

class TaskPlan(BaseModel):
    objective: str = Field(description="Overall goal of the task")
    steps: List[TaskStep] = Field(description="List of steps to accomplish the goal in order")

class EvaluationVerdict(str, Enum):
    SUCCESS = "SUCCESS"
    RETRY = "RETRY"
    REPLAN = "REPLAN"
    FAIL = "FAIL"

class EvaluationResult(BaseModel):
    verdict: EvaluationVerdict = Field(description="The outcome of evaluating the step")
    reasoning: str = Field(description="Explanation for the verdict")

class VerificationResult(BaseModel):
    verified: bool = Field(description="True if the overall goal was accomplished")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    missing: List[str] = Field(default_factory=list, description="List of missing criteria")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    reasoning: str = Field(description="Explanation for the verification outcome")

class TaskContext(BaseModel):
    state: TaskState = TaskState.PENDING
    plan: Optional[TaskPlan] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)
    memory_context: str = ""
