import os
import glob
import json
import uuid
import time
from fastapi import BackgroundTasks
from app.services.chat_service import ChatService
from app.api.v1.chat import get_llm_service, get_cross_encoder_service, get_memory_service
from app.core.database import SessionLocal

class BenchmarkMode:
    LOCAL = "local"
    CI = "ci"
    PRODUCTION = "production"

class EndToEndScenarios:
    def __init__(self, mode: str = BenchmarkMode.LOCAL):
        self.mode = mode
        self.datasets_dir = os.path.join(os.path.dirname(__file__), "datasets", "scenarios")

    def _load_datasets(self):
        datasets = []
        for file in glob.glob(os.path.join(self.datasets_dir, "*.json")):
            with open(file, "r", encoding="utf-8") as f:
                datasets.extend(json.load(f))
        return datasets

    def run_all(self):
        datasets = self._load_datasets()
        results = {}
        
        # Instantiate services
        from app.core.database import SessionLocal, Base, engine
        import app.models
        try:
            from app.collaboration.session.collaboration_session import CollaborationSession
            from app.collaboration.messaging.message_models import CollaborationMessage
        except ImportError:
            pass
        Base.metadata.create_all(bind=engine)
        from app.services.vectorstore.qdrant_service import create_collection
        create_collection()
        db = SessionLocal()
        llm = get_llm_service()
        memory = get_memory_service(db, llm)
        
        # We need the full SupervisorGraph
        from app.api.v1.agent import get_supervisor_graph, get_capability_inference_service, get_graph_router, get_service_container, get_cross_encoder_service
        cross_encoder = get_cross_encoder_service()
        container = get_service_container(memory, llm, cross_encoder)
        knowledge_agent_graph = get_graph_router(container)
        capability_service = get_capability_inference_service()
        
        supervisor = get_supervisor_graph(
            db=db,
            memory_service=memory,
            llm_service=llm,
            capability_service=capability_service,
            knowledge_agent_graph=knowledge_agent_graph
        )
        
        session_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        
        # Limit to 5 for Local mode to prevent massive loops/costs unless CI/Prod
        limit = 5 if self.mode == BenchmarkMode.LOCAL else len(datasets)
        print(f"Running in {self.mode} mode. Processing {limit} queries out of {len(datasets)}.")
        
        import asyncio
        
        for i, data in enumerate(datasets[:limit]):
            q_id = data["scenario_id"]
            query = data["query"]
            print(f"Executing {q_id}: {query}")
            
            try:
                start_time = time.time()
                
                initial_state = {
                    "user_input": query,
                    "session_id": session_id,
                    "conversation_id": conversation_id,
                    "memory_context": "",
                    "execution_time_ms": 0.0,
                    "selected_agents": [],
                    "completed_tasks": [],
                    "failed_tasks": [],
                }
                
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                from app.operations.tracing.trace_manager import TraceManager
                for exporter in TraceManager._exporters:
                    if hasattr(exporter, "traces"):
                        exporter.traces.clear()
                    
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                    final_state = asyncio.run(supervisor.run(initial_state))
                else:
                    final_state = loop.run_until_complete(supervisor.run(initial_state))
                    
                response_text = final_state.get("final_response", "")
                latency = (time.time() - start_time) * 1000
                
                traces_list = []
                for exporter in TraceManager._exporters:
                    if hasattr(exporter, "get_all_traces"):
                        for trace_id, spans in exporter.get_all_traces().items():
                            traces_list.extend(spans)
                            
                from evaluation.models import EvaluationResult, ExecutionStatus, FailureCategory
                
                # Check for AI vs Infra failure based on final response or traces
                # If there's an answer, it's SUCCESS
                exec_status = ExecutionStatus.SUCCESS if response_text else ExecutionStatus.FAILED
                fail_cat = FailureCategory.NONE
                fail_rsn = None
                
                if not response_text:
                    fail_cat = FailureCategory.UNKNOWN
                    fail_rsn = "No valid response generated"
                    
                results[q_id] = EvaluationResult(
                    scenario_id=q_id,
                    query=query,
                    ground_truth=data.get("ground_truth", ""),
                    expected_capability=data.get("expected_capability", "unknown"),
                    expected_agent=data.get("expected_agent", "unknown"),
                    expected_provider=data.get("expected_provider", "unknown"),
                    expected_tools=data.get("expected_tools", []),
                    expected_guardrails=data.get("expected_guardrails", []),
                    success=bool(response_text),
                    execution_status=exec_status,
                    failure_category=fail_cat,
                    failure_reason=fail_rsn,
                    actual_answer=response_text,
                    latency_ms=latency,
                    traces=traces_list
                )
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"SCENARIO FAILED {q_id}: {e}")
                error_str = str(e).lower()
                fail_cat = FailureCategory.INFRASTRUCTURE
                fail_rsn = str(e)
                
                if "quota" in error_str or "rate limit" in error_str:
                    fail_cat = FailureCategory.PROVIDER
                elif "timeout" in error_str:
                    fail_cat = FailureCategory.PROVIDER
                elif "no providers available" in error_str:
                    fail_cat = FailureCategory.ROUTING
                    
                results[q_id] = EvaluationResult(
                    scenario_id=q_id,
                    query=query,
                    ground_truth=data.get("ground_truth", ""),
                    expected_capability=data.get("expected_capability", "unknown"),
                    expected_agent=data.get("expected_agent", "unknown"),
                    expected_provider=data.get("expected_provider", "unknown"),
                    expected_tools=data.get("expected_tools", []),
                    expected_guardrails=data.get("expected_guardrails", []),
                    success=False,
                    execution_status=ExecutionStatus.FAILED,
                    failure_category=fail_cat,
                    failure_reason=fail_rsn,
                    error=str(e),
                    traces=[]
                )
                
        db.close()
        return results
