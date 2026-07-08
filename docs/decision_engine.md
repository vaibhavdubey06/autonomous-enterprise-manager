# Decision Engine
## Purpose
To dynamically decompose complex user intents into executable sub-tasks (Plans).

## Architecture
Injected as a node inside the LangGraph. Connects to the LLM Gateway with specific prompting for structural decomposition.

## Flow
Receives query -> Fetches contextual tools -> LLM generates JSON plan -> Planner Node parses and queues sub-tasks into Graph State.

## Extension Points
Modify the planner prompt template, or implement alternative Planner nodes (e.g., ReAct vs. Plan-and-Solve).
