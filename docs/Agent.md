# Agent

# Properties

| Attribute | Type                   | Description   |
|-----------|------------------------|---------------|
| spec      | AgentSpec              | Agent spec    |
| tools     | list of ToolDefinition | list of tools |

# Methods

## from_spec

def from_spec(cls, spec: models.AgentSpec) -> "Agent"

Create a Session from spec.

| Parameter | Type      | Description |
|-----------|-----------|-------------|
| spec      | AgentSpec | Agent spec  |
|           |           |             |

**returns** Agent

## add_tools

def add_tools(self, tools: list[ToolImplementation]) -> Self:

Add tools to Agent.


| Parameter | Type                       | Description               |
|-----------|----------------------------|---------------------------|
| tools     | list of ToolImplementation | list of tools to be added |
|           |                            |                           |

**returns** none.

## add_tools_from_spec

def add_tools_from_spec(self, tools: list[models.ToolSpec]) -> Self:

Add tools to Agent.


| Parameter | Type             | Description               |
|-----------|------------------|---------------------------|
| tools     | list of ToolSpec | list of tools to be added |
|           |                  |                           |

**returns** none.




