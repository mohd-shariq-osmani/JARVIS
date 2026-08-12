# JARVIS — Complex Task & Multi-Step Agent Upgrade

## Objective

Upgrade the existing JARVIS implementation from a simple tool-calling assistant into a genuine agent capable of accomplishing unfamiliar, complex, multi-stage goals.

The core loop must become:

User Request
→ Understand
→ Decompose
→ Plan
→ Validate Plan
→ Execute Step
→ Observe Result
→ Evaluate
→ Recover / Adapt
→ Continue
→ Verify Final Result
→ Respond

Do NOT solve this merely by making the system prompt longer. Implement a real **Task Planning + Execution Engine**.

---

## 1. Inspect the Existing JARVIS First

Before changing code:

1. Inspect the current project architecture.
2. Identify the existing agent/orchestrator.
3. Identify the tool registry.
4. Identify the AI provider layer.
5. Identify voice/STT/TTS components.
6. Identify task handling.
7. Identify the event system.
8. Identify persistence/database code.
9. Determine exactly why complex tasks currently fail.
10. Preserve working functionality and refactor only where necessary.

Do not rewrite functioning components unnecessarily.

---

## 2. New Agent Architecture

Create or adapt the following subsystem:

```text
backend/app/agent/
    orchestrator.py
    planner.py
    executor.py
    observer.py
    evaluator.py
    recovery.py
    verifier.py
    task_state.py
    task_context.py
    task_events.py
```

Architecture:

```text
USER
  ↓
Intent Understanding
  ↓
Complexity Detector
  ├── SIMPLE → Direct Agent
  │
  └── COMPLEX
        ↓
      Planner
        ↓
   Plan Validator
        ↓
   Task Executor
        ↓
     Observer
        ↓
    Evaluator
        │
        ├── Success → Next Step
        ├── Retry → Retry Step
        ├── Replan → Planner
        ├── User Input → Wait
        └── Failure → Graceful Failure
        ↓
      Verifier
        ↓
     Completed
```

The LLM is the reasoning engine.

The application is the execution authority.

---

## 3. Task Model

Create a persistent structured Task object.

Example:

```json
{
  "id": "task_123",
  "goal": "Prepare a benchmark comparison and save it to Desktop",
  "status": "planning",
  "priority": "normal",
  "created_at": "...",
  "steps": [],
  "current_step": null,
  "context": {},
  "artifacts": [],
  "errors": [],
  "requires_confirmation": false
}
```

Supported states:

```text
CREATED
UNDERSTANDING
PLANNING
PLAN_VALIDATION
WAITING_FOR_CONFIRMATION
EXECUTING
OBSERVING
EVALUATING
RECOVERING
PAUSED
WAITING_FOR_USER
VERIFYING
COMPLETED
FAILED
CANCELLED
```

Persist task state in SQLite.

---

## 4. Task Step Model

Every step must have:

- ID
- Objective
- Tool
- Arguments
- Dependencies
- Expected result
- Actual result
- Status
- Retry count
- Error state
- Verification state
- Maximum attempts
- Retry strategy

Example:

```json
{
  "id": "step_3",
  "title": "Open benchmark result",
  "description": "Open the second credible benchmark result",
  "status": "pending",
  "tool": "browser.open",
  "arguments": {},
  "dependencies": ["step_1", "step_2"],
  "expected_result": "Benchmark page is loaded",
  "actual_result": null,
  "attempts": 0,
  "max_attempts": 2,
  "retryable": true
}
```

---

## 5. Use a Task Graph, Not Just a List

Complex tasks must support dependencies and branching.

Example:

```text
Search web
   │
   ├── Result A ──┐
   ├── Result B ──┼──→ Compare → Summarize → Save → Verify
   └── Result C ──┘
```

Represent this internally as a DAG/task graph where appropriate.

Independent safe steps may execute concurrently.

Dependent or conflicting steps must execute sequentially.

---

## 6. Planner

The planner must determine:

1. Actual user goal
2. Required information
3. Required tools
4. Required steps
5. Step dependencies
6. Steps that can run in parallel
7. Dangerous operations
8. Confirmation requirements
9. Success criteria
10. Verification strategy

Do not execute until the plan is valid.

The planner must return structured JSON, not free-form prose.

Example:

