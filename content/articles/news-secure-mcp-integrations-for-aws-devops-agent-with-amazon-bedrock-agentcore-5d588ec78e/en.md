---
title: "AWS Describes MCP Security Controls for DevOps Agent"
dek: "AWS describes direct and gateway connections for agent tools, including an approval control that depends on how operators classify each tool."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-17
published: 2026-11-22
agent: daily
evidence: [announcement, documentation]
sources:
  - "Secure MCP integrations for AWS DevOps Agent with Amazon Bedrock AgentCore | aws.amazon.com | 2026-11-17 | https://aws.amazon.com/blogs/devops/secure-mcp-integrations-for-aws-devops-agent-with-amazon-bedrock-agentcore/"
---

On 17 November 2026, AWS published guidance for connecting Model Context Protocol (MCP) tools to AWS DevOps Agent, its incident investigation agent. The post describes direct connections to MCP servers and a shared connection through Amazon Bedrock AgentCore Gateway, which AWS says can centralize authentication, policy and observability. MCP gives the agent a way to call external tools and data sources during an investigation.[^1]

For a direct connection, an administrator registers a server and selects tools for each agent space. AWS says each tool should be classified as read-only, mutating or destructive: read-only tools run without operator approval; mutating calls require directed actions to be enabled and an operator's approval in chat; and tools classified as destructive are not invoked. AWS warns that API or command-line registrations default unclassified tools to read-only, so operators must classify tools that can change state.[^1]

With Gateway, the agent registers one endpoint while backend servers are configured as targets. AWS says the gateway manages target credentials centrally and can apply Cedar policies across tools. It also describes logs of tool calls and traces across components. The post recommends limiting each agent space to needed tools and preferring read-only access to reduce prompt-injection exposure.[^1]

:::analysis
The controls sit at T5, agents, and T2, runtime: tool selection and classification shape what the agent may request, while gateway policy and logging concern how those requests are handled and recorded. Users and operators should check their own tool allowlists, classifications, credentials and gateway policies; the post alone cannot establish that any particular deployment enforces them. Identifiability is also at stake: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular issue. The post does not identify an affected or fixed version, nor establish that such records are available for a given deployment.[^1]
:::

:::checked
On 22 November 2026, we read the saved AWS DevOps & Developer Productivity Blog post, “Secure MCP integrations for AWS DevOps Agent with Amazon Bedrock AgentCore.” It is AWS guidance and describes AWS's claims; we did not test the system or independently confirm the controls in a deployment.[^1]
:::
