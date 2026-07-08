# Connectors
## Purpose
Native, secure wrappers around external Enterprise systems (GitHub, Slack, Jira).

## Architecture
`BaseConnector` interface with concrete implementations handling auth, rate-limiting, and error recovery.

## Flow
Agent decides to use Connector -> Connector fetches Auth token from `CredentialManager` -> Executes API call -> Returns parsed data.

## Extension Points
Subclass `BaseConnector` to add support for new platforms (e.g., Salesforce, ServiceNow).
