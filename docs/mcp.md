# Model Context Protocol (MCP)
## Purpose
Standardizes how LLMs consume and interact with arbitrary enterprise data sources and tools.

## Architecture
A unified interface translating internal tool definitions into MCP-compliant JSON schema.

## Flow
Agent requests tool -> MCP Adapter formats request -> Calls external MCP server -> Parses response to agent.

## Extension Points
Register new external MCP servers in the Configuration system.