```json
{
  "goal": "Find and compare RTX 5090 benchmark results",
  "success_criteria": [
    "At least 3 credible sources analyzed",
    "Performance metrics extracted",
    "Comparison generated",
    "Summary saved to Desktop",
    "Saved file verified"
  ],
  "steps": [
    {
      "id": "1",
      "action": "browser.search",
      "arguments": {
        "query": "RTX 5090 benchmarks"
      },
      "depends_on": []
    }
  ]
}
```

Validate the plan against a schema before execution.

If invalid, request structured repair from the model.

Never execute malformed plans.

---

## 7. Task Context

Create a TaskContext containing:

```text
user_goal
plan
current_step
completed_steps
failed_steps
tool_results
observations
artifacts
important_facts
user_preferences
permissions
environment_state
variables
```

Example:

```json
{
  "variables": {
    "search_results": [],
    "selected_sources": [],
    "summary": null,
    "output_file": null
  }
}
```

Steps must be able to reference outputs from previous steps.

Example:

```text
browser.open(url={{search_results[0].url}})
```

---

## 8. Tool Results Become Task Context

Do not use:

```text
Tool → result → final response
```

Use:

```text
Tool
 ↓
Structured result
 ↓
TaskContext
 ↓
Evaluator
 ↓
Next step
```

Example:

```json
{
  "success": true,
  "data": {
    "url": "...",
    "title": "...",
    "text": "..."
  }
}
```

Store results in TaskContext so subsequent steps can consume them.

---

## 9. Observation Loop

Do not assume an action succeeded just because the tool returned successfully.

Use:

```text
Action
 ↓
Result
 ↓
Observe actual environment
 ↓
Evaluate
 ↓
Continue / Retry / Replan
```

For computer/UI actions:

```text
Action
 ↓
Screenshot or UI state
 ↓
Vision/UI analysis
 ↓
Compare with expected state
```

Example:

```text
Open Chrome
 ↓
Observe
 ↓
Is Chrome actually open?
 ├── YES → Continue
 └── NO → Recovery
```

---

## 10. Expected Results

Every important step should define an expected result.

Example:

```text
Action:
Click "Download"

Expected:
Download begins or confirmation appears.
```

Compare expected state with observed state.

If they do not match, invoke recovery or replanning.

---

## 11. Evaluator

Create:

```text
TaskEvaluator
```

Responsibilities:

- Determine step success
- Determine whether task can continue
- Detect incorrect results
- Detect missing information
- Detect unexpected UI state
- Decide whether retry is safe
- Decide whether replanning is required
- Decide whether user intervention is required

The evaluator must not blindly trust the tool result.

---

## 12. Recovery Engine

Create:

```text
RecoveryEngine
```

Failure flow:

```text
Failure
  ↓
Classify
  ↓
Can retry?
 ├── YES → Retry
 └── NO
      ↓
Can use alternate method?
 ├── YES → Replan
 └── NO
      ↓
Ask user / Fail gracefully
```

Failure categories:

```text
TEMPORARY
INVALID_ARGUMENT
TOOL_FAILURE
APPLICATION_STATE
NETWORK
PERMISSION
MISSING_INFORMATION
MODEL_ERROR
ENVIRONMENT_ERROR
UNKNOWN
```

Do not blindly retry.

Default maximum attempts: 2.

Examples:

```text
Network timeout → retry

Chrome not found → use another browser or replan

Permission denied → ask user

File already exists → ask user or choose safe alternative

Wrong UI state → observe and replan
```

---

## 13. Dynamic Replanning

JARVIS must be able to change the plan when reality differs from the original plan.

Example:

Original:

```text
Open Chrome
Search Google
Click first result
```

Chrome is unavailable.

JARVIS should determine:

```text
Chrome unavailable.
Edge is installed.
Edge can accomplish the same task.
```

New plan:

```text
Open Edge
Search Google
Click result
```

Validate the new plan before execution.

Do not simply fail because the original plan became impossible.

---

## 14. Partial Success

Tasks should not always be binary.

Example:

User asks to compare five sources.

One source is unavailable.

JARVIS should be able to:

```text
4/5 sources analyzed
1 source unavailable
```

Then determine whether:

- The task can still be completed
- Another source should be found
- The user needs to be informed

Do not fail the whole task unnecessarily.

---

## 15. Human-in-the-Loop

The planner must identify dangerous actions before execution.

Example:

