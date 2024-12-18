# Examples

## Basic example

This is the same example as shown in the Overview section.

```
    import bluemarz as bm
    import asyncio
    
    async def procedural_example():
        # retrieve an Agent from OpenAI
        agent = await bm.openai.OpenAiAssistant.from_id(api_key, assistant_id)
        # create a Session (i.e. a thread in OpenAI terms)
        session = await bm.openai.OpenAiAssistantNativeSession.new_session(api_key)
        #create an Assignment, to assign an agent to a session
        task = bm.Assignment(agent, session)
        #send a message to the agent
        msg="What can you do?"
        await task.add_message(bm.SessionMessage(role=bm.MessageRole.USER, text=msg))
        # run the agent
        res = await task.run_until_breakpoint()
        # print results
        print(f"Q:{msg}")
        print(f"A:{res.last_run_result.messages[0].text}")
    
    asyncio.run(procedural_example())
```

Following the comments, you can see Bluemarz concepts being used:

* retrieval of an Agent (in this case, from OpenAI)
* creation of a Session to initiate a conversation with an Agent (again, in OpenAI)
* creating an Assignment, to associate an Agent with a Session
* the dialog itself

## Using specs

Specs (specifications) gives you enhanced control over building your Session, Agent or Assignment. For example:

```
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
        task = await bm.Assignment.from_spec(spec)
        res = await task.run_until_breakpoint()
        print(f"Q:{msg}")
        print(f"A:{res.last_run_result.messages[0].text}")
```

Specs are textual descriptions in property-list format of the characteristics of the desired element (an Assignment in this case). In this example, the following properties are being used:

* id: Agent ID in your LLM provider´s format
* type: type of Agent, in this case an OpenAI assistant
* session_type: type of session, in this case an OpenAI thread
* api_key: provider API KEY
* prompt: Agent prompt
* query: User message to the Agent

When creating an Assignment this way, a Session and Agent objects are built internally by Bluemarz. 
You can access these objects using the Assignment properties.

## Tool execution

Tools (aka Actions) extend the power of LLMs by providing access to external systems. 
The call of a tool causes a break in the dialog, and waits for the User´s response. 
The image illustrates the sequence of events:

(**Image is a Work in Progress**)
![rework](image_2.png)

As can be seen, the LLM requests the execution of a tool, which is delegated to a Tool Executor component in Bluemarz. 
Tool execution can be synchronous or asynchronous, depending on how long it takes to run. 
Async tool calling is an important Bluemarz addition since frequently in high performance systems you don´t want to keep resources allocated in synchronous operations.

You can define a Tool from its spec:

```
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

```

A Tool is represented by a class extending bm.SyncTool or bm.AsyncTool. 
The following methods must be implemented:

* spec: returns the spec
* tool_name: returns tool name
* call: tool call implementation which must return a ToolCallResult containing "tool call id" and "returned value"

In this example, the Tool spec includes:

* id: tool identifier, following provider´s conventions
* name: tool name
* description: tool description which will be used by the LLM to decide what tool to call
* toolType: sync or async
* variables: input variables

For example, a tool can be called following an Agent activation:

```
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
        task = await bm.Assignment.from_spec(spec)
        task.add_tools([Tool()])
        res = await task.run_until_breakpoint()
        print(f"Q:{msg}")
        print(f"A:{res.last_run_result.messages[0].text}")
```

It´s similar to the previous example but, in this case, a tool has been added to the Assignment using the simple task.add_tools() method. Any number of tools can be added.

## Tool execution with specs

Instead of adding tools programatically as with the above example, you can also add tools via spec. Refer to the following example:

```
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
        task = await bm.Assignment.from_spec(spec)
        res = await task.run_until_breakpoint()
        print(f"Q:{msg}")
        print(f"A:{res.last_run_result.messages[0].text}")
```

This example is similar to the previous one but includes the tool definition as a spec, using the same attributes as the previous class example. This textual form allows alternatives, like using a ToolRepository, explained later.

In this case, a ToolExecutor must be injected to allow the tool to be really executed. Note we´re exchanging the procedural flow (using task.add_tools() as with the previous example, by code injection (using annotation @bm.sync_tool_executor).

```
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

```

## Adding files

In this example, a file is added to the context window, expanding the LLM´s knowledge.

```
async def file_usage_example():
    msg = "What´s Bluemarz?"
    agent = await bm.openai.OpenAiAssistant.from_id(oai_api_key, assistant_id)
    session = await bm.openai.OpenAiAssistantNativeSession.new_session(oai_api_key)
    task = bm.Assignment(agent, session)
    a_file = bm.SessionFile(url="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf", file_name="dummy.pdf")
    await session.add_file(a_file)
    await task.add_message(bm.SessionMessage(role=bm.MessageRole.USER, text=msg))
    res = await task.run_until_breakpoint()
    print(f"Q:{msg}")
    print(f"A:{res.last_run_result.messages[0].text}")
```

It´s the same basic example with the addition of a file. To add a file to a Session you need to:
- create a SessionFile, specifying a URL from where to retrieve the file and a file_name to be used. Local files cannot be added in the current version.
- add the file to the Session by calling session.add_file() method.


## Using 2 Agents in a Session (sequencial agentic flow)

In this example, 2 Agents are used in sequence, within the same Session.
The example follows the same structure as the Basic Example.

```
async def many_agents_example():
    msg1 = "What´s Bluemarz?"
    agent1 = await bm.openai.OpenAiAssistant.from_id(oai_api_key, assistant_id)
    session = await bm.openai.OpenAiAssistantNativeSession.new_session(oai_api_key)
    task = bm.Assignment(agent1, session)
    await task.add_message(bm.SessionMessage(role=bm.MessageRole.USER, text=msg1))
    res = await task.run_until_breakpoint()
    print(f"Q:{msg1}")
    print(f"A:{res.last_run_result.messages[0].text}")

    msg2 = "What was the first question?"
    agent2 = await bm.openai.OpenAiAssistant.from_id(oai_api_key, second_assistant_id)
    task = bm.Assignment(agent2, session)
    await task.add_message(bm.SessionMessage(role=bm.MessageRole.USER, text=msg2))
    res = await task.run_until_breakpoint()
    print(f"Q:{msg2}")
    print(f"A:{res.last_run_result.messages[0].text}")
```

The same basic example is initially used. Then, a new Agent (agent2) is retrieved and added to the Session. Next, messages (task.add_message()) are sent to the Agent.

