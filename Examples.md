# Examples

## Initial example

This is the same example as shown in Overview section.

<code-block lang="python" noinject="true">
    import bluemarz as bm
    import asyncio
    async def procedural_example():
        # retrieve an Agent from OpenAI
        agent = bm.openai.OpenAiAssistant.from_id(api_key, assistant_id)
        # create a Session (i.e. a thread in OpenAI terms)
        session = bm.openai.OpenAiAssistantNativeSession.new_session(api_key)
        #create an Assignment, to assign an agent to a session
        task = bm.Assignment(agent, session)
        #send a message to the agent
        msg="What can you do?"
        task.add_message(bm.SessionMessage(role=bm.MessageRole.USER, text=msg)
        # run the agent
        res = await task.run_until_breakpoint()
        # print results
        print(f"Q:{msg}")
        print(f"A:{res.last_run_result.messages[0].text}")asyncio.run(procedural_example())
</code-block>

Following the comments, you can see Bluemarz concepts being used:

* retrieval of an Agent (in this case, from OpenAI)
* creation of a Session to dialog with an Agent (again, in OpenAI)
* creation of an Assignment, the association of an Agent to a Session
* the dialog itself

## Using specs

Specs (specifications) allows you better control on how to build your Session, Agent or Assignment. For example:

<code-block lang="python" noinject="true">
    import bluemarz as bm
    async def from_spec_example():
        msg= "What can you do?"
        spec = bm.AssignmentSpec(
            agent=bm.AgentSpec(
                id=assistant_id,
                type="OpenAiAssistant",
                session_type="NativeSession",
                api_key=oai_api_key,
                prompt="Help the user in what he needs",
            ),
            query=msg,
        )
        task = bm.Assignment.from_spec(spec)
        res = await task.run_until_breakpoint()
        print(f"Q:{msg}")
        print(f"A:{res.last_run_result.messages[0].text}")
</code-block>

Specs are textual descriptions in property-list format of the characteristics of the desired element (an Assignment in this case). In this example, the following properties are being used:

* id: Agent ID in your LLM provider´s format
* type: type of Agent, in this case an OpenAI assistant
* session_type: type of session, in this case an OpenAI thread
* api_key: provider API KEY
* prompt: Agent prompt
* query: User message to Agent

When creating an Assignment this way, a Session and Agent objects are built internally. 
You can access these objects using Assignment properties.

## Tool execution

Tools (aka Actions) extend the power of LLMs by providing access to external systems. 
The call of a tool causes a break in the dialog, waiting for the User´s response. 
The image illustrates the sequence of events:

(**need to be replaced by a similar picture**)
![rework](image_2.png)

As can be seen, the LLM requests the execution of a tool, which is delegated to a Tool Executor component in Bluemarz. 
Tool execution can be synchronous or asynchronous, depending on how long it takes to run. 
Async tool calling is an important Bluemarz addition since frequently in high performance systems you don´t want to keep resources allocated in synchronous operations.

You can define a Tool from its spec:

<code-block lang="python" noinject="true">
    class Tool(bm.SyncTool):
        def __init__(self):
                self._spec = bm.ToolSpec.model_validate(
                    {
                        "id": "convert_celsius_temperature",
                        "name": "convert_celsius_temperature",
                        "description": "Converts a temperature form Celsius to Kelvin",
                        "toolType": "sync",
                        "variables": {
                            "temperature": {
                                "type": "string",
                                "description": "The temperature to convert in Celsius",
                            },
                        },
                    }
                )
    
    @property
    def spec(self):
        return self._spec
    
    def tool_name(self):
        return "convert_celsius_temperature"
    
    def call(self, tool_call: bm.ToolCall) -> bm.ToolCallResult:
        conversion = str(int(tool_call.arguments.get("temperature", "0")) + 273.15)
        return bm.ToolCallResult(
                tool_call=tool_call,
                text=conversion
            )

</code-block>

A Tool is represented by a class extending bm.SyncTool or bm.AsyncTool. 
The following methods must be implemented:

* spec: returns the spec
* tool_name: returns tool name
* call: tool call implementation which must return a ToolCallResult containing "tool call id" and "returned value"

In this example, the Tool spec includes:

* id: tool identifier, following provider´s conventions
* name: tool name
* description: tool description which will be used by LLM to decide what tool to call
* toolType: sync or async
* variables: input variables

A tool can be used following in an Agent activation as in:

<code-block lang="python" noinject="true">
    async def tool_call_procedural_example():
        msg="Please convert 32 degress celsius to kelvin using the convert_celsius_temperature tool"
        spec = bm.AssignmentSpec(
            agent=bm.AgentSpec(
                id=assistant_id,
                type="OpenAiAssistant",
                session_type="NativeSession",
                api_key= api_key,
                prompt="Help the user in what he needs",
            ),
            query=msg,
        )
        task = bm.Assignment.from_spec(spec)
        task.add_tools([Tool()])
        res = await task.run_until_breakpoint()
        print(f"Q:{msg}")
        print(f"A:{res.last_run_result.messages[0].text}")
</code-block>

It´s similar to previous example but, in this case, a tool has been added to the Assignment using the simple task.add_tools() method. Any number of tools can be added.

## Tool execution with specs

Instead of adding tools programatically as the above example, you can also add tool via spec. Check the following example:

<code-block lang="python" noinject="true">
    async def tool_call_executor_example():
        msg = "Please convert 32 degress celsius to kelvin using the convert_celsius_temperature tool"
        spec = bm.AssignmentSpec.model_validate(
            {
                "agent": {
                    "id": assistant_id,
                    "type": "OpenAiAssistant",
                    "session_type": "NativeSession",
                    "api_key": oai_api_key,
                    "prompt": "Help the user in what he needs",
                },
                "additional_tools": [
                    {
                        "id": "convert_celsius_temperature",
                        "name": "convert_celsius_temperature",
                        "description": "Converts a temperature form Celsius to Kelvin",
                        "toolType": "sync",
                        "variables": {
                            "temperature": {
                                "type": "string",
                                "description": "The temperature to convert in Celsius",
                            },
                        },
                    }
                ],
                "query": msg,
            }
        )
        task = bm.Assignment.from_spec(spec)
        res = await task.run_until_breakpoint()
        print(f"Q:{msg}")
        print(f"A:{res.last_run_result.messages[0].text}")
</code-block>

This example is similar to the previous one but includes the tool definition as a spec, using the same attributes as the previous class example. This textual form allows alternatives, like using a ToolRepository, explained later.

In this case, a ToolExecutor must be injected to allow the tool to be really executed. Note we´re exchanging the procedural flow (using task.add_tools() as previous example) by code injection (using annotation @bm.sync_tool_executor).

<code-block lang="python" noinject="true">
    @bm.sync_tool_executor
    class KelvinCelsiusTool(bm.SyncToolExecutor):
        @classmethod
        def tool_name(cls):
             return "convert_celsius_temperature"
    @classmethod
    def execute_call(cls, tool_call: bm.ToolCall) -> bm.ToolCallResult:
            conversion = str(int(tool_call.arguments.get("temperature", "0")) + 273.15)
    
            return bm.ToolCallResult(
                tool_call=tool_call,
                text=conversion
            )

</code-block>

## Adding files

example to be added

## Using 2 Agents in a Session (sequencial agentic flow)

example to be added