```text
Plan:
1. Search files
2. Select files
3. Delete files
```

Before deletion:

```text
CONFIRMATION REQUIRED

JARVIS plans to permanently delete 18 files.

[Cancel] [Approve]
```

Do not ask for confirmation for harmless operations.

Permission classes:

```text
READ_ONLY
LOW_RISK
USER_IMPACT
DANGEROUS
BLOCKED
```

Examples:

No confirmation:

- Get GPU usage
- Search web
- Open Chrome
- Read a file
- Take screenshot

Confirmation:

- Delete files
- Send email
- Move important files
- Install software
- Shutdown
- Execute privileged commands

The LLM cannot grant itself permission.

Only PermissionManager can authorize execution.

---

## 16. Parallel Execution

Independent operations may execute concurrently.

Example:

```text
Get CPU stats ────────┐
Get GPU stats ────────┼──→ Generate report
Get RAM stats ────────┘
```

Never parallelize conflicting operations.

Only one foreground computer-control task should normally control the mouse/keyboard at a time.

---

## 17. Foreground and Background Tasks

Support:

```text
FOREGROUND
BACKGROUND
```

Foreground:

- Computer control
- Browser automation
- UI interaction

Background:

- System monitoring
- Memory indexing
- Scheduled tasks
- Safe research

Prevent multiple foreground tasks from fighting over the same UI.

---

## 18. Long-Running Tasks

The UI must show progress.

Example:

```text
TASK IN PROGRESS

Goal:
Prepare benchmark report

Progress:
██████████████░░░░ 72%

Completed:
✓ Search
✓ Source 1
✓ Source 2
✓ Source 3

Current:
→ Source 4

Remaining:
○ Source 5
○ Compare
○ Generate report
○ Save
○ Verify

[Pause] [Cancel] [View Details]
```

Allow the user to:

- Pause
- Resume
- Cancel
- Inspect the plan
- Ask JARVIS what it is doing
- Modify the task

---

## 19. User Intervention

If JARVIS needs the user:

```text
WAITING_FOR_USER
```

Example:

> I need you to complete the login in the browser.

After the user finishes:

```text
Continue
```

Resume from the exact paused step.

---

## 20. Task Modification

Support natural commands during execution:

```text
Pause
Resume
Stop
Skip this step
Skip this website
Try another method
Use Edge instead
Don't save the report
Save it as PDF instead
```

Translate these into task modifications.

---

## 21. Task Persistence

If JARVIS closes during a long task, persist state in SQLite.

On restart:

```text
A previous task was interrupted.

Task:
Prepare benchmark report

Progress:
7/11 steps completed

[Resume] [Discard]
```

Never automatically resume dangerous operations.

---

## 22. Artifact Manager

Create:

```text
ArtifactManager
```

Artifacts may include:

- Files
- URLs
- Screenshots
- Images
- Extracted text
- Reports
- Generated audio
- Generated images

Example:

```json
{
  "id": "artifact_01",
  "type": "file",
  "path": "C:/Users/User/Desktop/report.md",
  "created_by": "step_12"
}
```

Tasks can reference artifacts.

---

## 23. Final Verification

Never tell the user "Done" until the task is verified.

Example:

```text
Folder exists? YES
Files exist? YES
Files are inside folder? YES
Original locations empty? YES
```

Only then mark the task completed.

Create:

```text
TaskVerifier
```

Input:

```text
User goal
Success criteria
Task plan
Completed steps
Artifacts
Observed state
```

Output:

```json
{
  "verified": true,
  "confidence": 0.97,
  "missing": [],
  "warnings": []
}
```

If `verified = false`, do not claim completion. Replan or report the incomplete state.

---

## 24. Agent Execution Loop

Implement the following architecture:

```python
while not task.is_terminal():

    if task.cancelled:
        cancel()

    if task.paused:
        wait()

    if task.waiting_for_user:
        wait()

    if task.needs_replanning:
        plan = planner.replan(task_context)
        validate(plan)

    step = executor.next_ready_step(task)

    if step.requires_confirmation:
        request_confirmation()
        continue

    result = executor.execute(step)

    task_context.store(result)

    observation = observer.observe(step, result)

    evaluation = evaluator.evaluate(
        step,
        result,
        observation,
        task_context
    )

    if evaluation.success:
        mark_step_complete()

    elif evaluation.retry:
        retry_step()

    elif evaluation.replan:
        task.needs_replanning = True

    elif evaluation.wait_for_user:
        task.waiting_for_user = True

    else:
        fail_or_continue()

    if all_success_criteria_met():
        verification = verifier.verify(task)

        if verification.verified:
            complete_task()
        else:
            replan()
```

