# ADR-0011: Session Context Contract

## Status

Accepted


# Context

Current Agent execution lifecycle:

RuntimeRequest

↓

AgentLoop

↓

Conversation

↓

Response


Conversation currently exists only during a single AgentLoop execution.

This prevents:

- multi-turn conversation
- session based history
- reusing previous messages


This ADR introduces a Session Layer.

The Session Layer only manages conversation history ownership.

It does not implement:

- Memory
- Vector Retrieval Memory
- Persistence
- Summarization
- Context Compression


---

# Decision

Introduce:

app/session


Dependency direction:

app.session

↓

app.conversation


Forbidden:

app.conversation

↓

app.session


Session Layer owns session lifecycle.

Conversation remains the message model owner.


---

# Module Structure


Create:


app/session/

    __init__.py

    models.py

    store.py

    service.py

    exceptions.py


---

# Session Model


Location:

app/session/models.py


Definition:


@dataclass(frozen=True)
class Session:

    session_id: str

    messages: tuple[Message, ...]


Rules:

## session_id

Must:

- be non-empty string
- preserve original value


Invalid:

empty string


Raises:

SessionError


---

## messages

Rules:

- tuple only
- preserve Message object identity
- preserve order
- no mutation after creation


---

Forbidden fields:

Do not add:

- user_id
- metadata
- timestamps
- expiration
- permissions


---

# Session Store Contract


Location:

app/session/store.py


Abstract:


class SessionStore:


async def get(
    session_id: str
) -> Session | None:


async def save(
    session: Session
) -> None:


Rules:

- abstract interface only
- no database dependency
- no persistence assumptions


---

# InMemorySessionStore


Same file:


class InMemorySessionStore(SessionStore)


Storage:

dict[str, Session]


Behavior:

- process memory only
- no serialization
- no automatic expiration


Rules:

get missing session:

return None


---

# Session Service


Location:

app/session/service.py


Class:


class SessionService:


Constructor:


SessionService(
    store: SessionStore
)


---

## get_or_create


Signature:


async def get_or_create(
    session_id: str
) -> Session


Behavior:


Existing:

return stored Session


Missing:

create:


Session(
    session_id=session_id,
    messages=()
)


save it


return it


---

## append_messages


Signature:


async def append_messages(
    session_id: str,
    messages: tuple[Message,...]
) -> Session


Behavior:


Existing messages:

+

new messages


Create new Session.


Do not mutate old Session.


---

# Exceptions


Location:

app/session/exceptions.py


Base:


class SessionError(Exception):
    pass


---

# AgentLoop Integration


Modify:

app/agents/loop.py


Add optional dependency:


session_service: SessionService | None


---

Compatibility requirement:


Existing:


AgentLoop(
    chat_service,
    tool_executor,
    tools
)


must continue working.


New:


AgentLoop(
    chat_service,
    tool_executor,
    tools,
    session_service
)


---

# Session Usage Rules


If session_service is None:


Current behavior unchanged.


If session_service exists:


Before execution:


1. Load session.

2. Use existing messages as initial conversation history.


After execution:


Save final messages.


---

# AgentLoop Ownership


AgentLoop does NOT:

- create SessionStore
- close SessionService
- persist externally


Lifecycle belongs to composition layer.


---

# Allowed Changes


Add:


app/session/__init__.py

app/session/models.py

app/session/store.py

app/session/service.py

app/session/exceptions.py


Tests:


tests/test_session_models.py

tests/test_session_store.py

tests/test_session_service.py


Modify:


app/agents/loop.py

tests/test_agent_loop.py


---

# Forbidden Changes


Do not modify:


app/runtime/

app/chat/

app/providers/

app/tools/

app/conversation/

app/rag/

app/retrievers/

app/vectorstores/

app/embeddings/


---

# Testing Requirements


## Session Model


Test:

- valid creation
- empty id rejection
- frozen behavior
- tuple messages
- message identity


---

## Session Store


Test:

- save
- get
- missing session
- multiple sessions isolation


---

## Session Service


Test:

- create new session
- load existing session
- append messages
- old session unchanged


---

## AgentLoop


Test:

- no SessionService keeps old behavior
- SessionService loads history
- final messages saved
- external dependencies not closed


---

# Acceptance Criteria


Must satisfy:


✓ Session Layer exists

✓ Conversation remains unchanged

✓ Runtime remains unchanged

✓ AgentLoop compatibility preserved

✓ Session history stored

✓ Old behavior preserved

✓ No Memory implementation

✓ No persistence

✓ Tests pass

✓ Ruff pass

✓ Black pass


---

# Commit Message


feat(session): add session context layer

---

# Amendment 1

Status:

Accepted


## 1. Session ID Source


Current AgentLoop API:


async def run(
    request: ChatRequest
) -> AgentResult


ChatRequest cannot be modified.


Therefore Session ID is provided through AgentLoop construction.


Add optional constructor dependency:


session_id: str | None


Example:


AgentLoop(
    chat_service,
    tool_executor,
    tools,
    max_iterations=5,
    session_service=session_service,
    session_id="session-001",
)


Rules:

- session_id belongs to Agent composition layer.
- AgentLoop does not generate session_id.
- Empty string is invalid.
- None means session disabled.


If session_service exists but session_id is None:

raise AgentLoopError.



---

## 2. AgentLoop Constructor Compatibility


Existing constructor:


AgentLoop(
    chat_service,
    tool_executor,
    tools,
    max_iterations=5,
)


Must remain valid.


Do NOT insert session_service before max_iterations.


New parameters must be keyword-only:


Example:


AgentLoop(
    chat_service,
    tool_executor,
    tools,
    max_iterations=5,
    session_service=session_service,
    session_id="abc",
)


Signature:


AgentLoop(
    chat_service,
    tool_executor,
    tools,
    max_iterations=5,
    *,
    session_service=None,
    session_id=None,
)



---

## 3. Session Save Strategy


AgentLoop must not duplicate history.


Before execution:


loaded_session.messages


are used as initial messages.


During execution:


AgentLoop maintains current conversation messages.


After successful completion:


save the complete final message history using:


SessionService.save_session()


or equivalent explicit replacement operation.


Do not call append_messages() with full history.



If SessionService only exposes append_messages():

it must be extended with an explicit replace/save operation.

The implementation must not duplicate previous messages.



---

## 4. Session Error Handling


Session errors:


SessionError


must be converted to:


AgentLoopError


while preserving exception chain:


raise AgentLoopError(...) from exc


This applies to:

- get_or_create failure
- save failure



---

## 5. Session Lifecycle


AgentLoop:

- owns no SessionStore
- creates no SessionService
- closes no SessionService


Composition layer manages lifecycle.



---

## 6. Allowed Changes Update


Modify:


app/session/service.py

if required to add explicit replacement save API.


Modify:


app/agents/loop.py


app/agents/models.py


tests


No changes:


app/runtime/

app/chat/

app/providers/

app/tools/

app/conversation/



---

## 7. Testing Update


Additional tests required:


Constructor:

- old positional max_iterations still works
- session_service must be keyword-only


Session:

- missing session_id rejected
- session history loaded
- final history saved once
- no duplicated messages


Errors:

- SessionError converted to AgentLoopError
- exception chain preserved
