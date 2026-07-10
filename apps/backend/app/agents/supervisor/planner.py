import json
import logging
from app.services.llm.gateway import LLMGateway
from app.agents.supervisor.schemas import ExecutionPlan, Task, TaskStatus, ApprovalGate
from app.workflows.templates.template_registry import TemplateRegistry
from app.services.decisions.models import DecisionType
from pydantic import BaseModel
from typing import List

logger = logging.getLogger(__name__)


class LLMTask(BaseModel):
    goal: str
    description: str
    priority: int
    assigned_agent: str
    required_capabilities: List[str]
    dependencies: List[str]


class LLMExecutionPlan(BaseModel):
    goal: str
    tasks: List[LLMTask]


class LLMStrategicPlan(BaseModel):
    autonomy_level: int
    requires_approval: bool
    approval_reason: str
    milestones: List[str]


class Planner:
    """
    Evaluates the user objective, understands intent, determines complexity,
    and generates a structured execution plan across two internal stages:
    Strategic Planning and Task Planning.
    """

    def __init__(
        self,
        llm_service: LLMGateway,
        capability_service=None,
        decision_engine=None,
        agent_registry=None,
    ):
        self.llm_service = llm_service
        self.capability_service = capability_service
        from app.services.decisions.engine import DecisionEngine

        self.decision_engine = decision_engine or DecisionEngine()
        self.agent_registry = agent_registry

    def _strategic_planning_phase(self, goal: str, context: str) -> LLMStrategicPlan:
        """Determines the overarching strategy, autonomy level, and approvals needed."""
        prompt = (
            "You are the Enterprise Supervisor (CEO) Agent in the Strategic Planning Phase.\n"
            "Analyze the following goal and context. Determine the required autonomy level (0-4),\n"
            "whether human approval is needed before execution (for high risk or side effects),\n"
            "and list 2-4 major milestones.\n"
            "Autonomy Levels: 0=Assistant, 1=Suggest, 2=Auto Execute, 3=Auto Recover, 4=Continuous Optimization.\n"
            "You MUST output ONLY a single raw JSON object (no markdown, no code blocks, no explanation) exactly matching this schema:\n"
            "{\n"
            '  "autonomy_level": 2,\n'
            '  "requires_approval": false,\n'
            '  "approval_reason": "",\n'
            '  "milestones": ["milestone 1", "milestone 2"]\n'
            "}\n\n"
            f"User Goal: {goal}\n"
        )
        if context:
            prompt += f"Context:\n{context}\n"

        try:
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self.llm_service.generate_structured, prompt, LLMStrategicPlan
                )
                json_response = future.result(timeout=60)
            cleaned = self._clean_json(json_response)
            data = json.loads(cleaned)
            return LLMStrategicPlan(**data)
        except Exception as e:
            logger.error(f"Strategic planning failed: {e}")
            return LLMStrategicPlan(
                autonomy_level=2,
                requires_approval=False,
                approval_reason="",
                milestones=[],
            )

    def _task_planning_phase(
        self, goal: str, context: str, strategy: LLMStrategicPlan
    ) -> LLMExecutionPlan:
        """Breaks down the goal into granular tasks based on the strategic plan."""
        agent_list = "- 'CTO Agent': Handles engineering and code\n- 'Knowledge Agent': Handles documents"
        if self.agent_registry:
            agents = self.agent_registry.list_agents()
            if agents:
                agent_list = "\n".join(
                    [f"- '{a.agent_name}': {a.description}" for a in agents]
                )

        prompt = (
            "You are the Enterprise Supervisor (CEO) Agent in the Task Planning Phase.\n"
            "Your task is to generate a structured execution plan consisting of granular tasks.\n"
            "You may delegate tasks to multiple different agents if the goal requires cross-domain expertise.\n"
            f"Available Agents:\n{agent_list}\n\n"
            "Available Capabilities (tools): 'github_tool'.\n"
            f"Milestones to cover: {', '.join(strategy.milestones)}\n\n"
            'CRITICAL: You MUST output ONLY a single raw JSON object at the TOP LEVEL with EXACTLY these two keys: "goal" and "tasks".\n'
            'Do NOT wrap the output in any other key like "execution_plan" or "plan".\n'
            "The JSON must look EXACTLY like this example:\n"
            "{\n"
            '  "goal": "the overall goal string",\n'
            '  "tasks": [\n'
            "    {\n"
            '      "goal": "specific task goal",\n'
            '      "description": "detailed description",\n'
            '      "priority": 1,\n'
            '      "assigned_agent": "agent name",\n'
            '      "required_capabilities": [],\n'
            '      "dependencies": []\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            f"User Goal: {goal}\n"
        )
        if context:
            prompt += f"Context:\n{context}\n"

        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                self.llm_service.generate_structured, prompt, LLMExecutionPlan
            )
            json_response = future.result(timeout=60)
        cleaned = self._clean_json(json_response)
        data = json.loads(cleaned)
        return LLMExecutionPlan(**data)

    def _clean_json(self, response: str) -> str:
        """Clean and extract valid JSON from LLM response, handling nested wrappers."""
        cleaned = response.strip()
        # Strip markdown code fences
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Try to detect if the top-level JSON wraps the real plan in a sub-key.
        # E.g. {"execution_plan": {"goal": ..., "tasks": [...]}} or {"plan": {...}}
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                # If top-level lacks required keys, look one level deeper
                if "goal" not in parsed or "tasks" not in parsed:
                    for v in parsed.values():
                        if isinstance(v, dict) and "goal" in v and "tasks" in v:
                            return json.dumps(v)
                        elif isinstance(v, dict) and "tasks" in v:
                            # Inject a goal if missing
                            v.setdefault("goal", "Extracted plan")
                            return json.dumps(v)
        except Exception:
            pass  # Fall through to returning cleaned as-is

        return cleaned

    def plan(self, goal: str, context: str = "") -> ExecutionPlan:
        """Creates an ExecutionPlan for a given goal using internal stages and templates."""
        from app.operations.tracing.trace_manager import TraceManager
        from app.operations.telemetry.telemetry_context import TelemetryContext

        telemetry_snap = TelemetryContext.get_snapshot()
        trace_id = telemetry_snap.get("trace_id")
        trace_manager = TraceManager()

        span = trace_manager.start_span(
            trace_id=trace_id or "planning_trace",
            operation="planning",
            parent_span_id=telemetry_snap.get("span_id") if trace_id else None,
            goal_length=len(goal),
        )

        try:
            logger.info(f"Planner generating execution plan for goal: {goal}")

            # 1. Check Template Registry
            template_name = TemplateRegistry.find_best_match(goal)

            self.decision_engine.record_decision(
                decision_type=DecisionType.PLANNING,
                component="Planner.TemplateRegistry",
                selected_option=template_name if template_name else "Dynamic",
                context={"template_used": template_name, "historical_success": 0.8},
                trace_id=trace_id,
            )

            if template_name:
                logger.info(f"Using template {template_name} for goal: {goal}")
                template_plan = TemplateRegistry.get_template(template_name, goal=goal)
                if template_plan:
                    span.add_event("workflow_template_selected")

                    # Adapt the template using the dedicated engine
                    from app.workflows.engine.template_engine import (
                        WorkflowTemplateEngine,
                    )

                    engine = WorkflowTemplateEngine(
                        self.llm_service, self.decision_engine
                    )
                    adapted_plan = engine.adapt_template(
                        template_plan, goal, context, trace_id
                    )

                    span.add_event("template_modified")

                    span.attributes["template_used"] = template_name
                    span.attributes["task_count"] = len(adapted_plan.tasks)
                    span.add_event("template_success")
                    trace_manager.end_span(span, "OK")
                    return adapted_plan

            # 2. Strategic Planning Phase
            strategy = self._strategic_planning_phase(goal, context)

            # 3. Task Planning Phase
            task_plan = self._task_planning_phase(goal, context, strategy)

            self.decision_engine.record_decision(
                decision_type=DecisionType.PLANNING,
                component="Planner.Dynamic",
                selected_option="LLM_Generated_Plan",
                context={"complexity": "medium", "historical_success": 0.7},
                trace_id=trace_id,
            )

            # Map to Application Schema
            tasks = []
            for t in task_plan.tasks:
                tasks.append(
                    Task(
                        goal=t.goal,
                        description=t.description,
                        priority=t.priority,
                        assigned_agent=t.assigned_agent,
                        required_capabilities=t.required_capabilities,
                        dependencies=t.dependencies,
                        status=TaskStatus.PENDING,
                    )
                )

            # Augment tasks with inferred capabilities if the service is available
            if self.capability_service:
                for task in tasks:
                    decision = self.capability_service.infer(
                        goal=task.goal, description=task.description
                    )
                    task.required_capability = decision.required_capability
                    task.confidence = decision.confidence
                    task.reasoning = decision.reasoning

            approval_gates = []
            if strategy.requires_approval:
                approval_gates.append(
                    ApprovalGate(
                        description=strategy.approval_reason,
                        condition="Before execution",
                    )
                )

            result_plan = ExecutionPlan(
                goal=task_plan.goal,
                tasks=tasks,
                autonomy_level=strategy.autonomy_level,
                milestones=strategy.milestones,
                approval_gates=approval_gates,
            )

            span.attributes["task_count"] = len(tasks)
            trace_manager.end_span(span, "OK")
            return result_plan

        except Exception as e:
            logger.error(f"Planner failed to generate execution plan: {e}")
            fallback_tasks = [
                Task(
                    goal=goal,
                    description="Automatically generated fallback task",
                    status=TaskStatus.PENDING,
                    assigned_agent="Knowledge Agent",
                )
            ]
            if self.capability_service:
                for task in fallback_tasks:
                    decision = self.capability_service.infer(
                        goal=task.goal, description=task.description
                    )
                    task.required_capability = decision.required_capability

            span.attributes["fallback"] = True
            trace_manager.end_span(span, "ERROR")
            return ExecutionPlan(
                goal=goal,
                tasks=fallback_tasks,
            )