Adapt this to the existing codebase. Do not blindly copy it.

---

## 25. Keep LLM and Application Responsibilities Separate

The LLM should handle:

- Intent understanding
- Planning
- Tool selection
- Reasoning
- Evaluation
- Recovery decisions
- Natural-language responses

The application should handle:

- Task state
- Permissions
- Scheduling
- Tool execution
- Retries
- Persistence
- Cancellation
- Verification
- Security

The application must remain the authority.

---

## 26. Context Management

Do not send the entire task history to the LLM on every turn.

Construct compact context containing:

```text
TASK GOAL
SUCCESS CRITERIA
CURRENT STEP
RELEVANT VARIABLES
RECENT TOOL RESULTS
CURRENT OBSERVATION
RELEVANT MEMORY
KNOWN ERRORS
```

Summarize older completed steps.

Keep the full history in SQLite.

This prevents context-window explosion.

---

## 27. Complexity Detection

Existing simple commands must remain fast.

Create:

```text
SIMPLE_MODE
COMPLEX_MODE
```

Examples:

```text
"Open Chrome."
→ SIMPLE

"Check my GPU."
→ SIMPLE

"Search for RTX 5090 benchmarks."
→ SIMPLE

"Search for benchmarks, compare 5 sources, create a report,
save it, and email it to me."
→ COMPLEX
```

Detect complexity semantically, considering:

- Number of actions
- Number of tools
- Dependencies
- Need for memory
- Need for observation
- Need for confirmation
- External information
- Multi-stage language
- Conditional logic
- Expected artifacts

Do not rely only on word count.

Simple tasks should use the lightweight path.

Complex tasks should automatically enter the full Task Execution Engine.

---

## 28. Plan Visibility

Add a collapsible Task Plan panel.

Example:

```text
TASK PLAN

✓ Search web
✓ Select sources
✓ Analyze source 1
✓ Analyze source 2
→ Analyze source 3
○ Analyze source 4
○ Compare results
○ Generate report
○ Save report
○ Verify report
```

Do not expose hidden chain-of-thought.

Only display concise actionable steps and status.

---

## 29. Resource Awareness

The task engine should know the environment.

Example:

```text
GPU VRAM:
14.7 / 16 GB

LM Studio:
Running

ComfyUI:
Running

Available RAM:
3.1 GB
```

If the system is under load, adapt.

Example:

> ComfyUI is using most of the GPU memory. I'll avoid starting another GPU-heavy model.

---

## 30. Example Complex Tasks

### Research + File

> Open Chrome, search for the latest RTX 5090 benchmarks, compare the first three credible results, summarize the performance differences, save the summary to my Desktop, and tell me where you saved it.

Expected dynamic workflow:

```text
Open browser
→ Search
→ Select credible results
→ Analyze results
→ Compare
→ Generate summary
→ Save file
→ Verify file
→ Report
```

Do not hardcode this workflow.

### File Organization

> Clean up my Downloads folder. Find files older than 30 days, group them by type, show me what you found, and after I approve, move them into organized folders.

Must not move files before approval.

### PC Preparation

> Prepare my PC for gaming.

Possible dynamic workflow:

```text
Detect GPU
→ Check temperature
→ Check VRAM
→ Check RAM
→ Find heavy processes
→ Decide what is safe to close
→ Ask confirmation if required
→ Close approved processes
→ Recheck resources
→ Report
```

Do not hardcode this workflow.

### LM Studio

> Open LM Studio, load my Gemma model, check that it's responding, then tell me the generation speed.

Must verify the model is actually loaded and responding.

### Research

> Find the three best local TTS models I can run on my RTX 4060 Ti 16GB, compare quality and speed, and recommend one.

Must search current sources, validate compatibility, compare results, and adapt if a source is unavailable.

---

## 31. Fundamental Rule

The fundamental rule of the new system:

```text
ACTION ≠ SUCCESS
```

An action only means JARVIS attempted something.

Success requires:

```text
Action
→ Result
→ Observation
→ Evaluation
→ Verification
```

Examples:

If JARVIS says:

