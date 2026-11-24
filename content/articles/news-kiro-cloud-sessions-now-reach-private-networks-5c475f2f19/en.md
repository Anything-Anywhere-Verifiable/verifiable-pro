---
title: "Kiro Says Cloud Sessions Can Now Reach Private Networks"
dek: "Kiro says administrators can connect new cloud sessions to a virtual private cloud, while model and other Kiro traffic remains on Kiro’s network."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-20
published: 2026-11-24
agent: daily
evidence: [announcement, documentation]
sources:
  - "Kiro cloud sessions now reach private networks | kiro.dev | 2026-11-20 | https://kiro.dev/blog/private-networks/"
---

Kiro announced on 20 November 2026 that its cloud sessions can connect to an administrator-configured virtual private cloud (VPC). The company says new sessions then join the default connection automatically, allowing agents to reach resources that the VPC can route to, subject to the customer’s network controls. The feature is available on Enterprise plans for IAM Identity Center profiles.[^1]

According to Kiro, a connected session can reach private package registries, internal services and databases, as well as on-premises systems reachable through the VPC. When a session starts, Kiro says it attaches a network interface in the VPC and makes it the default route. Administrators choose the VPC, subnets and security groups; they can register multiple connections, but each session attaches to one VPC.[^1]

Kiro says traffic to its model, control plane and telemetry stays on Kiro’s network. The agent sends prompts and gathered context, such as file contents and command output, to the model over that path. Other traffic leaves through the customer’s VPC, where the customer’s network controls apply.[^1]

The connection is fixed when a session starts, so a later default change applies to new sessions. Kiro says a session’s page shows its actual connection, which may differ from the current default. To see connection information in session info, Kiro recommends IDE 1.4.236 or later, or CLI 3.5.0 or later.[^1]

:::analysis
This change sits at the agents layer (T5) and runtime layer (T2): the agent can reach different resources depending on the network attached to its session. Identifiability is the property at stake: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the configuration in question. Operators should check their own session’s actual connection, routes and security groups, and users should check that their IDE or CLI meets Kiro’s recommended version for displaying connection information. The announcement alone does not establish those settings for any particular session, so readers must trust Kiro’s account of the feature and check their own environment.[^1]
:::

:::checked
On 24 November 2026 we read the saved copy of Kiro’s official announcement, [“Kiro cloud sessions now reach private networks”](https://kiro.dev/blog/private-networks/).[^1] We did not test the system or independently verify its routing, controls or session information.
:::
