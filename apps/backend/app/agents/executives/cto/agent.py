import logging
from typing import Dict, Any, List
import time

from app.agents.base.base_agent import BaseExecutiveAgent
from app.agents.base.profile import AgentProfile
from app.agents.base.capabilities import Capability
from app.agents.base.task import ExecutiveTask
from app.agents.base.output import ExecutiveResult
from app.services.llm.llm_service import LLMService

from app.agents.executives.cto.planner import CTOPlanner
from app.agents.executives.cto.architect import ArchitectureReviewer
from app.agents.executives.cto.reviewer import TechnicalReviewer

logger = logging.getLogger(__name__)

class CTOAgent(BaseExecutiveAgent):
    """
    The Chief Technology Officer (CTO) Executive Agent.
    Specializes in software architecture, code quality, tech debt, and system design.
    """
    
    def __init__(self, llm_service: LLMService, capability_executor=None, knowledge_agent_graph=None):
        super().__init__(llm_service, capability_executor)
        self.planner = CTOPlanner(llm_service)
        self.architect = ArchitectureReviewer(llm_service)
        self.reviewer = TechnicalReviewer(llm_service)
        
        # Temporary for backward compatibility during migration
        self.knowledge_agent = knowledge_agent_graph
        
        self._profile = AgentProfile(
            agent_name="CTO Agent",
            title="Chief Technology Officer",
            domain="Engineering & Architecture",
            description="Evaluates system architecture, codebase quality, technical debt, and provides technical planning.",
            capabilities=[
                Capability.CODE_REVIEW,
                Capability.ARCHITECTURE_ANALYSIS,
                Capability.TECHNICAL_PLANNING,
                Capability.SYSTEM_DESIGN
            ],
            supported_task_types=[
                "Architecture Review",
                "Codebase Analysis",
                "Technical Debt Analysis",
                "Migration Planning",
                "Technology Recommendation"
            ],
            required_tools=[],
            supported_sources=["GitHub", "Architecture Docs", "Technical Memory"]
        )

    def get_profile(self) -> AgentProfile:
        return self._profile

    def execute(self, task: ExecutiveTask, state: Dict[str, Any]) -> ExecutiveResult:
        start_time = time.time()
        logger.info(f"[CTO Agent] Executing task: {task.goal}")
        
        # 1. Plan Execution Strategy
        plan = self.planner.plan(task)
        
        # 2. Retrieve Enterprise Knowledge based on plan
        gathered_context = []
        sources = []
        
        # Execute capabilities
        for action in plan.required_github_actions:
            result = self.invoke_capability(
                capability_id="github_tool",
                action=action,
                repository_name="default"  # Placeholder, should be extracted from context
            )
            gathered_context.append(f"GitHub {action} Result: {result.data if result.success else result.errors}")
            
        for query in plan.queries:
            # Fallback to direct Knowledge Agent invocation if capabilities aren't enough yet
            if self.knowledge_agent:
                sub_state = {
                    "question": query,
                    "session_id": state.get("session_id"),
                    "conversation_id": state.get("conversation_id"),
                    "execution_trace": [],
                    "metrics": {},
                    "tool_results": [],
                    "sources": [],
                    "reranked_chunks": [],
                    "semantic_memory": [],
                    "recent_memory": [],
                }
                res = self.knowledge_agent.run(sub_state)
                gathered_context.append(f"Query: {query}\nResult: {res.get('answer', '')}")
                for source in res.get("sources", []):
                    if source not in sources:
                        sources.append(source)
            else:
                gathered_context.append(f"Query: {query}\nResult: Retrieval unavailable.")
                    
        full_context = "\n\n".join(gathered_context)
        
        # 3. Analyze based on capabilities required
        recommendations = []
        findings_summary = []
        
        if Capability.ARCHITECTURE_ANALYSIS in task.required_capabilities or "architecture" in task.goal.lower():
            arch_findings = self.architect.review(task.goal, full_context)
            findings_summary.append(
                f"Architecture Score - Scalability: {arch_findings.scalability_score}/10, "
                f"Modularity: {arch_findings.modularity_score}/10."
            )
            findings_summary.extend(arch_findings.findings)
            recommendations.extend(arch_findings.recommendations)
            
        if Capability.CODE_REVIEW in task.required_capabilities or "code" in task.goal.lower() or "debt" in task.goal.lower():
            review_findings = self.reviewer.review(task.goal, full_context)
            findings_summary.append("Technical Review Findings:")
            findings_summary.extend(review_findings.tech_debt_issues)
            findings_summary.extend(review_findings.documentation_gaps)
            recommendations.extend(review_findings.recommendations)
            
        # Fallback if no specific capability triggered a sub-agent
        if not findings_summary:
            findings_summary.append("General technical review based on gathered context.")
            # We could use self.reason() here to generate unstructured summary
            
        # Compile reasoning
        reasoning = "CTO Agent Analysis:\n" + "\n".join(findings_summary)
        summary = f"CTO Agent completed analysis for '{task.goal}' with {len(recommendations)} recommendations."
        
        metrics = {
            "execution_time_ms": (time.time() - start_time) * 1000,
            "queries_executed": len(plan.queries)
        }
        
        return self._create_result(
            task=task,
            summary=summary,
            reasoning=reasoning,
            recommendations=recommendations,
            sources=sources,
            metrics=metrics
        )
