import asyncio
from typing import Any

from bluemarz.core import registries
from bluemarz.core.interfaces import Agent, AssignmentExecutor, Session
from bluemarz.core.models import (
    AddFileResult,
    AddMessageResult,
    AssignmentRunResult,
    RunResult,
    RunResultType,
    SessionMessage,
    ToolCall,
    ToolCallResult,
    ToolSpec,
    ToolType,
)

import logging

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)


class Assignment:
    agent: Agent
    session: Session
    executor: type[AssignmentExecutor]
    run_id: str | None
    last_result: RunResult | None
    params: dict[str, Any]

    def __init__(
        self, agent: Agent, session: Session, run_id: str = None, **kwargs
    ) -> None:
        self.agent = agent
        self.session = session
        self.run_id = run_id
        self.executor = registries.get_executor(agent, session)
        self.params = kwargs

        self._validate_assignment()

    def _validate_assignment(self) -> None:
        self.executor.validate_assignment(
            self.agent, self.session, self.run_id, **self.params
        )

    def add_message(self, message: SessionMessage) -> AddMessageResult:
        return self.session.add_message(message)

    def add_file(self) -> AddFileResult:
        return self.session.add_file()

    async def run_once(self) -> RunResult:
        result = self.executor.execute(
            self.agent, self.session, self.run_id, **self.params
        )
        self.last_result = result
        self.run_id = result.run_id

        return result

    def submit_tool_calls(self, tool_call_results: list[ToolCallResult]):
        self.executor.submit_tool_calls(
            self.agent, self.session, self.run_id, tool_call_results, **self.params
        )

    def prepare_for_async_tool_calls(self):
        self.executor.prepare_for_async_tool_calls(
            self.agent, self.session, self.run_id, **self.params
        )

    async def run_until_breakpoint(self) -> AssignmentRunResult:
        return await _run_assignment_until_breakpoint(self)


def _tool_can_be_sync_called(toolSpec: ToolSpec) -> bool:
    return toolSpec.tool_type == ToolType.SYNC and registries.has_sync_tool_executor(
        toolSpec.name
    )


async def _execute_sync_tool_call(toolCall: ToolCall) -> ToolCallResult:
    executor_class = registries.get_sync_tool_executor(toolCall.tool.name)
    return executor_class.execute_call(toolCall)


async def _run_assignment_until_breakpoint(
    assignment: Assignment,
) -> AssignmentRunResult:
    done: bool = False
    while not done:
        result = await assignment.run_once()
        done = True

        if result.result_type == RunResultType.TOOL_CALL:
            if all([_tool_can_be_sync_called(tc.tool) for tc in result.tool_calls]):
                try:
                    # process all calls synchronously
                    async with asyncio.TaskGroup() as tg:
                        tasks = [
                            tg.create_task(_execute_sync_tool_call(tc))
                            for tc in result.tool_calls
                        ]
                    tc_results = [task.result() for task in tasks]
                    assignment.submit_tool_calls(tc_results)

                    # will run again after this
                    done = False

                except Exception as ex:
                    # if any failures fallback to async case
                    # TODO: log
                    logging.info(f"Error processing sync tools: {ex}")
                    return AssignmentRunResult(
                        session_id=assignment.session.spec.id,
                        last_run_result=assignment.last_result,
                    )
            else:
                assignment.prepare_for_async_tool_calls()

    return AssignmentRunResult(
        session_id=assignment.session.spec.id, last_run_result=assignment.last_result
    )
