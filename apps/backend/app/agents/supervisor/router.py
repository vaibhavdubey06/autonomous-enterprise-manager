import logging
from app.agents.supervisor.schemas import Task, TaskStatus

logger = logging.getLogger(__name__)

class AgentRouter:
    """
    Routes a Task to the appropriate specialist agent for execution.
    Currently routes everything to the Knowledge Agent (RAG pipeline) by default.
    """
    
    def __init__(self, knowledge_agent_graph=None):
        # We will inject the existing LangGraph (GraphRouter) as the knowledge_agent_graph
        self.knowledge_agent = knowledge_agent_graph
        
    def route_and_execute(self, task: Task, state: dict) -> dict:
        """
        Selects the appropriate agent, executes the task, and returns the result.
        """
        agent = task.assigned_agent or "Knowledge Agent"
        logger.info(f"Routing task {task.task_id} to {agent}")
        
        # Placeholder for future agents
        if agent == "CTO Agent":
            logger.warning("CTO Agent is a placeholder. Routing to Knowledge Agent.")
            agent = "Knowledge Agent"
        elif agent == "Memory Agent":
            logger.warning("Memory Agent is a placeholder. Routing to Knowledge Agent.")
            agent = "Knowledge Agent"
            
        # Execute using Knowledge Agent (existing RAG LangGraph)
        if self.knowledge_agent:
            logger.info("Executing task via Knowledge Agent graph.")
            # Map task into the format expected by the Knowledge Agent graph
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
