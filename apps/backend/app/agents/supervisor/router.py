import logging
from app.agents.supervisor.schemas import Task, TaskStatus
from app.agents.base.registry import AgentRegistry
from app.agents.base.task import ExecutiveTask

logger = logging.getLogger(__name__)

class AgentRouter:
    """
    Routes a Task to the appropriate specialist agent for execution via the AgentRegistry.
    Falls back to the Knowledge Agent for direct retrieval tasks if no executive is assigned.
    """
    
    def __init__(self, agent_registry: AgentRegistry, knowledge_agent_graph=None):
        self.agent_registry = agent_registry
        self.knowledge_agent = knowledge_agent_graph
        
    def route_and_execute(self, task: Task, state: dict) -> dict:
        """
        Selects the appropriate agent, executes the task, and returns the result.
        """
        agent_name = task.assigned_agent or "Knowledge Agent"
        logger.info(f"Routing task {task.task_id} to {agent_name}")
        
        # Try to find a registered Executive Agent
        executive = self.agent_registry.get_agent(agent_name)
        
        if executive:
            # Map Supervisor Task to Executive Task
            exec_task = ExecutiveTask(
                task_id=task.task_id,
                goal=task.goal,
                description=task.description,
                priority=task.priority,
                dependencies=task.dependencies,
                assigned_agent=agent_name,
                context=task.context,
                artifacts=task.artifacts
            )
            
            try:
                result = executive.execute(exec_task, state)
                task.status = TaskStatus.COMPLETED
                return {
                    "task_id": task.task_id,
                    "agent_used": agent_name,
                    "result": result.reasoning + "\n\n" + result.summary,
                    "sources": result.sources,
                    "metrics": result.execution_metrics
                }
            except Exception as e:
                logger.error(f"Executive Agent {agent_name} failed: {e}")
                task.status = TaskStatus.FAILED
                return {
                    "task_id": task.task_id,
                    "agent_used": agent_name,
                    "result": f"Execution failed: {str(e)}",
                    "sources": [],
                    "metrics": {}
                }
        
        # Fallback for placeholders or direct Knowledge Agent calls
        if agent_name != "Knowledge Agent":
            logger.warning(f"{agent_name} not found in registry or is a placeholder. Routing to Knowledge Agent.")
            agent_name = "Knowledge Agent"
            
        # Execute using Knowledge Agent (existing RAG LangGraph)
        if self.knowledge_agent:
            logger.info("Executing task via Knowledge Agent graph.")
            sub_state = {
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
            task.status = TaskStatus.COMPLETED
            
            return {
                "task_id": task.task_id,
                "agent_used": "Knowledge Agent",
                "result": result_state.get("answer", ""),
                "sources": result_state.get("sources", []),
                "metrics": result_state.get("metrics", {})
            }
            
        else:
            logger.error("Knowledge Agent graph not provided to Router.")
            task.status = TaskStatus.FAILED
            return {
                "task_id": task.task_id,
                "agent_used": "None",
                "result": "Execution failed: No agent available to process this task.",
                "sources": [],
                "metrics": {}
            }
