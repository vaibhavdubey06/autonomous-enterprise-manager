import os
import sys
import yaml
import time
import numpy as np

os.environ["USE_SQLITE"] = "true"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend")))

from evaluation.scenarios import EndToEndScenarios, BenchmarkMode
from evaluation.regression import RegressionEngine
from evaluation.reports.generator import ReportGenerator
from app.operations.tracing.exporter import InMemoryTraceExporter
from app.operations.tracing.trace_manager import TraceManager
from evaluation.metrics.aggregator import MetricsAggregator

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "benchmark.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f).get("benchmark", {})
    return {"mode": "LOCAL", "iterations": 1}

def main():
    print("Starting Enterprise AI Evaluation Framework (Production Grade)...")
    config = load_config()
    
    mode = config.get("mode", BenchmarkMode.LOCAL)
    iterations = config.get("iterations", 1)
    
    # 1. Setup Exporter
    exporter = InMemoryTraceExporter()
    TraceManager.register_exporter(exporter)
    
    all_results = []
    
    # 2. Iterations
    print(f"Running {iterations} iterations in {mode} mode...")
    for i in range(iterations):
        print(f"--- Iteration {i+1}/{iterations} ---")
        exporter.clear()
        
        # Real graph execution
        scenarios = EndToEndScenarios(mode=mode).run_all()
        
        metrics = MetricsAggregator(scenarios).evaluate()
        all_results.append(metrics)
        
    # 3. Compute Statistical Variance across iterations
    final_metrics = MetricsAggregator.compute_variance(all_results)
    
    # 4. Regressions & Output
    history_dir = os.path.join(os.path.dirname(__file__), "reports", "history")
    final_metrics["regression_analysis"] = RegressionEngine(history_dir).detect_regressions(final_metrics)
    
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    json_path, md_path = ReportGenerator(reports_dir).generate(final_metrics)
    
    print(f"Evaluation complete. Reports generated:\n- {json_path}\n- {md_path}")

if __name__ == "__main__":
    main()
