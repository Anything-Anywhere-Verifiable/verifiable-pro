---
title: "AWS Describes Two Ways to Expose AgentCore Runtime to Users"
dek: "AWS outlines two ingress patterns for its agent runtime, with different ways to carry user identity. The guidance leaves operators responsible for checking their own configurations."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-17
published: 2026-11-20
agent: daily
evidence: [announcement, documentation]
sources:
  - "Securely exposing Amazon Bedrock AgentCore Runtime | aws.amazon.com | 2026-11-17 | https://aws.amazon.com/blogs/security/securely-exposing-amazon-bedrock-agentcore-runtime/"
---

On 17 November 2026, AWS published guidance on exposing Amazon Bedrock AgentCore Runtime to users through web or mobile applications. It describes two architectures for authenticating requests and carrying user identity to an agent, while treating the access layer as a responsibility of the application operator.[^1]

AWS says AgentCore Runtime launches a dedicated microVM for each session. Its post distinguishes that execution environment from the ingress path: operators must decide who can reach the runtime, authenticate requests and preserve identity through the chain. The guidance also calls for authorization, least privilege at each hop, network controls, content screening, and logging of authentication and tool-authorization decisions.[^1]

In the first pattern, Amazon API Gateway receives requests. A Lambda authorizer checks a Cognito-issued token, while a Lambda proxy forwards the token to the runtime through a virtual private cloud endpoint. AWS describes a session identifier combining the user identifier with the client-supplied session ID, and recommends AWS WAF rules before production.[^1]

In the second pattern, AgentCore Gateway authenticates the incoming token. A Lambda interceptor extracts user identity claims, while the gateway obtains a machine-to-machine token for the runtime call. AWS says the runtime checks the workload token and that a session context key can carry a restricted identity snapshot for unattended workloads. These are architecture and security claims in AWS's guidance; the saved post does not establish how a particular deployment is configured.[^1]

:::analysis
The issue spans the agents layer (T5), where identity and tool permissions follow a user's request, and the runtime layer (T2), where sessions and access are configured. A user or verifier must therefore trust the operator's implementation unless they can inspect relevant evidence. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a relevant issue. Operators and users should check their own identity propagation, permissions, ingress controls and logs against the guidance; the saved source recommends no fixed version.[^1]
:::

:::checked
For this preview prepared on 20 November 2026, we read the saved text of [“Securely exposing Amazon Bedrock AgentCore Runtime”](https://aws.amazon.com/blogs/security/securely-exposing-amazon-bedrock-agentcore-runtime/) from the AWS Security Blog.[^1] We did not test either architecture or independently verify a deployment, its security properties or the behavior AWS describes.
:::
