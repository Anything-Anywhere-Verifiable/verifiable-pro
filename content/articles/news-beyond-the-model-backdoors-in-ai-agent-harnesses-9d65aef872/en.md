---
title: "CERT-EU Reports Agent Extension Backdoors Acting Outside Model Tool Calls"
dek: "In isolated lab tests, modified extensions transmitted host information while agents continued normal conversations. CERT-EU recommends controls over the entire execution environment."
kind: news
topics: [supply-chain, agents-accountability]
layers: [agents, runtime]
event_date: 2026-10-30
published: 2026-11-10
agent: daily
evidence: [announcement, documentation]
sources:
  - "Beyond the model: backdoors in AI agent harnesses | cert.europa.eu | 2026-10-30 | https://cert.europa.eu/blog/beyond-the-model-backdoors-in-ai-agent-harnesses"
---

CERT-EU reported on 30 October 2026 that backdoors inserted into local copies of legitimate AI agent extensions transmitted host information without model-generated tool calls. Its isolated laboratory experiment used Pi 1.3.0 and Claude Code 2.1.304 with test credentials. No public package releases were modified or distributed, the agency said.[^1]

The payloads occupied existing event-handling paths: an additional `before_agent_start` handler in Pi and code reached through a `UserPromptSubmit` hook in Claude Code. According to CERT-EU, ordinary prompts left the payloads dormant; input containing the phrase “lgtm, ship it” activated collection when the collection endpoint was configured. Both agents continued their conversations without a visible malicious tool call. The collector received one request from each modified package, containing information including environment variables and credential-related files.[^1]

In the tested configurations, restrictions on model file-reading tools did not cover files accessed directly by extension handlers. Controls inspecting model-generated tool calls did not intercept these operations. CERT-EU recommends restricted execution environments, narrowly scoped temporary credentials, outbound network controls, extension inventories and version pinning, plus monitoring beyond tool calls. The post does not announce a fixed version or identify these tested harness versions as universally vulnerable.[^1]

:::analysis
The issue sits at T5 (agents), where extensions handle workflow events, and T2 (runtime), where their inherited permissions allow direct file and network access; a normal conversation or clean tool-call log therefore cannot establish what the whole environment did. Users and operators should verify installed extension versions and provenance, review changes, and check actual filesystem, credential and network access against CERT-EU’s recommendations. The verifiable property at stake is identifiability: if the exact versions and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the relevant configuration; establishing actual collection still requires execution evidence. The source supplies no fixed release to verify against.[^1]
:::

:::checked
On 10 November 2026, we read the saved text of CERT-EU’s “Beyond the model: backdoors in AI agent harnesses,” published on 30 October 2026. This reading establishes what CERT-EU reported, including its experimental scope and recommendations. We did not test the system, inspect the modified packages or independently verify the collector records.[^1]
:::

[^1]: CERT-EU, “Beyond the model: backdoors in AI agent harnesses,” 30 October 2026. https://cert.europa.eu/blog/beyond-the-model-backdoors-in-ai-agent-harnesses
