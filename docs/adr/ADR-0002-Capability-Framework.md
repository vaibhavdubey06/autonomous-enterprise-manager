# ADR 0002: Enterprise Capability Framework

**Date**: 2026-06-27
**Status**: Accepted

## Context
Executive Agents (like the CTO Agent) initially interacted directly with external services, such as the `KnowledgeAgent` or GitHub. This created tight coupling and violated the Open/Closed principle, as adding new tools (Slack, Jira, etc.) required modifying the agent's core execution loop. Furthermore, observability, authorization, and error handling were scattered.

## Decision
We introduced the **Enterprise Capability Framework** as the standard execution layer for the Autonomous Enterprise Manager. 
- **`BaseCapability`**: Provides a standard interface enforcing authorization, input validation, execution, and output validation.
- **`CapabilityRegistry`**: Centralizes the registration and discovery of capabilities.
- **`CapabilityExecutor`**: Acts as a central chokepoint. All capabilities are invoked via the executor, which standardizes error handling and observability metrics.

## Consequences
- **Positive**: Executive Agents are completely decoupled from the tools they use. Adding a new tool (e.g., Jira) only requires registering it in the `CapabilityRegistry`.
- **Positive**: The Supervisor Agent can now dynamically inject capability requirements (e.g., `github_tool`) into execution plans.
- **Negative**: Increased abstraction overhead. Simple tool calls now pass through multiple layers (`Agent -> Executor -> Registry -> Capability -> External System`).
