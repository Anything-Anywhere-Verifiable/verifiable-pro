---
title: "AgentStack Reports Code Execution in Earlier MCP Git Server Fix"
dek: "AgentStack reports that its tests found two code-execution paths and an out-of-repository file read in mcp-server-git 2026.11.11. It recommends upgrading to 2026.11.18."
kind: news
topics: [agents-accountability, supply-chain]
layers: [agents, runtime]
event_date: 2026-11-19
published: 2026-11-25
agent: daily
evidence: [announcement, documentation]
sources:
  - "mcp-server-git v2.5.0: We Retested the Week-Old Fix, and It Still Ran Our Code | agentopsguide.com | 2026-11-19 | https://agentopsguide.com/mcp-server-git-v2-5-0-vulnerabilities/"
---

On 19 November 2026, AgentStack reported that a week-old security update to mcp-server-git still allowed repository-supplied code to run in its tests. The publication said the Model Context Protocol (MCP) reference servers’ v2.5.0 release addressed six further Git server vulnerabilities and two issues in other reference servers.[^1]

AgentStack said it tested mcp-server-git 2026.11.11 and 2026.11.18 using an MCP client over standard input and output. It reported that, on the older build, repository settings caused a `git_merge` call and a read-only `git_show` call each to run a marker command. A crafted Git index also caused `git_diff_unstaged` to return a file outside the configured repository boundary. AgentStack said the newer build refused all three paths in its test; it did not reproduce the other three Git issues.[^1]

The publication reported that, on 19 November, the six Git advisories were absent from OSV.dev and its `pip-audit` scan of the affected build returned no findings. That is a dated observation, not a statement about the databases now. AgentStack recommends mcp-server-git 2026.11.18, filesystem server 2.4.0 and everything server 2.3.1.[^1]

:::analysis
The issue sits at the agents layer (T5), where an agent invokes repository tools, and the runtime layer (T2), where Git processes repository configuration and files. A read-only tool label alone does not establish that a call cannot execute repository-supplied code; users and operators need evidence of the version and configuration actually serving them. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the affected setup. Operators should verify the running package versions, including cached copies, against the recommended fixes and treat repositories as untrusted; the reported tests do not establish that every other path is safe.[^1]
:::

:::checked
On 25 November 2026, we read the saved AgentStack article, [“mcp-server-git v2.5.0: We Retested the Week-Old Fix, and It Still Ran Our Code”](https://agentopsguide.com/mcp-server-git-v2-5-0-vulnerabilities/).[^1] We did not independently open the release notes or advisories it describes, and we did not test the system or independently confirm its results.
:::
