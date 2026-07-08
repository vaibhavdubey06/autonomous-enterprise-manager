import numpy as np
from typing import Dict, Any, List
from app.operations.tracing.trace_manager import TraceManager

class TelemetryEvaluator:
    def __init__(self):
        self.trace_manager = TraceManager()
        
    def _calculate_percentiles(self, name: str, data: List[float]) -> Dict[str, float]:
        if not data:
            return {"p50": 0.0, "p90": 0.0, "p99": 0.0, "avg": 0.0, "min": 0.0, "max": 0.0, "count": 0}
        
        return {
            "p50": float(np.percentile(data, 50)),
            "p90": float(np.percentile(data, 90)),
            "p99": float(np.percentile(data, 99)),
            "avg": float(np.mean(data)),
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "count": len(data)
        }

    def evaluate(self) -> Dict[str, Any]:
        all_traces = self.trace_manager.get_all_traces()
        
        latency_data = {
            "llm_generation": [],
            "build_context": [],
            "compile_prompt": [],
            "e2e": [] # we could get this from root spans
        }
        
        llm_metrics = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "fallback_count": 0,
            "providers_used": {},
            "routing_policies": {}
        }
        
        guardrail_metrics = {
            "blocked": 0,
            "errors": 0
        }
        
        knowledge_metrics = {
            "documents_retrieved": 0,
            "chunks_retrieved": 0,
            "vector_search_hits": 0
        }
        
        execution_metrics = {
            "total_spans": 0,
            "parallel_tasks": 0,
            "workflow_failures": 0,
            "total_replans": 0,
            "successful_recoveries": 0,
            "templates_used": 0,
            "human_interventions": 0
        }
        
        mcp_metrics = {
            "mcp_client_requests": 0,
            "mcp_tool_executions": 0,
            "mcp_resource_reads": 0,
            "mcp_prompt_requests": 0,
            "mcp_failures": 0,
            "mcp_total_cost": 0.0,
            "mcp_total_tokens": 0
        }
        
        a2a_metrics = {
            "a2a_discovery_requests": 0,
            "a2a_delegation_requests": 0,
            "a2a_negotiation_requests": 0,
            "a2a_server_executions": 0,
            "a2a_failures": 0,
            "total_latency_ms": 0.0,
            "request_count": 0
        }
        
        workflow_metrics = {
            "template_matches": 0,
            "template_adaptations": 0,
            "template_successes": 0
        }
        
        connector_metrics = {
            "connector_selected": 0,
            "connector_execution": 0,
            "connector_failure": 0,
            "total_latency_ms": 0.0,
            "total_cost": 0.0
        }
        
        runtime_metrics = {
            "sessions_created": 0,
            "sessions_completed": 0,
            "sessions_failed": 0,
            "total_duration_ms": 0.0,
            "checkpoints": 0,
            "replays": 0
        }
        
        decision_metrics = {
            "total_decisions": 0,
            "policy_violations": 0,
            "avg_confidence": 0.0,
            "avg_risk": 0.0,
            "types": {}
        }
        confidence_sum = 0.0
        risk_sum = 0.0

        for trace_id, spans in all_traces.items():
            execution_metrics["total_spans"] += len(spans)
            
            trace_start = min(s.get("start_time", 0) for s in spans if s.get("start_time")) if spans else 0
            trace_end = max(s.get("end_time", 0) for s in spans if s.get("end_time")) if spans else 0
            if trace_end > trace_start:
                latency_data["e2e"].append((trace_end - trace_start) * 1000)
                
            for span in spans:
                op = span.get("operation", "")
                attrs = span.get("attributes", {})
                duration = span.get("duration_ms", 0)
                status = span.get("status", "OK")
                
                if op == "planning":
                    events = [e.get("name") for e in span.get("events", [])]
                    if "workflow_template_selected" in events:
                        workflow_metrics["template_matches"] += 1
                    if "template_modified" in events:
                        workflow_metrics["template_adaptations"] += 1
                    if "template_success" in events:
                        workflow_metrics["template_successes"] += 1
                
                if op == "decision_recorded":
                    decision_metrics["total_decisions"] += 1
                    conf = attrs.get("confidence", 0.0)
                    risk = attrs.get("risk", 0.0)
                    confidence_sum += conf
                    risk_sum += risk
                    dt = attrs.get("decision_type", "unknown")
                    decision_metrics["types"][dt] = decision_metrics["types"].get(dt, 0) + 1
                    if not attrs.get("policy_compliant", True):
                        decision_metrics["policy_violations"] += 1
                
                if status == "ERROR":
                    if "guardrail" in op.lower() or "blocked" in attrs.get("error", "").lower():
                        guardrail_metrics["blocked"] += 1
                    else:
                        guardrail_metrics["errors"] += 1
                        if "workflow" in op.lower():
                            execution_metrics["workflow_failures"] += 1
                            
                if "parallel" in op.lower() or attrs.get("is_parallel"):
                    execution_metrics["parallel_tasks"] += 1
                    
                if "replan" in op.lower() or attrs.get("replan"):
                    execution_metrics["total_replans"] += 1
                    
                if "recovery" in op.lower() and status == "OK":
                    execution_metrics["successful_recoveries"] += 1
                    
                if attrs.get("template_used"):
                    execution_metrics["templates_used"] += 1
                    
                if attrs.get("requires_approval") or "approval" in op.lower():
                    execution_metrics["human_interventions"] += 1
                    
                if "search" in op.lower() or "rag" in op.lower() or "retrieve" in op.lower():
                    knowledge_metrics["documents_retrieved"] += attrs.get("docs_retrieved", attrs.get("chunks_retrieved", 0))
                    knowledge_metrics["vector_search_hits"] += 1
                
                if op in latency_data:
                    latency_data[op].append(duration)
                elif "search" in op.lower():
                    if "vector_search" not in latency_data: latency_data["vector_search"] = []
                    latency_data["vector_search"].append(duration)
                
                if op == "llm_generation":
                    cost = attrs.get("estimated_cost", 0.0)
                    llm_metrics["total_cost"] += cost
                    llm_metrics["total_tokens"] += attrs.get("tokens_max", 0)
                    
                    provider = attrs.get("provider", "unknown")
                    llm_metrics["providers_used"][provider] = llm_metrics["providers_used"].get(provider, 0) + 1
                    
                    policy = attrs.get("routing_policy", "unknown")
                    llm_metrics["routing_policies"][policy] = llm_metrics["routing_policies"].get(policy, 0) + 1
                    
                    llm_metrics["fallback_count"] += attrs.get("fallback_count", 0)
                    
                if "mcp_" in op:
                    if op == "mcp_client_request":
                        mcp_metrics["mcp_client_requests"] += 1
                    elif op == "mcp_tool_execution":
                        mcp_metrics["mcp_tool_executions"] += 1
                        mcp_metrics["mcp_total_cost"] += attrs.get("cost", 0.0)
                        mcp_metrics["mcp_total_tokens"] += attrs.get("tokens", 0)
                    elif op == "mcp_resource_read":
                        mcp_metrics["mcp_resource_reads"] += 1
                    elif op == "mcp_prompt_request":
                        mcp_metrics["mcp_prompt_requests"] += 1
                        
                    if status == "ERROR":
                        mcp_metrics["mcp_failures"] += 1
                        
                    if op not in latency_data:
                        latency_data[op] = []
                    latency_data[op].append(duration)
                    
                if "a2a_" in op:
                    if op == "a2a_discovery_request":
                        a2a_metrics["a2a_discovery_requests"] += 1
                    elif op == "a2a_delegation_request":
                        a2a_metrics["a2a_delegation_requests"] += 1
                    elif op == "a2a_negotiation_request":
                        a2a_metrics["a2a_negotiation_requests"] += 1
                    elif op == "a2a_server_execute":
                        a2a_metrics["a2a_server_executions"] += 1
                        
                    if status == "ERROR" or "error" in attrs:
                        a2a_metrics["a2a_failures"] += 1
                        
                    latency = attrs.get("latency_ms", duration)
                    if latency > 0:
                        a2a_metrics["total_latency_ms"] += latency
                        a2a_metrics["request_count"] += 1
                        if op not in latency_data:
                            latency_data[op] = []
                        latency_data[op].append(latency)
                        
                if "connector_" in op:
                    if op == "connector_selected":
                        connector_metrics["connector_selected"] += 1
                    elif op == "connector_execution":
                        connector_metrics["connector_execution"] += 1
                        connector_metrics["total_cost"] += attrs.get("cost", 0.0)
                        
                    if status == "ERROR" or op == "connector_failure":
                        connector_metrics["connector_failure"] += 1
                        
                    latency = attrs.get("latency_ms", duration)
                    if latency > 0:
                        connector_metrics["total_latency_ms"] += latency
                        if op not in latency_data:
                            latency_data[op] = []
                        latency_data[op].append(latency)
                        
                if "runtime_" in op:
                    if op == "runtime_created":
                        runtime_metrics["sessions_created"] += 1
                    elif op == "runtime_completed":
                        runtime_metrics["sessions_completed"] += 1
                    elif op == "runtime_failed":
                        runtime_metrics["sessions_failed"] += 1
                    elif op == "runtime_duration":
                        runtime_metrics["total_duration_ms"] += duration
                    elif op == "runtime_checkpoint":
                        runtime_metrics["checkpoints"] += 1
                    elif op == "runtime_replayed":
                        runtime_metrics["replays"] += 1

        if decision_metrics["total_decisions"] > 0:
            decision_metrics["avg_confidence"] = confidence_sum / decision_metrics["total_decisions"]
            decision_metrics["avg_risk"] = risk_sum / decision_metrics["total_decisions"]

        # Aggregate
        metrics = {
            "performance": {},
            "llm_metrics": llm_metrics,
            "guardrail_metrics": guardrail_metrics,
            "knowledge_metrics": knowledge_metrics,
            "execution_metrics": execution_metrics,
            "decision_metrics": decision_metrics,
            "mcp_metrics": mcp_metrics,
            "a2a_metrics": a2a_metrics,
            "workflow_metrics": workflow_metrics,
            "connector_metrics": connector_metrics,
            "runtime_metrics": runtime_metrics
        }
        
        for op, data in latency_data.items():
            metrics["performance"][op] = self._calculate_percentiles(op, data)
            
        return metrics
