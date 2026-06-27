import os
import sys

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluation.performance.latency import LatencyEvaluator
from evaluation.performance.resources import ResourceEvaluator
from evaluation.intelligence.rag import RAGEvaluator
from evaluation.intelligence.memory import MemoryEvaluator
from evaluation.scenarios import EndToEndScenarios
from evaluation.regression import RegressionEngine
from evaluation.reports.generator import ReportGenerator

def main():
    print("Starting Enterprise AI Evaluation Framework...")
    
    # 1. Run Scenarios
    scenarios = EndToEndScenarios().run_all()
    
    # 2. Collect Performance
    resources = ResourceEvaluator().get_current_usage()
    latency_breakdown = LatencyEvaluator().measure_e2e("dummy")
    
    # 3. Collect Intelligence Quality
    rag_metrics = RAGEvaluator().evaluate(dataset=[])
    memory_metrics = MemoryEvaluator().evaluate(dataset=[])
    
    # 4. Aggregate Metrics
    metrics = {
        "scenarios": scenarios,
        "resources": resources,
        "latency_breakdown": latency_breakdown,
        "rag_quality": rag_metrics,
        "memory_quality": memory_metrics
    }
    
    # 4. Check Regressions
    history_dir = os.path.join(os.path.dirname(__file__), "reports", "history")
    regression_results = RegressionEngine(history_dir).detect_regressions(metrics)
    metrics["regression_analysis"] = regression_results
    
    # 5. Generate Reports
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    json_path, md_path = ReportGenerator(reports_dir).generate(metrics)
    
    print(f"Evaluation complete. Reports generated:\n- {json_path}\n- {md_path}")

if __name__ == "__main__":
    main()