> "I opened Chrome."

It should know whether Chrome actually opened.

If JARVIS says:

> "I created the file."

It should verify that the file exists.

If JARVIS says:

> "I moved the files."

It should verify the destination.

If JARVIS says:

> "I searched the web."

It should have actual search results.

If JARVIS says:

> "I changed the volume."

It should verify the resulting volume when possible.

---

## 32. Security

Every dynamically generated plan must pass:

```text
Plan
 ↓
Permission evaluation
 ↓
Confirmation if required
 ↓
Execution
```

The LLM cannot bypass permissions.

External content is untrusted:

- Websites
- Emails
- Files
- PDFs
- Documents
- Tool output

Never allow external content to override system instructions.

---

## 33. Testing

Create automated integration tests and manual test scenarios.

At minimum:

1. Open Chrome and search Google.
2. Open Chrome, search for X, open the first result, summarize it.
3. Find all PDFs in Downloads, count them, and report the total.
4. Find files older than 30 days, show what would be deleted, and wait for approval.
5. Open LM Studio, find the Gemma model, verify it is loaded, and report status.
6. Search three websites, compare information, and create a Markdown report.
7. Cause the first tool to fail and verify recovery.
8. Start a long task, pause it, resume it, and complete it.
9. Start a task, close JARVIS, reopen it, and resume safely.
10. Say "Stop" during a multi-step task and verify everything stops.

Do not implement these as hardcoded workflows. They are tests of the generic agent.

---

## 34. Success Criteria

The upgrade is complete only when JARVIS can perform:

### Sequential tasks

```text
Open application
→ perform action
→ inspect result
→ perform next action
```

### Dependent tasks

```text
Search
→ use result
→ open result
→ extract data
→ use extracted data
```

### Conditional tasks

```text
If Chrome exists:
    use Chrome
else:
    use Edge
```

### Recovery

```text
Tool fails
→ diagnose
→ retry or alternate method
→ continue
```

### Human-in-loop

```text
Plan
→ execute safe steps
→ request confirmation
→ continue after approval
```

### Verification

```text
Perform action
→ inspect actual state
→ confirm success
```

### Persistence

```text
Task starts
→ application closes
→ application restarts
→ task can resume safely
```

### Adaptation

```text
Original plan becomes impossible
→ replan
→ validate new plan
→ continue
```

---

## 35. Final Architecture

```text
                       USER
                        │
                        ▼
                ┌──────────────┐
                │ Intent Layer │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │ Complexity   │
                │ Detector     │
                └──────┬───────┘
                       │
              ┌────────┴────────┐
              │                 │
           SIMPLE             COMPLEX
              │                 │
              ▼                 ▼
        Direct Agent       Task Planner
                                │
                                ▼
                         Plan Validator
                                │
                                ▼
                         Task Executor
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
                 Tools                  Observer
                    │                       │
                    └───────────┬───────────┘
                                ▼
                           Evaluator
                                │
                     ┌──────────┼──────────┐
                     │          │          │
                   Done       Retry      Replan
                     │          │          │
                     │          └────┬─────┘
                     │               │
                     │               ▼
                     │          Task Executor
                     │
                     ▼
                  Verifier
                     │
                     ▼
                 Completed
```

---

# Final Instruction to Gemini 3.1 Pro

Do not merely modify the system prompt.

This requires **real architectural changes**.

Inspect the existing JARVIS implementation first.

Then:

1. Identify the current agent architecture.
2. Identify why multi-step tasks currently fail.
3. Design the Task Execution Engine.
4. Implement structured task planning.
5. Implement task state.
6. Implement dependencies.
7. Implement execution.
8. Implement observation.
9. Implement evaluation.
10. Implement retry/recovery.
11. Implement replanning.
12. Implement verification.
13. Implement persistence.
14. Implement task cancellation.
15. Implement task pause/resume.
16. Implement human-in-the-loop confirmation.
17. Add the Task Center UI.
18. Add comprehensive tests.

Do not break existing simple commands.

Do not replace working components unnecessarily.

Do not hardcode example workflows.

The final system must be able to receive an unfamiliar complex request and dynamically decompose it into executable steps, execute those steps, observe the real result, recover from failures, adapt its plan, and verify the final outcome.

The goal is:

**JARVIS should not merely know how to call tools.**

**JARVIS should know how to accomplish goals.**
