import logging
from typing import List
from app.collaboration.coordinator.collaboration_manager import CollaborationManager
from app.collaboration.schemas.executive import ExecutiveDecision, DecisionStrategy
from app.agents.supervisor.schemas import ExecutionPlan
from app.operations.tracing.trace_manager import TraceManager

logger = logging.getLogger(__name__)


class ExecutiveCouncil:
    """
    A specialized orchestrator built on top of CollaborationManager.
    Handles strategic discussions, conflict resolution, consensus generation,
    and produces a structured ExecutiveDecision for the CEO.
    """

    def __init__(self, collaboration_manager: CollaborationManager):
        self.manager = collaboration_manager
        self.trace_manager = TraceManager()

    def orchestrate_council(
        self,
        objective: str,
        plan: ExecutionPlan,
        strategy: DecisionStrategy,
        participating_agents: List[str],
    ) -> ExecutiveDecision:
        """
        Coordinates the executive board meeting for a strategic objective.
        """
        logger.info(f"Starting Executive Council for objective: {objective[:50]}...")

        # 1. Start Session
        session = self.manager.create_session(objective=objective)
        session_id = session.session_id

        # 2. Form Team
        self.manager.form_team(session_id)

        # In a real environment, we would invoke the agent discussion loop here.
        # For now, we simulate the output from the formed team to build the ExecutiveDecision.
        recommendations = []
        conflicts = []
        votes = {}
        risks = {"Technical": [], "Financial": [], "Operational": []}

        with self.trace_manager.span(
            "workflow_trace",
            "ExecutiveCouncil_Discussion",
            execution_strategy=strategy.value,
        ):
            for agent in participating_agents:
                with self.trace_manager.span(
                    "workflow_trace", f"Council_{agent}", agent_name=agent
                ):
                    recommendations.append(
                        f"{agent} recommends proceeding with caution."
                    )
                    votes[agent] = "APPROVE"
                    if agent == "CFO":
                        risks["Financial"].append("High initial capital expenditure.")
                    elif agent == "CISO":
                        risks["Technical"].append(
                            "Compliance with data sovereignty laws required."
                        )

            # Simulate a conflict if both CTO and CFO are present
            if "CTO" in participating_agents and "CFO" in participating_agents:
                conflicts.append(
                    "CTO prioritizes cloud migration speed; CFO prioritizes phased approach for cost control."
                )

        # We would use the manager.conflict and manager.consensus components here.
        # For now, return the structured output.
        decision = ExecutiveDecision(
            objective=objective,
            decision_strategy=strategy,
            recommendations=recommendations,
            conflicts_detected=conflicts,
            votes=votes,
            risks=risks,
            confidence_score=0.85,
            follow_up_actions=[
                "Schedule technical review",
                "Prepare budget allocation",
            ],
            participating_executives=participating_agents,
            final_decision="Proceed with phased execution."
            if strategy == DecisionStrategy.CEO_OVERRIDE
            else "Approved by majority.",
        )

        # 3. Complete Session
        import asyncio

        try:
            asyncio.get_running_loop()
            asyncio.create_task(self.manager.complete_session(session_id))
        except RuntimeError:
            asyncio.run(self.manager.complete_session(session_id))

        return decision
