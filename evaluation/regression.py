import os
import glob
import json
import shutil
import numpy as np


class RegressionEngine:
    def __init__(self, history_dir: str):
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)

    def detect_regressions(self, current_metrics: dict):
        # Load up to last 20 historical runs
        history_files = sorted(
            glob.glob(os.path.join(self.history_dir, "system_report_*.json"))
        )

        history_data = []
        for file in history_files[-20:]:  # Last 20 runs
            try:
                with open(file, "r", encoding="utf-8") as f:
                    history_data.append(json.load(f))
            except Exception:
                continue

        if not history_data:
            baseline_path = os.path.join(self.history_dir, "baseline.json")
            with open(baseline_path, "w", encoding="utf-8") as f:
                json.dump(current_metrics, f, indent=4)
            return {
                "status": "baseline_established",
                "regressions": [],
                "improvements": [],
                "recommendations": ["Gather more historical data for trend analysis."],
                "trends": {},
            }

        latest_history_file = history_files[-1]
        try:
            # also save as explicit baseline.json
            baseline_path = os.path.join(self.history_dir, "baseline.json")
            shutil.copy(latest_history_file, baseline_path)
        except Exception:
            pass

        regressions = []
        improvements = []
        trends = {}

        def get_val(metrics_dict, domain, metric):
            obj = metrics_dict.get(domain, {}).get(metric, {})
            if isinstance(obj, dict):
                return obj.get("value", 0.0)
            return 0.0

        # Compare latency (lower is better)
        curr_perf = current_metrics.get("pipeline", {})
        last_metrics = history_data[-1]
        last_perf = last_metrics.get("pipeline", {})

        for op, data in curr_perf.items():
            if op in last_perf:
                curr_p50 = data.get("p50", 0)
                last_p50 = last_perf[op].get("p50", 0)
                if last_p50 > 0:
                    delta = (curr_p50 - last_p50) / last_p50
                    if delta > 0.10:
                        regressions.append(
                            f"{op} latency degraded by {delta * 100:.1f}% (now {curr_p50:.2f}ms)"
                        )
                    elif delta < -0.10:
                        improvements.append(
                            f"{op} latency improved by {abs(delta) * 100:.1f}% (now {curr_p50:.2f}ms)"
                        )

                # Trend calculation over history
                hist_vals = [
                    m.get("pipeline", {}).get(op, {}).get("p50", 0)
                    for m in history_data
                    if m.get("pipeline", {}).get(op, {}).get("p50", 0) > 0
                ]
                if hist_vals:
                    # For latency, higher is Regressing
                    if len(hist_vals) >= 2:
                        fh = np.mean(hist_vals[: len(hist_vals) // 2])
                        sh = np.mean(hist_vals[len(hist_vals) // 2 :])
                        trends[f"{op}_latency"] = (
                            "Regressing"
                            if sh > fh * 1.05
                            else ("Improving" if sh < fh * 0.95 else "Stable")
                        )

        # Trend analysis for AI Metrics
        ai_metrics = [
            ("quality", "groundedness_avg"),
            ("knowledge", "precision_avg"),
            ("planning", "quality_avg"),
        ]
        for domain, metric in ai_metrics:
            hist_vals = [get_val(m, domain, metric) for m in history_data]
            hist_vals = [v for v in hist_vals if v > 0]
            if len(hist_vals) >= 2:
                fh = np.mean(hist_vals[: len(hist_vals) // 2])
                sh = np.mean(hist_vals[len(hist_vals) // 2 :])
                trends[f"{metric}"] = (
                    "Improving"
                    if sh > fh * 1.05
                    else ("Regressing" if sh < fh * 0.95 else "Stable")
                )

        status = "degraded" if regressions else "stable"

        recommendations = []
        # Dynamic Subsystem Engineering Recommendations
        comp_rate = current_metrics.get("quality", {}).get("completion_rate", 100)
        if comp_rate < 90:
            recommendations.append(
                "Overall success rate is below 90%. Review infrastructure dashboards for quota limits or provider timeouts."
            )

        groundedness = get_val(current_metrics, "quality", "groundedness_avg")
        if groundedness > 0 and groundedness < 70:
            recommendations.append(
                "Groundedness score is low. Improve LLM prompt instructions to strictly rely on retrieved context."
            )

        precision = get_val(current_metrics, "knowledge", "precision_avg")
        if precision > 0 and precision < 50:
            recommendations.append(
                "Retrieval precision is degraded. Consider tuning embedding threshold or adjusting chunk sizes."
            )

        planner_acc = get_val(current_metrics, "planning", "tool_accuracy_avg")
        if planner_acc > 0 and planner_acc < 80:
            recommendations.append(
                "Tool selection accuracy is low. Expand the supervisor prompt descriptions for available tools."
            )

        planner_latency = curr_perf.get("planning", {}).get("avg", 0)
        if planner_latency > 5000:
            exp_improvement = (planner_latency - 3000) / 1000
            recommendations.append(
                f"Planner Average latency is {planner_latency / 1000:.1f} s. Recommend reducing prompt size. Expected Improvement: ~{exp_improvement:.1f} s"
            )

        prov_quota_failures = current_metrics.get("infrastructure", {}).get(
            "quota_failure_rate", 0
        )
        if prov_quota_failures > 0:
            exp_avail = (1 - (prov_quota_failures / 2)) * 100
            recommendations.append(
                f"Provider Quota exceeded ({prov_quota_failures * 100:.1f}%). Recommend increasing fallback pool. Expected Availability: {exp_avail:.1f}%"
            )

        routing_rate = (
            current_metrics.get("routing", {}).get("detected", 0)
            / current_metrics.get("routing", {}).get("expected", 1)
            if current_metrics.get("routing", {}).get("expected", 1) > 0
            else 0
        )
        if routing_rate > 0.8:
            recommendations.append(
                f"LLM Routing Rate is {routing_rate * 100:.1f}%. Recommend increasing deterministic routing threshold. Expected Improvement: Reduce routing latency by 60%."
            )

        result = {
            "status": status,
            "regressions": regressions,
            "improvements": improvements,
            "recommendations": recommendations,
            "trends": trends,
            "best_run": max(history_files) if history_files else None,
            "worst_run": min(history_files) if history_files else None,
        }

        with open(
            os.path.join(self.history_dir, "comparison.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(result, f, indent=4)

        return result
