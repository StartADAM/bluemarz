# Bluemarz
   
<img src="bluemarz.png" width="325" class="center" />

## What is Bluemarz?

Bluemarz is an open-source management layer for AI agents, offering a flexible, scalable, and stateless architecture for deploying and orchestrating multiple AI agents in sessions.

It supports multiple LLMs, including OpenAI, Claude, and Gemini, and is designed to meet enterprise needs such as security, privacy, access controls, and multi-agent collaboration.

It runs on Python 3.12+

## Community

<img src="discord.png" width="125" class="center" />

Connect with our community! -> https://discord.gg/Q6UtmJNY
See our [Code Of Conduct](./docs/CodeOfConduct.md).

## Code primer

Install with
pip install git+https://github.com/StartADAM/bluemarz.git

The following code uses the 3 main concepts in Bluemarz:

- Agent, provided by any supported LLM;
- Session, where the dialog User-Agent happens;
- Assignment of an Agent to a Session to be used in a dialog.

```python
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
    await task.add_message(bm.SessionMessage(role=bm.MessageRole.USER, text="What can you do?"))
    # run the agent
    res = await task.run_until_breakpoint()
    # print results
    print(res)
asyncio.run(procedural_example())
```

If you´re looking for more examples, check [Examples](./docs/Examples.md).

## Why Bluemarz?

Bluemarz addresses key shortcomings found in other platforms like Langchain, Langraph, Chainlit and OpenAI by focusing on multi-agent deployments, session management, and scalability.
Below is a quick comparison to highlight the advantages Bluemarz brings over these alternatives.

| Feature                                | LangChain | LangGraph | OpenAI SDK | Chainlit | Bluemarz |
| -------------------------------------- | --------- | --------- | ---------- | -------- | -------- |
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


# Use Cases

## Use Case 1: Multi-Agent Customer Support System

**Scenario:**

Your company receives a high volume of customer inquiries ranging from billing issues to technical support and general product information. Managing these efficiently requires specialized handling.

**Implementation with Bluemarz:**

- **Agent Specialization:** Create multiple AI agents, each trained and specialized in a specific domain:

  - **Billing Agent:** Handles payment queries, invoice requests, and account updates.
  - **Technical Support Agent:** Assists with troubleshooting, setup guides, and technical FAQs.
  - **Product Information Agent:** Provides details on product features, availability, and comparisons.

- **Dynamic Agent Assignment:** Using Bluemarz's flexible agent selection, route customer inquiries to the appropriate agent based on the content of their message. For example, keywords like "error," "not working," or "install" trigger the Technical Support Agent.

- **Session Management:** Bluemarz's stateless architecture allows each customer interaction to be managed efficiently without retaining session states, ensuring scalability during peak times.

- **Tool Integration:** Implement tools for order tracking, appointment scheduling, or account verification that agents can access during the session.

**Benefits:**

- **Improved Response Times:** Customers receive faster, more accurate responses tailored to their needs.
- **Resource Optimization:** Human support staff can focus on complex issues that require personal attention.
- **Scalability:** Easily handle increased inquiry volumes without degradation in service quality.

---

## Use Case 2: Internal Knowledge Base Access for Employees

**Scenario:**

Employees frequently need access to company policies, procedures, technical documentation, or HR information. Manually searching through databases or documents is time-consuming.

**Implementation with Bluemarz:**

- **Centralized Agent Access:** Deploy an AI agent that can access a broad range of internal documents and resources.

- **Retrieval-Augmented Generation (RAG):** Utilize Bluemarz's RAG support to enable the agent to fetch and reference specific documents or sections in real-time during interactions.

- **Multi-Agent Collaboration:** Assign specialized agents for different departments:

  - **HR Agent:** Answers questions about leave policies, benefits, and onboarding.
  - **IT Support Agent:** Provides help with software installations, password resets, and troubleshooting.
  - **Compliance Agent:** Advises on legal guidelines, compliance training, and regulatory requirements.

- **Secure Sessions:** Bluemarz integrates with your existing security protocols to ensure sensitive information remains confidential.

**Benefits:**

- **Increased Productivity:** Employees get immediate answers, reducing downtime and dependency on support staff.
- **Knowledge Retention:** Consistent and up-to-date information is provided across the organization.
- **Cost Efficiency:** Reduces the burden on internal support teams, allowing them to focus on strategic initiatives.

---

## Use Case 3: Automated Workflow and Task Management

**Scenario:**

Your team handles repetitive tasks like processing expense reports, scheduling meetings, or updating project statuses. Automating these can save time and reduce errors.

**Implementation with Bluemarz:**

- **Workflow Automation Agents:**

  - **Data Collection Agent:** Gathers necessary information from users or systems.
  - **Validation Agent:** Checks data accuracy, compliance, and completeness.
  - **Notification Agent:** Sends updates, reminders, or confirmations to stakeholders.

- **Async Execution:** Bluemarz's asynchronous capabilities allow multiple tasks to be processed concurrently, improving efficiency.

- **Tool Reusability:** Define tools (e.g., database queries, API calls, form submissions) that can be reused by different agents across various workflows.

- **Dynamic Assignment:** Agents can be added or removed from sessions as needed, enabling flexibility in managing complex workflows.

**Benefits:**

- **Efficiency Gains:** Automates routine tasks, freeing up team members for higher-value work.
- **Error Reduction:** Standardizes processes, minimizing the risk of human error.
- **Scalability:** Easily adjust workflows to accommodate changes in team size or project scope without overhauling the entire system.

---

By integrating Bluemarz into these scenarios, you leverage its strengths in multi-agent orchestration, stateless session management, and tool execution to enhance productivity and efficiency in your daily operations.

## Additional Considerations

- **Cost Control:** Bluemarz can help manage costs by allowing you to restrict agent usage on an as-needed basis, ensuring that only necessary agents are deployed in specific sessions.


## Conclusion

Bluemarz offers a stateless, flexible, and multi-agent platform that supports corporate needs for scalability, security, and flexibility.
Whether you want to configure a multi-agent session, assign agents dynamically, or reuse tools across agents, Bluemarz provides the open source infrastructure to manage AI agents efficiently.
