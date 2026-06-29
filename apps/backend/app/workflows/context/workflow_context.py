from typing import Any, Dict
import copy


class WorkflowContext:
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self._variables: Dict[str, Any] = {}
        self._artifacts: Dict[str, Any] = {}
        self._task_outputs: Dict[str, Dict[str, Any]] = {}

    def set_variable(self, key: str, value: Any) -> None:
        self._variables[key] = copy.deepcopy(value)

    def get_variable(self, key: str, default: Any = None) -> Any:
        return copy.deepcopy(self._variables.get(key, default))

    def set_artifact(self, name: str, data: Any) -> None:
        self._artifacts[name] = data

    def get_artifact(self, name: str) -> Any:
        return self._artifacts.get(name)

    def set_task_output(self, task_id: str, outputs: Dict[str, Any]) -> None:
        self._task_outputs[task_id] = copy.deepcopy(outputs)

    def get_task_output(self, task_id: str) -> Dict[str, Any]:
        return copy.deepcopy(self._task_outputs.get(task_id, {}))

    def get_all_state(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "variables": self._variables,
            "artifacts": self._artifacts,
            "task_outputs": self._task_outputs,
        }
