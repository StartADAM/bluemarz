from bluemarz.core.interfaces import SyncToolExecutor
from bluemarz.core.models import ToolCall, ToolCallResult
from bluemarz.core.class_registry import sync_tool_executor


@sync_tool_executor
class TestToolExecutor(SyncToolExecutor):
    @classmethod
    def tool_name(cls) -> str:
        return "test_tool"

    @classmethod
    def execute_call(cls, toll_call: ToolCall) -> ToolCallResult:
        return ToolCallResult(tool_call=toll_call, text="32")