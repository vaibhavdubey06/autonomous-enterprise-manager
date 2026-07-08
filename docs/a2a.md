# Agent-to-Agent (A2A) Platform
## Purpose
Enables autonomous collaboration between distinct agents.

## Architecture
A registry-based service discovery pattern where agents expose capabilities via APIs.

## Flow
Agent A needs specialized task -> Queries A2A Registry -> Discovers Agent B -> Dispatches sub-request -> Awaits result.

## Extension Points
Implement network adapters to call agents across different microservices.
