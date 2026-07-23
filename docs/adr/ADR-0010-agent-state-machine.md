# ADR-0010: Agent Execution State Machine

## Status

Accepted

## Context

Current `AgentLoop` uses bounded iteration:

```python
for range(max_iterations)
```

The loop already supports:

- ChatService call
- ToolCall execution
- ToolMessage feedback
- Final response

This ADR introduces explicit execution state tracking.

This change must not alter:

- Tool Calling behavior
- Provider call count
- `max_iterations` semantics
- Conversation lifecycle

## Decision

Introduce `AgentExecutionState`.

Do not modify:

```text
runtime.state.AgentState
```

Agent state belongs to:

```text
app.agents
```

## AgentPhase

Location:

```text
app/agents/state.py
```

Definition:

```python
class AgentPhase(str, Enum):
    INIT = "init"
    THINKING = "thinking"
    TOOL_EXECUTION = "tool_execution"
    OBSERVATION = "observation"
    FINISHED = "finished"
    FAILED = "failed"
```

Only these states are allowed.

## AgentExecutionState

Location:

```text
app/agents/models.py
```

Definition:

```python
@dataclass(frozen=True)
class AgentExecutionState:
    phase: AgentPhase
    messages: tuple[Message, ...]
    iteration: int
```

Rules:

- frozen
- no dependency references
- no request field
- no response field
- no provider field
- no executor field

`iteration` means Provider call count.

## AgentStateMachine

Location:

```text
app/agents/state_machine.py
```

Constructor:

```python
AgentStateMachine(
    initial_state: AgentExecutionState
)
```

Properties:

```python
state -> AgentExecutionState
```

Method:

```python
transition(
    next_phase: AgentPhase,
    *,
    messages: tuple[Message, ...] | None = None,
    iteration: int | None = None,
)
```

Behavior:

- create new `AgentExecutionState`
- replace current state
- do not mutate old state

## Transition Rules

Allowed:

```text
INIT
 -> THINKING

THINKING
 -> TOOL_EXECUTION

THINKING
 -> FINISHED

TOOL_EXECUTION
 -> OBSERVATION

OBSERVATION
 -> THINKING

Any non-terminal state
 -> FAILED
```

Forbidden:

```text
FINISHED -> THINKING
FINISHED -> TOOL_EXECUTION
FAILED -> THINKING
FAILED -> TOOL_EXECUTION
```

## Exception

Location:

```text
app/agents/exceptions.py
```

Add:

```python
class AgentStateError(AgentLoopError):
    pass
```

Illegal transitions raise `AgentStateError`.

## AgentLoop Integration

Location:

```text
app/agents/loop.py
```

Keep:

```python
for range(max_iterations)
```

Do not replace with `while`.

Initial state:

```python
AgentExecutionState(
    phase=AgentPhase.INIT,
    messages=(),
    iteration=0,
)
```

Flow:

```text
INIT
  |
  v
THINKING
  |
  v
ChatService
```

If ToolCall:

```text
THINKING
  |
  v
TOOL_EXECUTION
```

Tool finished:

```text
TOOL_EXECUTION
  |
  v
OBSERVATION
```

Continue:

```text
OBSERVATION
  |
  v
THINKING
```

Final answer:

```text
THINKING
  |
  v
FINISHED
```

Exception:

```text
ANY
  |
  v
FAILED
```

Then re-raise the original exception.

## AgentResult

Extend:

```python
final_state: AgentExecutionState
```

Final result contains:

- response
- messages
- final_state

## Allowed Changes

Add:

```text
app/agents/state.py
app/agents/state_machine.py
tests/test_agent_state.py
tests/test_agent_state_machine.py
```

Modify:

```text
app/agents/models.py
app/agents/loop.py
app/agents/__init__.py
tests/test_agent_loop.py
```

## Forbidden Changes

Do not modify:

```text
app/runtime/
app/chat/
app/providers/
app/tools/
app/conversation/
app/rag/
app/retrievers/
app/vectorstores/
app/embeddings/
```

Do not implement:

- Memory
- Persistence
- Resume
- Planner
- ReAct
- Multi Agent

## Tests

Must cover:

### AgentPhase

- members
- values

### AgentExecutionState

- create
- frozen
- fields

### StateMachine

- valid transitions
- invalid transitions

### AgentLoop

- FINISHED state
- FAILED state
- tool loop state changes
- iteration unchanged

## Commit Message

```text
feat(agent): add agent state machine
```
