# AGENTS.md

# GLOBAL OPERATING CONTRACT

This document defines mandatory operating rules.

These rules apply unless explicitly overridden by the user.

## 1. Mission
Deliver the correct solution with the smallest safe change.

Priority:
1. Correctness
2. Safety
3. Maintainability
4. Compatibility
5. Performance
6. Readability

## 2. Engineering Mindset
Understand → Investigate → Verify → Plan → Implement → Validate → Summarize

Never assume.
Never guess.

## 3. Source of Truth
Implementation > Tests > Configuration > Documentation > Comments

## 4. Investigation Rules
Inspect only relevant files.
Never scan the repository unless necessary.
Ignore:
- node_modules
- vendor
- dist
- build
- target
- coverage
- generated code

## 5. Planning
Identify:
- affected files
- dependencies
- risks
- validation strategy

## 6. Scope Control
Smallest safe change wins.
No unrelated refactoring.

## 7. Decision Rules
Prefer:
- simple
- consistent
- testable
- maintainable

## 8. Validation
Compile
→ Targeted tests
→ Integration tests
→ Full suite (only when required)

## 9. Failure Policy
If confidence <90%:
Stop.
Explain.
Ask.

## 10. Token Efficiency
Never:
- scan entire repository
- repeat previous analysis
- inspect unrelated modules
- perform unnecessary tests

## 11. Approval Gates
Require approval for:
- architecture
- database schema
- Docker
- dependencies
- authentication
- CI/CD
- public APIs

## 12. Output
Summary
Modified Files
Validation
Risks
Next Step

## Git Policy

Codex must never execute git push unless explicitly requested.

Codex may:

- inspect git status
- inspect git diff
- suggest commit messages

The user is responsible for:

- git add
- git commit
- git push

## Architecture Conflict

If implementation conflicts with existing public contracts:

1. Stop implementation immediately.

2. Produce an Architecture Report.

3. Do NOT modify existing stable APIs.

4. Wait for an Architecture Decision (ADR).

Only continue after the ADR is approved.

# Architecture Decision Record (ADR) Workflow

## Purpose

All architecture decisions that affect public contracts, module boundaries,
dependency direction, data models, APIs, or execution flow must be recorded as
repository files before implementation.

Chat discussion, temporary notes, or external instructions are not considered
the source of truth.

## ADR Storage

All ADR documents must be stored under:

`docs/adr/`

Naming convention:

`ADR-XXXX-short-description.md`

Example:

`docs/adr/ADR-0010-agent-state-machine.md`

## ADR Requirements

An ADR must define:

- Status
- Context
- Decision
- Module ownership
- Dependency direction
- Public contracts
- Data models
- Function signatures
- Default values
- Validation rules
- Allowed changes
- Forbidden changes
- Testing requirements
- Risks

## ADR Implementation Rules

Before implementing architecture-related changes:

1. Locate referenced ADR files in repository.
2. Read complete ADR content.
3. Verify required contracts exist.
4. Confirm allowed and forbidden changes.

If ADR file does not exist:

- Stop implementation.
- Report missing ADR.
- Do not infer architecture from chat history.
- Do not create public APIs by guessing.

## Never Guess Rule

Never guess:

- public APIs
- class fields
- dependency direction
- module ownership
- migration strategy
- state transitions
- error handling behavior

When information is missing:

1. Stop implementation.
2. Create Architecture Report.
3. Describe conflict.
4. Request ADR clarification.

## ADR Source of Truth

Priority order:

1. Repository ADR files (`docs/adr/*.md`)
2. Existing source code contracts
3. Existing tests
4. Task specification

Chat messages are not considered authoritative architecture documents unless
converted into repository ADR files.

## ADR Amendment Rules

When implementation discovers architecture conflicts:

1. Stop coding.
2. Create Architecture Report.
3. Propose ADR Amendment.
4. Update ADR document.
5. Continue implementation only after ADR is updated.

## Architecture Review Gate

Architecture changes must follow:

```text
ADR exists
    ↓
ADR reviewed
    ↓
Implementation
    ↓
Tests
    ↓
Architecture Review
```

No architecture implementation may bypass this sequence.
