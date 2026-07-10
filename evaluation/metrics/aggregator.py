import numpy as np
from typing import Dict, Any, List
from evaluation.models import EvaluationResult, ExecutionStatus
from evaluation.intelligence.quality import QualityEvaluator
from evaluation.intelligence.rag import RAGEvaluator
from evaluation.intelligence.supervisor import SupervisorEvaluator
from evaluation.intelligence.capability import CapabilityEvaluator
from evaluation.intelligence.memory import MemoryEvaluator
from evaluation.infrastructure.evaluator import InfrastructureEvaluator
from evaluation.metrics.normalizer import ScoreNormalizer
from evaluation.intelligence.decision import DecisionEvaluator
from evaluation.intelligence.mcp import MCPEvaluator
from evaluation.intelligence.a2a import A2AEvaluator
from evaluation.intelligence.workflow import WorkflowEvaluator
from evaluation.intelligence.connectors import ConnectorEvaluator
from evaluation.intelligence.runtime import RuntimeEvaluator
from evaluation.intelligence.cache import CacheEvaluator


class MetricsAggregator:
    def __init__(self, scenarios: Dict[str, EvaluationResult]):
        self.scenarios = scenarios

    def evaluate(self) -> Dict[str, Any]:
        metrics = {
            "pipeline": {},
            "routing": {
                "expected": 0,
                "detected": 0,
                "fallbacks": 0,
                "capability_accuracy": 0.0,
                "agent_accuracy": 0.0,
            },
            "guardrails": {"blocked": 0, "errors": 0, "bypassed": 0},
            "knowledge": {
                "docs_retrieved": 0,
                "chunks": 0,
                "precision": 0.0,
                "recall": 0.0,
                "utilization": 0.0,
            },
            "parallel": {"parallel_spans": 0},
            "provider": {"total_cost": 0.0, "total_tokens": 0},
            "quality": {"success": 0, "failed": 0, "completion_rate": 0.0},
            "planning": {},
            "memory": {},
            "mcp": {
                "client_requests": 0,
                "tool_executions": 0,
                "resource_reads": 0,
                "prompt_requests": 0,
                "failures": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
            },
        }

        latency_data = {}

        quality_eval = QualityEvaluator()
        rag_eval = RAGEvaluator()
        sup_eval = SupervisorEvaluator()
        cap_eval = CapabilityEvaluator()
        mem_eval = MemoryEvaluator()
        dec_eval = DecisionEvaluator()
        mcp_eval = MCPEvaluator()
        a2a_eval = A2AEvaluator()
        wf_eval = WorkflowEvaluator()
        conn_eval = ConnectorEvaluator()
        run_eval = RuntimeEvaluator()
        cache_eval = CacheEvaluator()

        metrics["decisions"] = {}

        total_scenarios = len(self.scenarios)

        # 1. Run Infrastructure Evaluator
        metrics["infrastructure"] = InfrastructureEvaluator().evaluate(
            list(self.scenarios.values())
        )

        # Subsystems for Coverage
        subsystems = {
            "supervisor": 0,
            "planner": 0,
            "capability_inference": 0,
            "agent_router": 0,
            "knowledge_search": 0,
            "memory": 0,
            "prompt_compiler": 0,
            "context_builder": 0,
            "guardrails": 0,
            "gateway": 0,
            "provider": 0,
            "reflection": 0,
        }

        # Accumulators for averages
        acc = {
            "groundedness": [],
            "faithfulness": [],
            "citation_accuracy": [],
            "answer_relevance": [],
            "retrieval_precision": [],
            "retrieval_recall": [],
            "context_utilization": [],
            "planner_quality": [],
            "tool_selection_accuracy": [],
            "capability_inference_accuracy": [],
            "agent_selection_accuracy": [],
            "memory_utilization": [],
            "reflection_quality": [],
            "guardrail_tp": 0,
            "guardrail_fp": 0,
            "guardrail_fn": 0,
            "guardrail_tn": 0,
            "decision_accuracy": [],
            "confidence_calibration": [],
            "policy_compliance": [],
            "avg_confidence": [],
            "tool_success_rate": [],
            "mcp_reliability": [],
            "a2a_discovery_accuracy": [],
            "a2a_delegation_success": [],
            "a2a_negotiation_success": [],
            "a2a_reliability": [],
            "template_match_accuracy": [],
            "workflow_completion": [],
            "template_effectiveness": [],
            "autonomy_score": [],
            "connector_availability": [],
            "connector_success_rate": [],
            "connector_sync_freshness": [],
            "connector_failure_recovery": [],
            "connector_latency_avg": [],
            "connector_cost_avg": [],
            "runtime_availability": [],
            "runtime_stability": [],
            "runtime_success_rate": [],
            "runtime_recovery_rate": [],
            "runtime_resume_success": [],
            "runtime_replay_success": [],
            "runtime_checkpoint_success": [],
            "runtime_cancellation_success": [],
            "cache_hit_rate": [],
            "cache_miss_rate": [],
            "tokens_saved": [],
            "cost_saved": [],
            "avg_lookup_latency": [],
            "avg_storage_latency": [],
        }

        # Scenario Quality Metrics
        for q_id, result in self.scenarios.items():
            metrics["routing"]["expected"] += 1
            if result.execution_status == ExecutionStatus.SUCCESS:
                metrics["quality"]["success"] += 1

                # ONLY Run Intelligence Evaluators on SUCCESS
                q_res = quality_eval.evaluate(result)
                r_res = rag_eval.evaluate(result)
                s_res = sup_eval.evaluate(result)
                c_res = cap_eval.evaluate(result)
                m_res = mem_eval.evaluate(result)

                acc["groundedness"].append(q_res["groundedness"])
                acc["faithfulness"].append(q_res["faithfulness"])
                acc["citation_accuracy"].append(q_res["citation_accuracy"])
                acc["answer_relevance"].append(q_res["answer_relevance"])

                acc["retrieval_precision"].append(r_res["retrieval_precision"])
                acc["retrieval_recall"].append(r_res["retrieval_recall"])
                acc["context_utilization"].append(r_res["context_utilization"])

                acc["planner_quality"].append(s_res["planner_quality"])
                acc["tool_selection_accuracy"].append(s_res["tool_selection_accuracy"])

                acc["capability_inference_accuracy"].append(
                    c_res["capability_inference_accuracy"]
                )
                acc["agent_selection_accuracy"].append(
                    c_res["agent_selection_accuracy"]
                )

                acc["memory_utilization"].append(m_res["memory_utilization"])
                acc["reflection_quality"].append(m_res["reflection_quality"])

                d_res = dec_eval.evaluate(result)
                acc["decision_accuracy"].append(d_res["decision_accuracy"])
                acc["confidence_calibration"].append(d_res["confidence_calibration"])
                acc["policy_compliance"].append(d_res["policy_compliance"])
                acc["avg_confidence"].append(d_res["avg_confidence"])

                mcp_res = mcp_eval.evaluate(result)
                acc["tool_success_rate"].append(mcp_res["tool_success_rate"])
                acc["mcp_reliability"].append(mcp_res["mcp_reliability"])

                a2a_res = a2a_eval.evaluate(result)
                acc["a2a_discovery_accuracy"].append(a2a_res["a2a_discovery_accuracy"])
                acc["a2a_delegation_success"].append(a2a_res["a2a_delegation_success"])
                acc["a2a_negotiation_success"].append(
                    a2a_res["a2a_negotiation_success"]
                )
                acc["a2a_reliability"].append(a2a_res["a2a_reliability"])

                wf_res = wf_eval.evaluate(result)
                acc["template_match_accuracy"].append(wf_res["template_match_accuracy"])
                acc["workflow_completion"].append(wf_res["workflow_completion"])
                acc["template_effectiveness"].append(wf_res["template_effectiveness"])
                acc["autonomy_score"].append(wf_res["autonomy_score"])

                conn_res = conn_eval.evaluate(result)
                acc["connector_availability"].append(conn_res["connector_availability"])
                acc["connector_success_rate"].append(conn_res["connector_success_rate"])
                acc["connector_sync_freshness"].append(
                    conn_res["connector_sync_freshness"]
                )
                acc["connector_failure_recovery"].append(
                    conn_res["connector_failure_recovery"]
                )
                acc["connector_latency_avg"].append(conn_res["connector_latency_avg"])
                acc["connector_cost_avg"].append(conn_res["connector_cost_avg"])

                run_res = run_eval.evaluate(result)
                acc["runtime_availability"].append(run_res["runtime_availability"])
                acc["runtime_stability"].append(run_res["runtime_stability"])
                acc["runtime_success_rate"].append(run_res["runtime_success_rate"])
                acc["runtime_recovery_rate"].append(run_res["runtime_recovery_rate"])
                acc["runtime_resume_success"].append(run_res["runtime_resume_success"])
                acc["runtime_replay_success"].append(run_res["runtime_replay_success"])
                acc["runtime_checkpoint_success"].append(
                    run_res["runtime_checkpoint_success"]
                )
                acc["runtime_cancellation_success"].append(
                    run_res["runtime_cancellation_success"]
                )

                cache_res = cache_eval.evaluate(result)
                acc["cache_hit_rate"].append(cache_res["cache_hit_rate"])
                acc["cache_miss_rate"].append(cache_res["cache_miss_rate"])
                acc["tokens_saved"].append(cache_res["tokens_saved"])
                acc["cost_saved"].append(cache_res["cost_saved"])
                acc["avg_lookup_latency"].append(cache_res["avg_lookup_latency"])
                acc["avg_storage_latency"].append(cache_res["avg_storage_latency"])
            else:
                metrics["quality"]["failed"] += 1

            # Guardrails Logic
            blocked = any(
                "guardrail" in s.get("operation", "").lower()
                or "blocked" in s.get("attributes", {}).get("error", "").lower()
                for s in result.traces
            )
            expected_block = len(result.expected_guardrails) > 0
            if blocked and expected_block:
                acc["guardrail_tp"] += 1
            elif blocked and not expected_block:
                acc["guardrail_fp"] += 1
            elif not blocked and expected_block:
                acc["guardrail_fn"] += 1
            else:
                acc["guardrail_tn"] += 1

            for span in result.traces:
                op = span.get("operation", "")
                attrs = span.get("attributes", {})
                duration = span.get("duration_ms", 0)

                # Subsystem coverage mapping
                op_l = op.lower()
                if "supervisor" in op_l:
                    subsystems["supervisor"] += 1
                if "plan" in op_l:
                    subsystems["planner"] += 1
                if "capability" in op_l:
                    subsystems["capability_inference"] += 1
                if "agent_routing" in op_l:
                    subsystems["agent_router"] += 1
                if "search" in op_l or "rag" in op_l:
                    subsystems["knowledge_search"] += 1
                if "memory" in op_l:
                    subsystems["memory"] += 1
                if "compile" in op_l:
                    subsystems["prompt_compiler"] += 1
                if "context" in op_l:
                    subsystems["context_builder"] += 1
                if "guardrail" in op_l:
                    subsystems["guardrails"] += 1
                if "gateway" in op_l:
                    subsystems["gateway"] += 1
                if "llm_generation" in op_l:
                    subsystems["provider"] += 1
                if "reflection" in op_l:
                    subsystems["reflection"] += 1
                if "mcp_" in op_l:
                    subsystems.setdefault("mcp", 0)
                    subsystems["mcp"] += 1

                # MCP
                if "mcp_" in op:
                    if op == "mcp_client_request":
                        metrics["mcp"]["client_requests"] += 1
                    elif op == "mcp_tool_execution":
                        metrics["mcp"]["tool_executions"] += 1
                        metrics["mcp"]["total_cost"] += attrs.get("cost", 0.0)
                        metrics["mcp"]["total_tokens"] += attrs.get("tokens", 0)
                    elif op == "mcp_resource_read":
                        metrics["mcp"]["resource_reads"] += 1
                    elif op == "mcp_prompt_request":
                        metrics["mcp"]["prompt_requests"] += 1

                    if attrs.get("status") == "ERROR" or "error" in attrs:
                        metrics["mcp"]["failures"] += 1

                # Routing
                if op == "agent_routing":
                    metrics["routing"]["detected"] += 1

                # Provider
                if op == "llm_generation":
                    metrics["provider"]["total_cost"] += attrs.get(
                        "estimated_cost", 0.0
                    )
                    metrics["provider"]["total_tokens"] += attrs.get("total_tokens", 0)
                    metrics["routing"]["fallbacks"] += attrs.get("fallback_count", 0)

                # Knowledge
                if (
                    "search" in op.lower()
                    or "rag" in op.lower()
                    or "retrieval" in op.lower()
                ):
                    metrics["knowledge"]["docs_retrieved"] += attrs.get(
                        "docs_retrieved", 0
                    )
                    metrics["knowledge"]["chunks"] += attrs.get("chunks_retrieved", 0)

                # Guardrails
                if (
                    "guardrail" in op.lower()
                    or "blocked" in attrs.get("error", "").lower()
                ):
                    metrics["guardrails"]["blocked"] += 1

                # Parallel
                if "parallel" in op.lower() or attrs.get("is_parallel"):
                    metrics["parallel"]["parallel_spans"] += 1

                # Latency grouping
                if op not in latency_data:
                    latency_data[op] = []
                latency_data[op].append(duration)

        metrics["coverage"] = {}
        for sub, count in subsystems.items():
            metrics["coverage"][sub] = {
                "executed": min(count, total_scenarios),
                "skipped": total_scenarios - min(count, total_scenarios),
                "failed": metrics["quality"]["failed"],
                "coverage_percent": (min(count, total_scenarios) / total_scenarios)
                if total_scenarios > 0
                else 0.0,
            }

        # Guardrail score normalization
        tp, fp, fn, _tn = (
            acc["guardrail_tp"],
            acc["guardrail_fp"],
            acc["guardrail_fn"],
            acc["guardrail_tn"],
        )
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        eff = (
            ((precision * recall * 2) / (precision + recall))
            if (precision + recall) > 0
            else 1.0
        )
        if tp == 0 and fn == 0 and fp == 0:
            eff = 1.0  # no expected guardrails, no false positive triggers

        metrics["guardrails"]["precision"] = ScoreNormalizer.normalize_single(
            precision, samples=total_scenarios
        ).model_dump()
        metrics["guardrails"]["recall"] = ScoreNormalizer.normalize_single(
            recall, samples=total_scenarios
        ).model_dump()
        metrics["guardrails"]["effectiveness"] = ScoreNormalizer.normalize_single(
            eff, samples=total_scenarios
        ).model_dump()

        if total_scenarios > 0:
            metrics["quality"]["completion_rate"] = round(
                (metrics["quality"]["success"] / total_scenarios) * 100, 2
            )
            metrics["quality"]["groundedness"] = ScoreNormalizer.normalize_list(
                acc["groundedness"]
            ).model_dump()
            metrics["quality"]["faithfulness"] = ScoreNormalizer.normalize_list(
                acc["faithfulness"]
            ).model_dump()
            metrics["quality"]["citation_accuracy"] = ScoreNormalizer.normalize_list(
                acc["citation_accuracy"]
            ).model_dump()
            metrics["quality"]["answer_relevance"] = ScoreNormalizer.normalize_list(
                acc["answer_relevance"]
            ).model_dump()

            metrics["knowledge"]["precision"] = ScoreNormalizer.normalize_list(
                acc["retrieval_precision"]
            ).model_dump()
            metrics["knowledge"]["recall"] = ScoreNormalizer.normalize_list(
                acc["retrieval_recall"]
            ).model_dump()
            metrics["knowledge"]["utilization"] = ScoreNormalizer.normalize_list(
                acc["context_utilization"]
            ).model_dump()

            metrics["planning"]["quality"] = ScoreNormalizer.normalize_list(
                acc["planner_quality"]
            ).model_dump()
            metrics["planning"]["tool_accuracy"] = ScoreNormalizer.normalize_list(
                acc["tool_selection_accuracy"]
            ).model_dump()

            metrics["routing"]["capability_accuracy"] = ScoreNormalizer.normalize_list(
                acc["capability_inference_accuracy"]
            ).model_dump()
            metrics["routing"]["agent_accuracy"] = ScoreNormalizer.normalize_list(
                acc["agent_selection_accuracy"]
            ).model_dump()

            metrics["memory"]["utilization"] = ScoreNormalizer.normalize_list(
                acc["memory_utilization"]
            ).model_dump()
            metrics["memory"]["reflection_quality"] = ScoreNormalizer.normalize_list(
                acc["reflection_quality"]
            ).model_dump()

            metrics["decisions"]["accuracy"] = ScoreNormalizer.normalize_list(
                acc["decision_accuracy"]
            ).model_dump()
            metrics["decisions"]["confidence_calibration"] = (
                ScoreNormalizer.normalize_list(
                    acc["confidence_calibration"]
                ).model_dump()
            )
            metrics["decisions"]["policy_compliance"] = ScoreNormalizer.normalize_list(
                acc["policy_compliance"]
            ).model_dump()
            metrics["decisions"]["avg_confidence"] = ScoreNormalizer.normalize_list(
                acc["avg_confidence"]
            ).model_dump()

            metrics["mcp"]["tool_success_rate"] = ScoreNormalizer.normalize_list(
                acc["tool_success_rate"]
            ).model_dump()
            metrics["mcp"]["reliability"] = ScoreNormalizer.normalize_list(
                acc["mcp_reliability"]
            ).model_dump()

            metrics.setdefault("a2a", {})
            metrics["a2a"]["discovery_accuracy"] = ScoreNormalizer.normalize_list(
                acc["a2a_discovery_accuracy"]
            ).model_dump()
            metrics["a2a"]["delegation_success"] = ScoreNormalizer.normalize_list(
                acc["a2a_delegation_success"]
            ).model_dump()
            metrics["a2a"]["negotiation_success"] = ScoreNormalizer.normalize_list(
                acc["a2a_negotiation_success"]
            ).model_dump()
            metrics["a2a"]["reliability"] = ScoreNormalizer.normalize_list(
                acc["a2a_reliability"]
            ).model_dump()

            metrics.setdefault("workflows", {})
            metrics["workflows"]["template_match_accuracy"] = (
                ScoreNormalizer.normalize_list(
                    acc["template_match_accuracy"]
                ).model_dump()
            )
            metrics["workflows"]["workflow_completion"] = (
                ScoreNormalizer.normalize_list(acc["workflow_completion"]).model_dump()
            )
            metrics["workflows"]["template_effectiveness"] = (
                ScoreNormalizer.normalize_list(
                    acc["template_effectiveness"]
                ).model_dump()
            )
            metrics["workflows"]["autonomy_score"] = ScoreNormalizer.normalize_list(
                acc["autonomy_score"]
            ).model_dump()

            metrics.setdefault("connectors", {})
            metrics["connectors"]["connector_availability"] = (
                ScoreNormalizer.normalize_list(
                    acc["connector_availability"]
                ).model_dump()
            )
            metrics["connectors"]["connector_success_rate"] = (
                ScoreNormalizer.normalize_list(
                    acc["connector_success_rate"]
                ).model_dump()
            )
            metrics["connectors"]["connector_sync_freshness"] = (
                ScoreNormalizer.normalize_list(
                    acc["connector_sync_freshness"]
                ).model_dump()
            )
            metrics["connectors"]["connector_failure_recovery"] = (
                ScoreNormalizer.normalize_list(
                    acc["connector_failure_recovery"]
                ).model_dump()
            )
            metrics["connectors"]["connector_latency_avg"] = {
                "value": float(np.mean(acc["connector_latency_avg"]))
                if acc["connector_latency_avg"]
                else 0.0,
                "state": "VALID",
            }
            metrics["connectors"]["connector_cost_avg"] = {
                "value": float(np.mean(acc["connector_cost_avg"]))
                if acc["connector_cost_avg"]
                else 0.0,
                "state": "VALID",
            }

            metrics.setdefault("runtime", {})
            metrics["runtime"]["runtime_availability"] = ScoreNormalizer.normalize_list(
                acc["runtime_availability"]
            ).model_dump()
            metrics["runtime"]["runtime_stability"] = ScoreNormalizer.normalize_list(
                acc["runtime_stability"]
            ).model_dump()
            metrics["runtime"]["runtime_success_rate"] = ScoreNormalizer.normalize_list(
                acc["runtime_success_rate"]
            ).model_dump()
            metrics["runtime"]["runtime_recovery_rate"] = (
                ScoreNormalizer.normalize_list(
                    acc["runtime_recovery_rate"]
                ).model_dump()
            )
            metrics["runtime"]["runtime_resume_success"] = (
                ScoreNormalizer.normalize_list(
                    acc["runtime_resume_success"]
                ).model_dump()
            )
            metrics["runtime"]["runtime_replay_success"] = (
                ScoreNormalizer.normalize_list(
                    acc["runtime_replay_success"]
                ).model_dump()
            )
            metrics["runtime"]["runtime_checkpoint_success"] = (
                ScoreNormalizer.normalize_list(
                    acc["runtime_checkpoint_success"]
                ).model_dump()
            )
            metrics["runtime"]["runtime_cancellation_success"] = (
                ScoreNormalizer.normalize_list(
                    acc["runtime_cancellation_success"]
                ).model_dump()
            )

            metrics.setdefault("cache", {})
            metrics["cache"]["cache_hit_rate"] = ScoreNormalizer.normalize_list(
                acc["cache_hit_rate"]
            ).model_dump()
            metrics["cache"]["cache_miss_rate"] = ScoreNormalizer.normalize_list(
                acc["cache_miss_rate"]
            ).model_dump()
            metrics["cache"]["tokens_saved"] = {
                "value": float(np.sum(acc["tokens_saved"])),
                "state": "VALID",
            }
            metrics["cache"]["cost_saved"] = {
                "value": float(np.sum(acc["cost_saved"])),
                "state": "VALID",
            }
            metrics["cache"]["avg_lookup_latency"] = {
                "value": float(np.mean(acc["avg_lookup_latency"]))
                if acc["avg_lookup_latency"]
                else 0.0,
                "state": "VALID",
            }
            metrics["cache"]["avg_storage_latency"] = {
                "value": float(np.mean(acc["avg_storage_latency"]))
                if acc["avg_storage_latency"]
                else 0.0,
                "state": "VALID",
            }

        # Calculate latency percentiles for this single iteration
        for op, data in latency_data.items():
            if data:
                metrics["pipeline"][op] = {
                    "p50": float(np.percentile(data, 50)),
                    "p90": float(np.percentile(data, 90)),
                    "p95": float(np.percentile(data, 95)),
                    "p99": float(np.percentile(data, 99)),
                    "avg": float(np.mean(data)),
                    "min": float(np.min(data)),
                    "max": float(np.max(data)),
                    "count": len(data),
                }

        metrics["scenarios_count"] = len(self.scenarios)
        return metrics

    @staticmethod
    def compute_variance(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate multiple iterations into one final statistically sound metric dict."""
        if not results:
            return {}

        final = results[0]  # take structure from first

        costs = [r.get("provider", {}).get("total_cost", 0.0) for r in results]
        final["provider"]["total_cost_avg"] = float(np.mean(costs))
        final["provider"]["total_cost_std"] = float(np.std(costs))

        for op in final.get("pipeline", {}).keys():
            op_p50s = [
                r.get("pipeline", {}).get(op, {}).get("p50", 0)
                for r in results
                if op in r.get("pipeline", {})
            ]
            if op_p50s:
                final["pipeline"][op]["p50_avg"] = float(np.mean(op_p50s))
                final["pipeline"][op]["p50_std"] = float(np.std(op_p50s))

        rates = [r.get("quality", {}).get("completion_rate", 0.0) for r in results]
        final["quality"]["completion_rate_avg"] = float(np.mean(rates))

        def avg_score(metric_path1, metric_path2):
            vals = [
                r.get(metric_path1, {}).get(metric_path2, {}).get("value", 0.0)
                for r in results
                if r.get(metric_path1, {}).get(metric_path2, {}).get("state") == "VALID"
            ]
            if vals:
                return ScoreNormalizer.normalize_list(
                    vals, scale_to_100=False
                ).model_dump()
            return ScoreModel(
                value=0.0, state="NOT_EXECUTED", confidence="NONE"
            ).model_dump()

        # Averages for all new metrics
        final["quality"]["groundedness_avg"] = avg_score("quality", "groundedness")
        final["quality"]["faithfulness_avg"] = avg_score("quality", "faithfulness")
        final["quality"]["answer_relevance_avg"] = avg_score(
            "quality", "answer_relevance"
        )
        final["quality"]["citation_accuracy_avg"] = avg_score(
            "quality", "citation_accuracy"
        )

        final["knowledge"]["precision_avg"] = avg_score("knowledge", "precision")
        final["knowledge"]["recall_avg"] = avg_score("knowledge", "recall")
        final["knowledge"]["utilization_avg"] = avg_score("knowledge", "utilization")

        final["planning"]["quality_avg"] = avg_score("planning", "quality")
        final["planning"]["tool_accuracy_avg"] = avg_score("planning", "tool_accuracy")

        final["routing"]["capability_accuracy_avg"] = avg_score(
            "routing", "capability_accuracy"
        )
        final["routing"]["agent_accuracy_avg"] = avg_score("routing", "agent_accuracy")

        final["memory"]["utilization_avg"] = avg_score("memory", "utilization")
        final["memory"]["reflection_quality_avg"] = avg_score(
            "memory", "reflection_quality"
        )

        final["guardrails"]["effectiveness_avg"] = avg_score(
            "guardrails", "effectiveness"
        )
        final["guardrails"]["precision_avg"] = avg_score("guardrails", "precision")
        final["guardrails"]["recall_avg"] = avg_score("guardrails", "recall")

        final.setdefault("decisions", {})
        final["decisions"]["accuracy_avg"] = avg_score("decisions", "accuracy")
        final["decisions"]["confidence_calibration_avg"] = avg_score(
            "decisions", "confidence_calibration"
        )
        final["decisions"]["policy_compliance_avg"] = avg_score(
            "decisions", "policy_compliance"
        )
        final["decisions"]["avg_confidence_avg"] = avg_score(
            "decisions", "avg_confidence"
        )

        final.setdefault("mcp", {})
        final["mcp"]["client_requests_avg"] = float(
            np.mean([r.get("mcp", {}).get("client_requests", 0) for r in results])
        )
        final["mcp"]["tool_executions_avg"] = float(
            np.mean([r.get("mcp", {}).get("tool_executions", 0) for r in results])
        )
        final["mcp"]["failures_avg"] = float(
            np.mean([r.get("mcp", {}).get("failures", 0) for r in results])
        )
        final["mcp"]["tool_success_rate_avg"] = avg_score("mcp", "tool_success_rate")
        final["mcp"]["reliability_avg"] = avg_score("mcp", "reliability")

        final.setdefault("a2a", {})
        final["a2a"]["discovery_accuracy_avg"] = avg_score("a2a", "discovery_accuracy")
        final["a2a"]["delegation_success_avg"] = avg_score("a2a", "delegation_success")
        final["a2a"]["negotiation_success_avg"] = avg_score(
            "a2a", "negotiation_success"
        )
        final["a2a"]["reliability_avg"] = avg_score("a2a", "reliability")

        final.setdefault("workflows", {})
        final["workflows"]["template_match_accuracy_avg"] = avg_score(
            "workflows", "template_match_accuracy"
        )
        final["workflows"]["workflow_completion_avg"] = avg_score(
            "workflows", "workflow_completion"
        )
        final["workflows"]["template_effectiveness_avg"] = avg_score(
            "workflows", "template_effectiveness"
        )
        final["workflows"]["autonomy_score_avg"] = avg_score(
            "workflows", "autonomy_score"
        )

        final.setdefault("connectors", {})
        final["connectors"]["connector_availability_avg"] = avg_score(
            "connectors", "connector_availability"
        )
        final["connectors"]["connector_success_rate_avg"] = avg_score(
            "connectors", "connector_success_rate"
        )
        final["connectors"]["connector_sync_freshness_avg"] = avg_score(
            "connectors", "connector_sync_freshness"
        )
        final["connectors"]["connector_failure_recovery_avg"] = avg_score(
            "connectors", "connector_failure_recovery"
        )

        l_avgs = [
            r.get("connectors", {}).get("connector_latency_avg", {}).get("value", 0.0)
            for r in results
        ]
        c_avgs = [
            r.get("connectors", {}).get("connector_cost_avg", {}).get("value", 0.0)
            for r in results
        ]

        final["connectors"]["connector_latency_avg_avg"] = {
            "value": float(np.mean(l_avgs)) if l_avgs else 0.0,
            "state": "VALID",
        }
        final["connectors"]["connector_cost_avg_avg"] = {
            "value": float(np.mean(c_avgs)) if c_avgs else 0.0,
            "state": "VALID",
        }

        final.setdefault("runtime", {})
        final["runtime"]["runtime_availability_avg"] = avg_score(
            "runtime", "runtime_availability"
        )
        final["runtime"]["runtime_stability_avg"] = avg_score(
            "runtime", "runtime_stability"
        )
        final["runtime"]["runtime_success_rate_avg"] = avg_score(
            "runtime", "runtime_success_rate"
        )
        final["runtime"]["runtime_recovery_rate_avg"] = avg_score(
            "runtime", "runtime_recovery_rate"
        )
        final["runtime"]["runtime_resume_success_avg"] = avg_score(
            "runtime", "runtime_resume_success"
        )
        final["runtime"]["runtime_replay_success_avg"] = avg_score(
            "runtime", "runtime_replay_success"
        )
        final["runtime"]["runtime_checkpoint_success_avg"] = avg_score(
            "runtime", "runtime_checkpoint_success"
        )
        final["runtime"]["runtime_cancellation_success_avg"] = avg_score(
            "runtime", "runtime_cancellation_success"
        )

        final.setdefault("cache", {})
        final["cache"]["cache_hit_rate_avg"] = avg_score("cache", "cache_hit_rate")
        final["cache"]["cache_miss_rate_avg"] = avg_score("cache", "cache_miss_rate")

        t_sum = [
            r.get("cache", {}).get("tokens_saved", {}).get("value", 0.0)
            for r in results
        ]
        c_sum = [
            r.get("cache", {}).get("cost_saved", {}).get("value", 0.0) for r in results
        ]
        lu_avgs = [
            r.get("cache", {}).get("avg_lookup_latency", {}).get("value", 0.0)
            for r in results
        ]
        st_avgs = [
            r.get("cache", {}).get("avg_storage_latency", {}).get("value", 0.0)
            for r in results
        ]

        final["cache"]["tokens_saved_sum"] = {
            "value": float(np.sum(t_sum)) if t_sum else 0.0,
            "state": "VALID",
        }
        final["cache"]["cost_saved_sum"] = {
            "value": float(np.sum(c_sum)) if c_sum else 0.0,
            "state": "VALID",
        }
        final["cache"]["avg_lookup_latency_avg"] = {
            "value": float(np.mean(lu_avgs)) if lu_avgs else 0.0,
            "state": "VALID",
        }
        final["cache"]["avg_storage_latency_avg"] = {
            "value": float(np.mean(st_avgs)) if st_avgs else 0.0,
            "state": "VALID",
        }

        final["iterations"] = len(results)
        return final
