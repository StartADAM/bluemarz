# Bluemarz

![Bluemarz logo](bluemarz.png "Bluemarz logo")

## What is Bluemarz?

Bluemarz is an open-source management layer for AI agents, offering a flexible, scalable, and stateless architecture for deploying and orchestrating AI agents.
It supports multiple LLMs, including OpenAI, Claude, and Gemini, and is designed to meet enterprise needs such as security, privacy, access controls, and multi-agent collaboration.

It runs on Python 3.12+

## Code primer

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
    task.add_message(bm.SessionMessage(role=bm.MessageRole.USER, text="What can you do?"))
    # run the agent
    res = await task.run_until_breakpoint()
    # print results
    print(res)
asyncio.run(procedural_example())
</code-block>

## Why Bluemarz?

Bluemarz addresses key shortcomings found in other platforms like Langchain, Langraph, Chainlit and OpenAI by focusing on multi-agent deployments, session management, and scalability. 
Below is a quick comparison to highlight the advantages Bluemarz brings over these alternatives.

| Feature                                | LangChain | LangGraph | OpenAI SDK | Chainlit | Bluemarz |
|----------------------------------------|-----------|-----------|------------|----------|----------|
| Stateless architecture                 | no        | no        | no         | no       | yes      |
| Multi-LLM support                      | yes       | yes       | yes        | no       | yes      |
| Agent selection via AI                 | no        | no        | no         | no       | yes      |
| Agent selection programmatically       | no        | no        | no         | no       | yes      |
| Multi-agent in a single session        | yes       | yes       | no         | no       | yes      |
| Reusable tools/actions across agents   | no        | no        | no         | no       | yes      |
| Async execution for better performance | no        | no        | no         | no       | yes      |


## What makes Bluemarz different

- **Stateless**: Bluemarz is designed to be stateless, meaning it can run 
in your Kubernetes cluster or any other platform without 
retaining session state, ensuring flexibility and scalability.

- **Multi-Agent & Multi-LLM**: Out of the box, Bluemarz supports 
multiple LLMs such as OpenAI, Claude, and Gemini, and enables multi-agent 
sessions, where agents can be dynamically added or removed even within a single session.

- **Enterprise-Ready**: Bluemarz works in your existing security, 
privacy, and access controls, making it a corporate-ready tool.

- **Flexible Agent Selection**: With Bluemarz, you can either 
programmatically decide which agent to invoke at which time or use 
the AI-powered Selector agent to automate agent selection (coming soon).

## Conceptual elements

### Provider 

Providers are your LLMs, such as OpenAI,
Google Gemini, Anthropic Claude, AWS Bedrock or self-hosted LLMs.

LLM Providers provide the dialog within a Bluemarz Session.

### Session

A Session in Bluemarz represents a dialogue or interaction.

- **Statelessness**: Bluemarz sessions are stateless, relying entirely 
on your LLM provider, which run and store your sessions.

- **Dialogues Across Platforms**: You can run Bluemarz sessions on 
your provider of choice, wherever dialogues occur.

### Agent

With Bluemarz, Agents can now be defined independently of sessions, and you can assign them dynamically at any time.

- **Dynamic Agent Assignment**: Agents can be added or removed from a session dynamically.
This way, any information flow between agents can be implemented as they´ll have access to all information
in a Session.

- **Selector Agent**: Bluemarz offers an AI-powered Selector agent, but you can also manually select agents programmatically (coming soon). 

### Assignment

Assignment in Bluemarz refers to the process of assigning agents to a session. 
Multiple agents can participate in a single session, and they can come from different LLMs. 
Bluemarz allows dynamic assignment, enabling the addition or removal of agents without predefined setups.

- **Multiple Agents Per Session**: Unlike some platforms (e.g., OpenAI Playground), Bluemarz supports multiple agents interacting in the same session.

- **Flexible Assignment**: Agents can be assigned at the start of or during a session, allowing real-time changes based on the session’s needs.


### Tool Execution

Bluemarz allows you to define tools once and reuse them across agents and providers. 
This centralization simplifies tool execution. Bluemarz executes tool calls, handling the complex HTTP request/reply flow,
collecting all tool responses before sending them to the LLM to continue generating a reply.  

- **Reusable Tools**: Tools can be defined centrally and used across any agent. 
For example, a tool that retrieves ERP data can be used by multiple agents without needing reconfiguration.

- **Centralized Control**: This allows for easier management of tools, ensuring they are 
secure and scalable across multiple agents and sessions.

### Retrieval-Augmented Generation (RAG) Support

Bluemarz provides RAG (Retrieval-Augmented Generation) support, which allows agents to 
access reference materials during task execution. 
RAG is supported at both the agent and assignment levels, giving flexibility for knowledge retrieval.

**RAG at the Agent Level**

Agents can retrieve reference files (e.g., documents, knowledge bases) as they execute tasks. 
For example, an agent can look up product manuals or knowledge databases during customer support sessions.

**RAG at the Assignment Level**

RAG can also be implemented at the session level, where the session provides context-specific 
reference files to all participating agents. Bluemarz doesn´t store any data; file content are stored in the provider.

## Additional considerations

- **Cost Control**: Bluemarz can help manage costs by allowing you to restrict agent usage on an as-needed basis, ensuring that only necessary agents are deployed in specific sessions.

## Conclusion

Bluemarz offers a stateless, flexible, and multi-agent platform that supports corporate needs for scalability, security, and flexibility. 
Whether you want to configure a multi-agent session, assign agents dynamically, or reuse tools across agents, Bluemarz provides the open source infrastructure to manage AI agents efficiently.


 
