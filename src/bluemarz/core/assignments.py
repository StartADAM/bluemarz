import asyncio
from typing import Any

from bluemarz.core import class_registry
from bluemarz.core.interfaces import (
    Agent,
    AssignmentExecutor,
    Session,
    ToolImplementation,
    ToolDefinition,
    SyncTool,
)
from bluemarz.core.models import (
    AddFileResult,
    AddMessageResult,
    AssignmentRunResult,
    RunResult,
    RunResultType,
    SessionMessage,
    SessionFile,
    ToolCall,
    ToolCallResult,
    ToolSpec,
    ToolType,
    AssignmentSpec,
    SessionSpec,
    MessageRole,
)

import logging

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)


class Assignment:
    agent: Agent
    session: Session
    executor: type[AssignmentExecutor]
    last_tools_submitted: list[ToolSpec]
    run_id: str | None
    last_result: RunResult | None
    params: dict[str, Any]

    def __init__(
        self, agent: Agent, session: Session, run_id: str = None, **kwargs
    ) -> None:
        self.agent = agent
        self.session = session
        self.run_id = run_id
        self.executor = class_registry.get_executor(agent, session)
        self.last_tools_submitted = []
        self.params = kwargs

        self._validate_assignment()

    def _validate_assignment(self) -> None:
        self.executor.validate_assignment(
            self.agent, self.session, self.run_id, **self.params
        )

    def add_message(self, message: SessionMessage) -> AddMessageResult:
        return self.session.add_message(message)

    def add_file(self, file: SessionFile) -> AddFileResult:
        return self.session.add_file(file)

    def add_tools(self, tools: list[ToolImplementation]) -> None:
        self.agent.add_tools(tools)

    def add_tools_from_spec(self, tools: list[ToolSpec]) -> None:
        for t in tools:
            t.parameters = self.params | t.parameters
        self.agent.add_tools_from_spec(tools)

    "TODO: create test"
    async def run_once(self) -> RunResult:
        self.last_tools_submitted = []
        result = self.executor.execute(
            self.agent, self.session, self.run_id, **self.params
        )
        self.last_result = result
        self.run_id = result.run_id

        return result

    def submit_tool_calls(self, tool_call_results: list[ToolCallResult]) -> None:
        self.last_tools_submitted.extend(
            [tcr.tool_call.tool for tcr in tool_call_results]
        )
        self.executor.submit_tool_calls(
            self.agent, self.session, self.run_id, tool_call_results, **self.params
        )

    def _prepare_for_async_tool_calls(self) -> None:
        self.executor.prepare_for_async_tool_calls(
            self.agent, self.session, self.run_id, **self.params
        )

    def add_tool_call_results(self, tool_call_results: list[ToolCallResult]) -> None:
        for result in tool_call_results:
            self.last_tools_submitted.append(result.tool_call.tool)
            self.session.add_tool_call_result(result)

    "TODO: create test"
    async def run_until_breakpoint(self) -> AssignmentRunResult:
        self.last_tools_submitted = []
        return await _run_assignment_until_breakpoint(self)

    "TODO: create test"
    @classmethod
    def from_spec(cls, spec: AssignmentSpec) -> "Assignment":
        return _create_assignment_from_spec(spec)


def _create_assignment_from_spec(spec: AssignmentSpec) -> Assignment:
    agent = _get_agent(spec)
    session = _get_session(spec)

    if spec.query:
        session.add_message(SessionMessage(role=MessageRole.USER, text=spec.query))
    elif session.is_empty and agent.spec.default_query:
        session.add_message(
            SessionMessage(role=MessageRole.USER, text=agent.spec.default_query)
        )

    return Assignment(agent, session, None, **spec.parameters)


def _get_agent(spec: AssignmentSpec):
    spec.agent.parameters = _merge_parameters(spec.parameters, spec.agent.parameters)
    spec.agent.tools.extend(spec.additional_tools)

    for t in spec.agent.tools:
        t.parameters = _merge_parameters(spec.parameters, t.parameters)

    return class_registry.get_agent_class(spec.agent.type).from_spec(spec.agent)


def _get_session(spec: AssignmentSpec) -> Session:
    agent = spec.agent
    session = spec.session
    parameters = spec.parameters
    if not session:
        session = SessionSpec()

    if agent.session_type == "NativeSession":
        if not session.api_key:
            session.api_key = agent.api_key

        session.parameters = _merge_parameters(
            _merge_parameters(parameters, agent.parameters), session.parameters
        )
        session.type = agent.type + "NativeSession"
    else:
        session.parameters = _merge_parameters(parameters, session.parameters)
        if not session.type:
            session.type = agent.session_type

    return class_registry.get_session_class(session.type).from_spec(session)


def _merge_parameters(
    super_parameters: dict[str, Any], spec_parameters: dict[str, Any]
) -> dict[str, Any]:
    for key in spec_parameters:
        value = spec_parameters[key]
        if isinstance(value, str) and str(value).startswith("$parameters."):
            template_key = str(value).split(".", 2)[1]
            if template_key in super_parameters:
                spec_parameters[key] = super_parameters[template_key]

    return super_parameters | spec_parameters


def _tool_can_be_sync_called(definition: ToolDefinition) -> bool:
    return definition.spec.tool_type == ToolType.SYNC and (
            (definition.executor is not None and isinstance(definition.executor, SyncTool))
            or class_registry.has_sync_tool_executor(definition.spec.name)
        )


async def _execute_sync_tool_call(toolCall: ToolCall, definition: ToolDefinition) -> ToolCallResult:
    if definition.executor and isinstance(definition.executor, SyncTool):
        return definition.executor.call(toolCall)

    executor_class = class_registry.get_sync_tool_executor(toolCall.tool.name)
    return executor_class.execute_call(toolCall)


async def _run_assignment_until_breakpoint(
    assignment: Assignment,
) -> AssignmentRunResult:
    done: bool = False
    while not done:
        result = await assignment.run_once()
        tools_dict = {t.spec.name: t for t in assignment.agent.tools}
        done = True

        if result.result_type == RunResultType.TOOL_CALL:
            if all([_tool_can_be_sync_called(tools_dict.get(tc.tool.name)) for tc in result.tool_calls]):
                try:
                    # process all calls synchronously
                    async with asyncio.TaskGroup() as tg:
                        tasks = [
                            tg.create_task(_execute_sync_tool_call(tc, tools_dict.get(tc.tool.name)))
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
