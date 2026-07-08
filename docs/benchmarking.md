# Benchmarking Framework
## Purpose
To continuously evaluate the platform's AI Quality, Runtime health, and Infrastructure resilience via procedurally generated E2E scenarios.

## Architecture
`ScenarioFactory` -> `E2ERunner` -> Validators (Subsystem Coverage, Playwright TTFT, Resource Load) -> `ReportGenerator`.

## Flow
Run `make benchmark` -> Spin up test clients -> Execute 300+ scenarios -> Output `engineering_report.md`.

## Extension Points
Add new procedural rules in `ScenarioFactory` or integrate new OpenTelemetry validators.
