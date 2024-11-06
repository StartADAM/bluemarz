# Tool

Handling Tools requires some objects, defined below.
- ToolDefinition for tool characterization
- ToolImplementation, abstraction of tool execution (base class)
- SyncTool extends ToolImplementation, to really execute a tool in sync mode
- AsyncTool extends ToolImplementation, to really execute a tool in async mode

# ToolDefinition

## Properties (ToolDefinition)

| Attribute | Type               | Description   |
|-----------|--------------------|---------------|
| spec      | ToolSpec           | Tool spec     |
| executor  | ToolImplementation | Tool executor |


## from_spec

def from_spec(cls, spec: models.ToolSpec) -> "ToolDefinition"

Create a Tool definition from spec.

| Parameter | Type     | Description |
|-----------|----------|-------------|
| spec      | ToolSpec | Tool spec   |
|           |          |             |

**returns** ToolDefinition

# ToolImplementation

## Properties (ToolImplementation)

| Attribute | Type     | Description |
|-----------|----------|-------------|
| spec      | ToolSpec | Tool spec   |
| tool_name | string   | tool name   |


# SyncTool inherits from ToolImplementation

## Properties (SyncTool)

| Attribute | Type     | Description          |
|-----------|----------|----------------------|
| spec      | ToolSpec | Tool spec, inherited |
| tool_name | string   | tool name, inherited |

## call (sync)

def call(self, toll_call: models.ToolCall) -> models.ToolCallResult

Executes a tool call, synchronously.

| Parameter | Type     | Description          |
|-----------|----------|----------------------|
| tool_call | ToolCall | execution parameters |
|           |          |                      |

**returns** ToolCallResult.

# AsyncTool inherits from ToolImplementation


## Properties (AsyncTool)

| Attribute | Type     | Description          |
|-----------|----------|----------------------|
| spec      | ToolSpec | Tool spec, inherited |
| tool_name | string   | tool name, inherited |

## call (async)

async def call(self, toll_call: models.ToolCall) -> models.ToolCallResult

Executes a tool asynchronously.

| Parameter | Type     | Description          |
|-----------|----------|----------------------|
| tool_call | ToolCall | execution parameters |
|           |          |                      |

**returns** ToolCallResult.
