import logging
import json
from pathlib import Path
from typing import Dict, Optional, List
import copy
from app.agents.supervisor.schemas import ExecutionPlan, Task, AutonomyLevel

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """
    Registry for discoverable and extensible workflow templates.
    Instead of static files, templates are registered dynamically.
    """
    
    _templates: Dict[str, ExecutionPlan] = {}

    @classmethod
    def register(cls, name: str, plan: ExecutionPlan):
        cls._templates[name] = plan
        logger.info(f"Registered workflow template: {name}")

    @classmethod
    def get_template(cls, name: str, goal: str = "") -> Optional[ExecutionPlan]:
        template = cls._templates.get(name)
        if template:
            # Return a deep copy so instances don't mutate the registry
            inst = copy.deepcopy(template)
            if goal:
                inst.goal = goal
            return inst
        return None

    @classmethod
    def list_templates(cls) -> List[str]:
        return list(cls._templates.keys())

    @classmethod
    def find_best_match(cls, goal: str) -> Optional[str]:
        """
        Simple heuristic matching for finding a template based on goal.
        Future extension: Semantic matching.
        """
        goal_lower = goal.lower()
        if "design" in goal_lower or "architecture" in goal_lower:
            return "Software Design"
        if "incident" in goal_lower or "outage" in goal_lower:
            return "Incident Response"
        if "security" in goal_lower or "audit" in goal_lower:
            return "Security Audit"
        if "research" in goal_lower:
            return "Research"
        if "deploy" in goal_lower:
            return "Deployment"
        return None


    @classmethod
    def load_packs(cls):
        """Loads JSON workflow packs from app/workflows/packs/."""
        packs_dir = Path(__file__).parent.parent / "packs"
        if not packs_dir.exists():
            logger.warning(f"Workflow packs directory not found at {packs_dir}")
            return
            
        for file_path in packs_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # We dynamically map JSON dict -> ExecutionPlan
                plan = ExecutionPlan(**data)
                plan.workflow_template = plan.goal # Set template name to goal
                
                # Register using the JSON file name or the goal name
                cls.register(plan.goal, plan)
            except Exception as e:
                logger.error(f"Failed to load workflow pack {file_path}: {e}")

# Automatically load packs when module is imported
TemplateRegistry.load_packs()
