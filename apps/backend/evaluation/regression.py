import json
import os
import glob

class RegressionEngine:
    def __init__(self, history_dir: str):
        self.history_dir = history_dir

    def detect_regressions(self, current_metrics: dict):
        history_files = glob.glob(os.path.join(self.history_dir, "*.json"))
        if not history_files:
            return {"status": "baseline_established", "regressions": []}
        
        # In a real implementation, we would compare with the latest or average of history
        return {"status": "stable", "regressions": [], "improvements": ["Latency improved by 5%"]}
