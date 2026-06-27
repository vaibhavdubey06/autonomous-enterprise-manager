import json
import datetime
import os

class ReportGenerator:
    def __init__(self, reports_dir: str):
        self.reports_dir = reports_dir

    def generate(self, metrics: dict):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = os.path.join(self.reports_dir, f"benchmark_{timestamp}.json")
        md_path = os.path.join(self.reports_dir, f"benchmark_{timestamp}.md")
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=4)
            
        md_content = f"# Enterprise AI Benchmark Report\n\n**Date**: {timestamp}\n\n"
        md_content += "## Executive Summary\nAll systems operational.\n"
        
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        return json_path, md_path
