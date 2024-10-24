from typing import TypeVar
from bluemarz.core.interfaces import (
    Agent,
    AssignmentExecutor,
    Session,
    SyncToolExecutor,
)
from bluemarz.core.exceptions import InvalidDefinition

_executors: dict[tuple[type[Agent], type[Session]], type[AssignmentExecutor]] = {}
_agents: dict[str, type[Agent]] = {}
_sessions: dict[str, type[Session]] = {}
_sync_tool_executors: dict[str, type[SyncToolExecutor]] = {}

__STE = TypeVar("__STE", bound=Session)


def sync_tool_executor(tool_executor: type[__STE]) -> type[__STE]:
    if not issubclass(tool_executor, SyncToolExecutor):
        raise TypeError("Decorator only usable with ToolExecutor class implementations")

    _sync_tool_executors[tool_executor.tool_name()] = tool_executor
    return tool_executor


def get_sync_tool_executor(tool_name: str) -> type[SyncToolExecutor]:
    try:
        return _sync_tool_executors[tool_name]
    except KeyError:
        raise InvalidDefinition(f"Unknown tool {tool_name}")


def has_sync_tool_executor(tool_name: str) -> type[SyncToolExecutor]:
    return tool_name in _sync_tool_executors


__S = TypeVar("__S", bound=Session)


def ai_session(session: type[__S]) -> type[__S]:
    if not issubclass(session, Session):
        raise TypeError("Decorator only usable with Session class implementations")

    _sessions[session.__name__] = session
    return session


def get_session_class(session_type: str) -> type[Session]:
    try:
        return _sessions[session_type]
    except KeyError:
        raise InvalidDefinition(f"Unknown session {session_type}")


__A = TypeVar("__A", bound=Agent)


def ai_agent(agent: type[__A]) -> type[__A]:
    if not issubclass(agent, Agent):
        raise TypeError("Decorator only usable with Agent class implementations")

    _agents[agent.__name__] = agent
    return agent


def get_agent_class(agent_type: str) -> type[Agent]:
    try:
        return _agents[agent_type]
    except KeyError:
        raise InvalidDefinition(f"Unknown agent {agent_type}")


__AE = TypeVar("__A", bound=AssignmentExecutor)


def assignment_executor(executor: type[__AE]) -> type[__AE]:
    if not issubclass(executor, AssignmentExecutor):
        raise TypeError("Decorator only usable with Executor class implementations")

    try:
        args = executor.execute.__annotations__
        key = f"{args["agent"].__name__}-{args["session"].__name__}"
    except Exception:
        raise InvalidDefinition(
            "Invalid Executor definition. There might be missing arguments or type hints in the 'execute' method"
        )

    if _executors.get(key, None):
        raise InvalidDefinition(
            f"Executor already defined for {args["agent"].__name__} and {args["session"].__name__}"
        )

    _executors[key] = executor

    return executor


def get_executor(agent: Agent, session: Session) -> type[AssignmentExecutor]:
    try:
        return _executors[f"{agent.__class__.__name__}-{session.__class__.__name__}"]
    except KeyError:
        raise InvalidDefinition(
            f"No executor defined for {agent.__class__.__name__} and {session.__class__.__name__}"
        )