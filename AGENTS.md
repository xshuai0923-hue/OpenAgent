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
