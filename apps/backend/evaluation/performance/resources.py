import psutil


class ResourceEvaluator:
    def get_current_usage(self):
        return {
            "cpu_percent": psutil.cpu_percent(),
            "ram_mb": psutil.virtual_memory().used / (1024 * 1024),
        }
