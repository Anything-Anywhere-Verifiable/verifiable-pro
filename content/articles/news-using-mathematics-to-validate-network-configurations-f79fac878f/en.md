---
title: "Amazon Describes Mathematical Checks for Cloud WAN Segmentation"
dek: "Amazon says its Tiros automated-reasoning tool can check modeled network paths against isolation policies without sampling packets. The result depends on the configuration and policy represented in the model."
kind: news
topics: [formal-verification]
layers: [runtime]
event_date: 2026-11-11
published: 2026-11-19
agent: daily
evidence: [announcement, documentation]
sources:
  - "Using mathematics to validate network configurations | www.amazon.science | 2026-11-11 | https://www.amazon.science/blog/using-mathematics-to-validate-network-configurations"
---

On 11 November 2026, Amazon Science described how Amazon Web Services (AWS) uses its Tiros automated-reasoning tool to check network segmentation in AWS Cloud WAN. Amazon says the approach analyzes a deployed network’s topology as often as every hour and checks modeled paths against isolation specifications without sampling live packet traffic.[^1]

Segmentation uses routing policies and logical rules to keep network resources apart. Amazon says its process collects Cloud WAN route tables, attachments and policy documents, then converts the configuration into logical propositions. Tiros derives paths between attachments for destination IP addresses; the system compares those paths with the expected segmentation and alerts an operator when they differ.[^1]

In Amazon’s example, a company separates production and development environments across regions. The company expresses that separation as a policy, and the model is queried for paths between the two segments. Amazon says that finding no such path in the model indicates that the core network’s segmentation aligns with the stated policy. This is a claim about the modeled configuration and policy, rather than an independent observation of every packet or a demonstration that the policy captures every intended restriction.[^1]

:::analysis
The issue sits at T2, the runtime layer: a verifier assessing network isolation must be able to trust or check the configuration supplied to the model, its translation into logic and the policy used for comparison. Users and operators should check that their own route tables, attachments and policies match the system and separation they intend to assess, and examine any alert against those inputs. The relevant property is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a configuration at issue. Amazon’s article does not establish that such per-user records are available or recommend a fixed version.[^1]
:::

:::checked
On 19 November 2026, we read the saved text of Amazon Science’s [“Using mathematics to validate network configurations”](https://www.amazon.science/blog/using-mathematics-to-validate-network-configurations), published on 11 November 2026.[^1] It describes Amazon’s method and claims; we did not test Tiros or independently verify its results, deployment or coverage.
:::
