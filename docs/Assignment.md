
# Assignment

# Properties

| Attribute | Type    | Description |
|-----------|---------|-------------|
| agent     | Agent   | Agent       |
| session   | Session | Session     |
|           |         |             |

# Methods
## add_message

def add_message(self, message: SessionMessage) -> AddMessageResult

Send a message to the Agent.

| Parameter | Type           | Description             |
|-----------|----------------|-------------------------|
| message   | SessionMessage | string to send to Agent |
|           |                |                         |

**returns** AddMessageResult: bool

## add_file

def add_file(self, file: SessionFile) -> AddFileResult

Send a file to the Agent. The file content is loaded as Session context window.


| Parameter | Type        | Description           |
|-----------|-------------|-----------------------|
| file      | SessionFile | file to send to Agent |
|           |             |                       |

**returns** AddFileResult: bool

## add_tools

def add_tools(self, tools: list[ToolImplementation]) -> None:

Add tools, using a list of instances of ToolImplementation.


| Parameter | Type                      | Description   |
|-----------|---------------------------|---------------|
| tools     | list[ToolIimplementation] | list of Tools |
|           |                           |               |

**returns** none.

 ## add_tools_from_spec

def add_tools_from_spec(self, tools: list[ToolSpec]) -> None:

Add tools using a list of tool specs.


| Parameter | Type           | Description   |
|-----------|----------------|---------------|
| tools     | list[ToolSpec] | list of Tools |
|           |                |               |

**returns** none.

## run_once

async def run_once(self) -> RunResult:

Send message to Agent and get a response; eventually executing a tool in this process.
Note it´s an async method.

| Parameter | Type | Description |
|-----------|------|-------------|
| -         | -    | -           |
|           |      |             |

**returns** RunResult.

## run_until_breakpoint

async def run_until_breakpoint(self) -> AssignmentRunResult:

Run until breakpoint.

| Parameter | Type | Description |
|-----------|------|-------------|
| -         | -    | -           |
|           |      |             |

**returns** AssignmentRunResult.

