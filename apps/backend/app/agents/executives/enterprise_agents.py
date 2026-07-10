import logging
import time
from typing import Any, ClassVar, Dict, List

from app.agents.base.base_agent import BaseExecutiveAgent
from app.agents.base.capabilities import Capability
from app.agents.base.output import ExecutiveResult
from app.agents.base.profile import AgentProfile
from app.agents.base.task import ExecutiveTask
from app.services.llm.gateway import LLMGateway

logger = logging.getLogger(__name__)


class DomainExecutiveAgent(BaseExecutiveAgent):
    profile_kwargs: ClassVar[Dict[str, Any]] = {}
    default_recommendations: ClassVar[List[str]] = []
    uses_knowledge_graph: ClassVar[bool] = False

    def __init__(
        self,
        llm_service: LLMGateway,
        capability_executor=None,
        knowledge_agent_graph=None,
    ):
        super().__init__(llm_service, capability_executor)
        self.knowledge_agent = knowledge_agent_graph
        self._profile = AgentProfile(**self.profile_kwargs)

    def get_profile(self) -> AgentProfile:
        return self._profile

    def _build_sources(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "source": "state_snapshot",
                "domain": self.get_profile().domain,
                "keys": sorted(state.keys()),
            }
        ]

    def _recommendations(self, task: ExecutiveTask) -> List[str]:
        if self.default_recommendations:
            return self.default_recommendations
        return [f"Proceed with the next step for {task.goal}."]

    def execute(
        self,
        task: ExecutiveTask,
        state: Dict[str, Any],
    ) -> ExecutiveResult:
        start_time = time.time()
        logger.info(
            "[%s] Executing task: %s",
            self.get_profile().agent_name,
            task.goal,
        )

        if self.uses_knowledge_graph and self.knowledge_agent:
            sub_state: Dict[str, Any] = {
                "question": task.description,
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
            result_state = self.knowledge_agent.run(sub_state)
            summary = result_state.get("answer") or (
                f"{self.get_profile().title} synthesized evidence for {task.goal}."
            )
            reasoning = (
                f"{self.get_profile().agent_name} used the knowledge graph "
                f"and returned a synthesized answer for {task.goal}."
            )
            metrics = {
                "execution_time_ms": (time.time() - start_time) * 1000,
                "knowledge_graph_used": True,
                "context_keys": len(state),
            }
            return self._create_result(
                task=task,
                summary=summary,
                reasoning=reasoning,
                recommendations=self._recommendations(task),
                sources=result_state.get("sources", []),
                metrics=metrics,
            )

        boundaries = ", ".join(self.get_profile().decision_boundaries)
        if not boundaries:
            boundaries = "executive scope only"
        prompt_strategy = self.get_profile().prompt_strategy
        if not prompt_strategy:
            prompt_strategy = "structured and outcome-oriented"

        summary = f"{self.get_profile().title} completed task: {task.goal}"
        reasoning = f"Boundaries: {boundaries}. Prompt: {prompt_strategy}."
        metrics = {
            "execution_time_ms": (time.time() - start_time) * 1000,
            "context_keys": len(state),
        }
        return self._create_result(
            task=task,
            summary=summary,
            reasoning=reasoning,
            recommendations=self._recommendations(task),
            sources=self._build_sources(state),
            metrics=metrics,
        )


class CEOAgent(DomainExecutiveAgent):
    profile_kwargs = {
        "agent_name": "CEO Agent",
        "title": "Chief Executive Officer",
        "domain": "Enterprise Leadership",
        "description": "Final executive arbitration and synthesis.",
        "capabilities": [
            Capability.STRATEGIC_LEADERSHIP,
            Capability.REPORT_GENERATION,
            Capability.RISK_ANALYSIS,
        ],
        "supported_task_types": [
            "Executive Decision",
            "Strategic Prioritization",
            "Portfolio Review",
            "Cross-Functional Arbitration",
        ],
        "required_tools": ["collaboration", "governance", "analytics"],
        "supported_sources": [
            "Supervisor",
            "Governance",
            "Analytics",
            "Collaboration",
        ],
        "responsibilities": [
            "Set direction",
            "Resolve tradeoffs",
            "Produce final response",
        ],
        "decision_boundaries": [
            "Does not replace governance approvals",
            "Does not run low-level operations",
        ],
        "memory_usage": "Strategic memory and governance history.",
        "prompt_strategy": "Concise and tradeoff-aware.",
        "delegation_strategy": "Delegates domain work, then consolidates.",
        "outputs": ["Executive memo", "decision summary", "escalation note"],
        "supervisor_interaction": "Top-level synthesis role.",
        "governance_interaction": "Requests approval gates.",
        "workflow_engine_interaction": "Approves or blocks workflows.",
        "decision_authority": ["Final executive arbitration and veto"],
        "inputs": ["Council recommendations", "Strategic objectives"],
        "memory_requirements": ["Strategic memory", "Governance history"],
        "approval_requirements": ["Board of Directors for major shifts"],
        "escalation_rules": ["Board of Directors"],
    }
    default_recommendations = [
        "Align stakeholders on the decision.",
        "Validate governance and approval needs.",
    ]


class COOAgent(DomainExecutiveAgent):
    profile_kwargs = {
        "agent_name": "COO Agent",
        "title": "Chief Operations Officer",
        "domain": "Operations",
        "description": "Operational cadence, coordination, throughput.",
        "capabilities": [
            Capability.OPERATIONS_LEADERSHIP,
            Capability.TECHNICAL_PLANNING,
            Capability.REPORT_GENERATION,
        ],
        "supported_task_types": [
            "Operating Plan",
            "Process Review",
            "Execution Coordination",
        ],
        "required_tools": ["workflow", "collaboration", "telemetry"],
        "supported_sources": ["Operations", "Workflow", "Telemetry"],
        "responsibilities": [
            "Coordinate execution",
            "Monitor throughput",
            "Enforce standards",
        ],
        "decision_boundaries": [
            "Does not authorize capital allocation",
            "Does not issue legal rulings",
        ],
        "memory_usage": "Operational memory and incidents.",
        "prompt_strategy": "Operational and reliability-focused.",
        "delegation_strategy": ("Delegates to workflow and incident specialists"),
        "outputs": ["Operating directive", "execution summary", "blockers"],
        "supervisor_interaction": "Provides status aggregation.",
        "governance_interaction": "Flags actions needing risk review.",
        "workflow_engine_interaction": "Coordinates workflow execution.",
        "decision_authority": ["Operational procedures", "Execution sequencing"],
        "inputs": ["Throughput metrics", "Operational plans"],
        "memory_requirements": ["Operational memory", "Incident history"],
        "approval_requirements": ["CEO approval for company-wide process changes"],
        "escalation_rules": ["Escalate to CEO for execution blockers"],
    }
    default_recommendations = [
        "Sequence the next operational steps.",
        "Confirm owners and dependencies.",
    ]


class CFOAgent(DomainExecutiveAgent):
    profile_kwargs = {
        "agent_name": "CFO Agent",
        "title": "Chief Financial Officer",
        "domain": "Finance",
        "description": "Budget, forecasting, cost control.",
        "capabilities": [
            Capability.FINANCIAL_LEADERSHIP,
            Capability.RISK_ANALYSIS,
            Capability.REPORT_GENERATION,
        ],
        "supported_task_types": [
            "Financial Analysis",
            "Budget Review",
            "Forecasting",
        ],
        "required_tools": ["sql", "analytics", "erp"],
        "supported_sources": ["Finance", "ERP", "Analytics"],
        "responsibilities": [
            "Manage spend",
            "Review tradeoffs",
            "Approve budget-sensitive actions",
        ],
        "decision_boundaries": [
            "Does not own product or engineering direction",
        ],
        "memory_usage": "Financial memory and forecast context.",
        "prompt_strategy": "Quantitative and risk-aware.",
        "delegation_strategy": "Delegates analysis and escalates approvals.",
        "outputs": ["Financial memo", "budget approval", "forecast summary"],
        "supervisor_interaction": "Finance gate in executive decisions.",
        "governance_interaction": "Required approver for finance commitments.",
        "workflow_engine_interaction": "Blocks or approves finance workflows.",
        "decision_authority": ["Budget allocation", "Financial forecasting"],
        "inputs": ["Cost estimates", "Financial models"],
        "memory_requirements": ["Financial memory", "Forecast context"],
        "approval_requirements": ["CEO approval for budget overrides"],
        "escalation_rules": ["Escalate to CEO for budget violations"],
    }
    default_recommendations = [
        "Validate budget impact before proceeding.",
        "Update forecast and variance assumptions.",
    ]


class CMOAgent(DomainExecutiveAgent):
    profile_kwargs = {
        "agent_name": "CMO Agent",
        "title": "Chief Marketing Officer",
        "domain": "Marketing",
        "description": "Campaign strategy and growth analysis.",
        "capabilities": [
            Capability.MARKETING_LEADERSHIP,
            Capability.DOCUMENT_ANALYSIS,
            Capability.REPORT_GENERATION,
        ],
        "supported_task_types": [
            "Marketing Analysis",
            "Campaign Planning",
            "Brand Strategy",
        ],
        "required_tools": ["crm", "analytics", "document_search"],
        "supported_sources": ["CRM", "Marketing", "Analytics"],
        "responsibilities": [
            "Shape demand",
            "Review campaigns",
            "Refine positioning",
        ],
        "decision_boundaries": [
            "Does not override legal or privacy approvals",
        ],
        "memory_usage": "Marketing memory and customer context.",
        "prompt_strategy": "Audience-aware and performance-driven.",
        "delegation_strategy": (
            "Delegates evidence gathering to research and analytics"
        ),
        "outputs": ["Campaign brief", "market insight", "growth rec"],
        "supervisor_interaction": "Provides marketing direction.",
        "governance_interaction": "Flags consent-sensitive actions.",
        "workflow_engine_interaction": "Coordinates campaign workflows.",
        "decision_authority": ["Brand strategy", "Campaign execution"],
        "inputs": ["Market research", "Campaign performance"],
        "memory_requirements": ["Marketing memory", "Customer context"],
        "approval_requirements": ["CLO approval for privacy-sensitive campaigns"],
        "escalation_rules": ["Escalate to CEO for brand risks"],
    }
    default_recommendations = [
        "Validate segmentation and channel assumptions.",
        "Align messaging with brand and conversion goals.",
    ]


class CHROAgent(DomainExecutiveAgent):
    profile_kwargs = {
        "agent_name": "CHRO Agent",
        "title": "Chief Human Resources Officer",
        "domain": "People Operations",
        "description": "Hiring, workforce planning, policy alignment.",
        "capabilities": [
            Capability.HUMAN_RESOURCES_LEADERSHIP,
            Capability.DOCUMENT_ANALYSIS,
            Capability.REPORT_GENERATION,
        ],
        "supported_task_types": [
            "Hiring Workflow",
            "Workforce Planning",
            "Org Review",
        ],
        "required_tools": ["hr", "calendar", "document_search"],
        "supported_sources": ["HR", "Policy", "Collaboration"],
        "responsibilities": [
            "Guide hiring",
            "Support workforce planning",
            "Review policy alignment",
        ],
        "decision_boundaries": [
            "Does not make legal rulings",
            "Does not manage payroll execution",
        ],
        "memory_usage": "HR memory and org context.",
        "prompt_strategy": "Fairness- and policy-aware.",
        "delegation_strategy": ("Delegates analysis to planning and analytics roles"),
        "outputs": ["Hiring rec", "staffing plan", "policy note"],
        "supervisor_interaction": "Reports human-capital impacts.",
        "governance_interaction": "Engages governance for privacy rules.",
        "workflow_engine_interaction": "Coordinates hiring workflows.",
        "decision_authority": ["People policies", "Workforce planning"],
        "inputs": ["Staffing requirements", "Policy drafts"],
        "memory_requirements": ["HR memory", "Org context"],
        "approval_requirements": ["CLO approval for compliance-related policies"],
        "escalation_rules": ["Escalate to CEO for critical talent loss"],
    }
    default_recommendations = [
        "Confirm role scope and hiring criteria.",
        "Check workforce impact and policy fit.",
    ]


class CLOAgent(DomainExecutiveAgent):
    profile_kwargs = {
        "agent_name": "CLO Agent",
        "title": "Chief Legal Officer",
        "domain": "Legal",
        "description": "Legal review and compliance interpretation.",
        "capabilities": [
            Capability.LEGAL_LEADERSHIP,
            Capability.RISK_ANALYSIS,
            Capability.DOCUMENT_ANALYSIS,
        ],
        "supported_task_types": [
            "Legal Review",
            "Contract Review",
            "Compliance Analysis",
        ],
        "required_tools": ["document_search", "workflow", "governance"],
        "supported_sources": ["Legal", "Contracts", "Policy"],
        "responsibilities": [
            "Review legal risk",
            "Interpret contracts",
            "Approve legal language",
        ],
        "decision_boundaries": [
            "Does not own business strategy",
            "Does not authorize technical changes",
        ],
        "memory_usage": "Legal memory and clause history.",
        "prompt_strategy": "Precedent-driven and risk-focused.",
        "delegation_strategy": ("Delegates fact finding to research and planning"),
        "outputs": ["Legal opinion", "redline summary", "approval note"],
        "supervisor_interaction": "Provides legal escalation.",
        "governance_interaction": "Primary legal approver.",
        "workflow_engine_interaction": "Approves legal-sensitive workflows.",
        "decision_authority": ["Legal compliance", "Risk mitigation"],
        "inputs": ["Contracts", "Policy documents"],
        "memory_requirements": ["Legal memory", "Clause history"],
        "approval_requirements": ["None (Ultimate legal authority)"],
        "escalation_rules": ["Escalate to CEO for high legal risk"],
    }
    default_recommendations = [
        "Verify contractual exposure before proceeding.",
        "Capture required legal approvals.",
    ]


class CISOAgent(DomainExecutiveAgent):
    profile_kwargs = {
        "agent_name": "CISO Agent",
        "title": "Chief Information Security Officer",
        "domain": "Security",
        "description": "Security posture, threat response, governance.",
        "capabilities": [
            Capability.SECURITY_LEADERSHIP,
            Capability.SECURITY_REVIEW,
            Capability.RISK_ANALYSIS,
        ],
        "supported_task_types": [
            "Security Review",
            "Threat Response",
            "Access Governance",
        ],
        "required_tools": ["security", "telemetry", "governance"],
        "supported_sources": ["Security", "Telemetry", "Policy"],
        "responsibilities": [
            "Assess threats",
            "Review controls",
            "Gate risky actions",
        ],
        "decision_boundaries": [
            "Does not own finance or HR approvals",
        ],
        "memory_usage": "Security memory and control history.",
        "prompt_strategy": "Threat-model oriented.",
        "delegation_strategy": ("Delegates triage to incident response and analytics"),
        "outputs": ["Security finding", "mitigation plan", "approval note"],
        "supervisor_interaction": "Provides security approval or escalation.",
        "governance_interaction": "Mandatory approver for high-risk actions.",
        "workflow_engine_interaction": "Controls security workflows.",
        "decision_authority": ["Security controls", "Access governance"],
        "inputs": ["Threat reports", "System architectures"],
        "memory_requirements": ["Security memory", "Control history"],
        "approval_requirements": ["None (Can veto on security grounds)"],
        "escalation_rules": ["Escalate to CEO for critical vulnerabilities"],
    }
    default_recommendations = [
        "Apply the least-privilege path.",
        "Review blast radius and mitigation options.",
    ]


class CIOAgent(DomainExecutiveAgent):
    profile_kwargs = {
        "agent_name": "CIO Agent",
        "title": "Chief Information Officer",
        "domain": "Information Systems",
        "description": "Enterprise systems, integrations, reliability.",
        "capabilities": [
            Capability.INFORMATION_LEADERSHIP,
            Capability.SYSTEM_DESIGN,
            Capability.TECHNICAL_PLANNING,
        ],
        "supported_task_types": [
            "Systems Review",
            "Integration Strategy",
            "Platform Planning",
        ],
        "required_tools": ["sql", "telemetry", "workflow"],
        "supported_sources": ["Systems", "Telemetry", "Architecture"],
        "responsibilities": [
            "Guide systems direction",
            "Review integrations",
            "Protect reliability",
        ],
        "decision_boundaries": ["Does not override governance approvals"],
        "memory_usage": "Systems memory and architecture history.",
        "prompt_strategy": "Architecture-aware and maintainability-centered.",
        "delegation_strategy": "Delegates to planning, research, analytics.",
        "outputs": ["Platform rec", "integration plan", "system brief"],
        "supervisor_interaction": "Provides systems context.",
        "governance_interaction": "Engages governance for change control.",
        "workflow_engine_interaction": "Coordinates systems workflows.",
        "decision_authority": ["Enterprise systems", "IT integrations"],
        "inputs": ["System requirements", "Integration requests"],
        "memory_requirements": ["Systems memory", "Architecture history"],
        "approval_requirements": ["CFO approval for IT spend"],
        "escalation_rules": ["Escalate to CEO for system outages"],
    }
    default_recommendations = [
        "Validate systems impact before implementation.",
        "Confirm observability and rollback readiness.",
    ]


class CSOAgent(DomainExecutiveAgent):
    profile_kwargs = {
        "agent_name": "CSO Agent",
        "title": "Chief Strategy Officer",
        "domain": "Strategy",
        "description": "Long-horizon strategy and scenarios.",
        "capabilities": [
            Capability.STRATEGIC_LEADERSHIP,
            Capability.RISK_ANALYSIS,
            Capability.REPORT_GENERATION,
        ],
        "supported_task_types": [
            "Strategic Review",
            "Scenario Planning",
            "Portfolio Strategy",
        ],
        "required_tools": ["analytics", "document_search", "knowledge_search"],
        "supported_sources": ["Strategy", "Research", "Analytics"],
        "responsibilities": [
            "Evaluate options",
            "Quantify downside",
            "Recommend direction",
        ],
        "decision_boundaries": ["Does not perform tactical execution"],
        "memory_usage": "Strategic memory and scenario history.",
        "prompt_strategy": "Scenario-based and leverage-oriented.",
        "delegation_strategy": "Delegates research and analysis.",
        "outputs": [
            "Strategy memo",
            "scenario summary",
            "prioritized options",
        ],
        "supervisor_interaction": "Provides strategic framing.",
        "governance_interaction": "Requests review for high-impact changes.",
        "workflow_engine_interaction": "Supports strategy planning workflows.",
        "decision_authority": ["Long-term strategy", "Market positioning"],
        "inputs": ["Market trends", "Scenario analyses"],
        "memory_requirements": ["Strategic memory", "Scenario history"],
        "approval_requirements": ["CEO approval for strategic pivots"],
        "escalation_rules": ["Escalate to CEO for strategic misalignment"],
    }
    default_recommendations = [
        "Compare strategic options and tradeoffs.",
        "Document downside cases and assumptions.",
    ]


class CPOAgent(DomainExecutiveAgent):
    profile_kwargs = {
        "agent_name": "CPO Agent",
        "title": "Chief Product Officer",
        "domain": "Product",
        "description": "Product vision, roadmap, customer tradeoffs.",
        "capabilities": [
            Capability.PRODUCT_LEADERSHIP,
            Capability.DOCUMENT_ANALYSIS,
            Capability.REPORT_GENERATION,
        ],
        "supported_task_types": [
            "Product Review",
            "Roadmap Planning",
            "Customer Value Analysis",
        ],
        "required_tools": ["crm", "analytics", "research"],
        "supported_sources": ["Product", "Customer", "Analytics"],
        "responsibilities": [
            "Prioritize roadmap",
            "Interpret customer value",
            "Sequence delivery",
        ],
        "decision_boundaries": [
            "Does not own security or legal approvals",
        ],
        "memory_usage": "Product memory and customer feedback.",
        "prompt_strategy": "Customer-centered and sequencing-aware.",
        "delegation_strategy": (
            "Delegates evidence gathering to research and analytics"
        ),
        "outputs": ["Product brief", "roadmap rec", "priority list"],
        "supervisor_interaction": "Provides product tradeoff analysis.",
        "governance_interaction": ("Flags sensitive data and compliance actions"),
        "workflow_engine_interaction": "Coordinates product workflows.",
        "decision_authority": ["Product roadmap", "Feature prioritization"],
        "inputs": ["Customer feedback", "Product analytics"],
        "memory_requirements": ["Product memory", "Customer feedback"],
        "approval_requirements": ["CTO alignment for technical feasibility"],
        "escalation_rules": ["Escalate to CEO for roadmap conflicts"],
    }
    default_recommendations = [
        "Clarify customer impact and priority order.",
        "Validate roadmap dependencies and timing.",
    ]


class KnowledgeAgent(DomainExecutiveAgent):
    uses_knowledge_graph = True
    profile_kwargs = {
        "agent_name": "Knowledge Agent",
        "title": "Knowledge Synthesis Agent",
        "domain": "Enterprise Knowledge",
        "description": "Retrieval, synthesis, and citations.",
        "capabilities": [
            Capability.KNOWLEDGE_SYNTHESIS,
            Capability.DOCUMENT_ANALYSIS,
            Capability.REPORT_GENERATION,
        ],
        "supported_task_types": [
            "Knowledge Retrieval",
            "Evidence Synthesis",
            "Citation Review",
        ],
        "required_tools": ["document_search", "sql", "web_search"],
        "supported_sources": ["Documents", "Memory", "Knowledge Base", "Web"],
        "responsibilities": [
            "Retrieve evidence",
            "Normalize knowledge",
            "Preserve citations",
        ],
        "decision_boundaries": ["Does not make final executive decisions"],
        "memory_usage": "Domain memory and source provenance.",
        "prompt_strategy": "Evidence-first and traceable.",
        "delegation_strategy": "Delegates retrieval to tools.",
        "outputs": ["Cited brief", "evidence pack", "source summary"],
        "supervisor_interaction": "Evidence provider for the supervisor.",
        "governance_interaction": "Observes access and retention constraints.",
        "workflow_engine_interaction": "Feeds knowledge steps into workflows.",
    }
    default_recommendations = [
        "Cite the strongest source and preserve provenance.",
        "Separate facts from interpretation.",
    ]


class ResearchAgent(DomainExecutiveAgent):
    profile_kwargs = {
        "agent_name": "Research Agent",
        "title": "Research Agent",
        "domain": "Research",
        "description": "Deep research and source comparison.",
        "capabilities": [
            Capability.RESEARCH_SYNTHESIS,
            Capability.DOCUMENT_ANALYSIS,
            Capability.RISK_ANALYSIS,
        ],
        "supported_task_types": [
            "Research Brief",
            "Source Comparison",
            "Evidence Review",
        ],
        "required_tools": [
            "web_search",
            "document_search",
            "knowledge_search",
        ],
        "supported_sources": ["Web", "Documents", "Knowledge", "Codebase"],
        "responsibilities": [
            "Rank evidence",
            "Check contradictions",
            "Produce research memos",
        ],
        "decision_boundaries": ["Does not approve execution actions"],
        "memory_usage": "Research memory and investigation history.",
        "prompt_strategy": "Hypothesis-driven and evidence-ranked.",
        "delegation_strategy": "Delegates parallel retrieval to tools.",
        "outputs": ["Research memo", "evidence pack", "comparison table"],
        "supervisor_interaction": "Investigation worker for the supervisor.",
        "governance_interaction": "Respects source access controls.",
        "workflow_engine_interaction": "Feeds research workflows.",
    }
    default_recommendations = [
        "Validate at least one independent source.",
        "Document contradictions and confidence.",
    ]


class PlanningAgent(DomainExecutiveAgent):
    profile_kwargs = {
        "agent_name": "Planning Agent",
        "title": "Planning Agent",
        "domain": "Planning",
        "description": "Task decomposition and sequencing.",
        "capabilities": [
            Capability.PLANNING_SYNTHESIS,
            Capability.TECHNICAL_PLANNING,
            Capability.REPORT_GENERATION,
        ],
        "supported_task_types": [
            "Plan Draft",
            "Dependency Analysis",
            "Scheduling",
        ],
        "required_tools": ["workflow", "analytics", "memory"],
        "supported_sources": ["Plans", "Memory", "Workflow", "Analytics"],
        "responsibilities": [
            "Break goals into tasks",
            "Sequence dependencies",
            "Surface risks",
        ],
        "decision_boundaries": [
            "Does not issue financial or legal approvals",
        ],
        "memory_usage": "Planning memory and prior plans.",
        "prompt_strategy": "Concrete and decision-point oriented.",
        "delegation_strategy": "Delegates implementation work.",
        "outputs": ["Plan", "milestones", "risk register"],
        "supervisor_interaction": "Provides planning structure.",
        "governance_interaction": "Prepares plans for review.",
        "workflow_engine_interaction": "Supports workflow construction.",
    }
    default_recommendations = [
        "Validate dependencies before execution.",
        "Add review checkpoints for high-risk tasks.",
    ]


class AnalyticsAgent(DomainExecutiveAgent):
    profile_kwargs = {
        "agent_name": "Analytics Agent",
        "title": "Analytics Agent",
        "domain": "Analytics",
        "description": "Trend analysis and KPI synthesis.",
        "capabilities": [
            Capability.ANALYTICS_SYNTHESIS,
            Capability.REPORT_GENERATION,
            Capability.RISK_ANALYSIS,
        ],
        "supported_task_types": [
            "KPI Review",
            "Trend Analysis",
            "Executive Reporting",
        ],
        "required_tools": ["sql", "telemetry", "document_search"],
        "supported_sources": ["Metrics", "Telemetry", "Reports"],
        "responsibilities": [
            "Analyze metrics",
            "Detect anomalies",
            "Summarize trends",
        ],
        "decision_boundaries": ["Does not change operational systems"],
        "memory_usage": "Analytics memory and baselines.",
        "prompt_strategy": "Quantitative and baseline-driven.",
        "delegation_strategy": "Delegates data retrieval to tools.",
        "outputs": ["Dashboard summary", "trend report", "executive brief"],
        "supervisor_interaction": "Supports executive decisions with data.",
        "governance_interaction": "Observes data access and reporting rules.",
        "workflow_engine_interaction": "Produces reporting workflows.",
    }
    default_recommendations = [
        "Compare against baseline and prior periods.",
        "Call out anomalies that need follow-up.",
    ]
