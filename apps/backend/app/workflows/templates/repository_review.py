from app.workflows.builder.workflow_builder import WorkflowBuilder
from app.workflows.schemas.workflow import WorkflowCreate
from app.workflows.models.task import TaskType

def create_repository_review_workflow(repo_url: str, branch: str = "main") -> WorkflowBuilder:
    builder = WorkflowBuilder(WorkflowCreate(
        goal=f"Perform a comprehensive review of {repo_url}",
        description="Analyzes the repository for security, architecture, and code quality issues.",
        owner_agent="CTO",
        template_name="Repository Review"
    ))
    
    # Task 1: Clone/Fetch repo
    clone_task_id = builder.add_task(
        name="Fetch Repository",
        task_type=TaskType.CAPABILITY,
        required_capability="github_clone",
        inputs={"repo_url": repo_url, "branch": branch}
    )
    
    # Task 2: Security Scan
    sec_task_id = builder.add_task(
        name="Security Audit",
        task_type=TaskType.CAPABILITY,
        required_capability="security_scan",
        dependencies=[clone_task_id]
    )
    
    # Task 3: Architecture Analysis
    arch_task_id = builder.add_task(
        name="Architecture Analysis",
        task_type=TaskType.AGENT,
        assigned_agent="CTO",
        dependencies=[clone_task_id]
    )
    
    # Task 4: Final Report (Depends on Security and Architecture)
    builder.add_task(
        name="Generate Final Report",
        task_type=TaskType.CAPABILITY,
        required_capability="report_generator",
        dependencies=[sec_task_id, arch_task_id]
    )
    
    return builder
