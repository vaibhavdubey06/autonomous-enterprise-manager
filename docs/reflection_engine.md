# Reflection Engine
## Purpose
Self-correcting node that evaluates an Agent's output against the user's goal.

## Architecture
Operates post-execution. Uses a secondary LLM call to grade the output (Pass/Fail) and generate critique.

## Flow
Agent executes task -> State moves to Reflector -> Reflector outputs Pass/Fail -> If Fail, loop back to Agent with Critique -> If Pass, proceed to End.

## Extension Points
Add strict programmatic guardrails (Regex, JSON schema validation) alongside LLM reflection.
