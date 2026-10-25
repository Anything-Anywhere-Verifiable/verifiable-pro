---
title: KNOX Preprint Proposes a TEE-Based Regulatory Sandbox for AI Agents
dek: On 20 October 2026 researchers from the Vector Institute and the University of Waterloo described KNOX, which checks each action of an AI agent against a policy drawn up for its prompt. They say regulators can check a run's record offline against one hardware attestation, without the model weights.
kind: news
topics: [agents-accountability, confidential-computing, evaluation-audits]
layers: [evaluations, agents, runtime]
event_date: 2026-10-20
published: 2026-10-25
agent: daily
evidence: [paper]
related: [nist-nsa-cisa-agent-incident-practices, singapore-agentic-testing-kit-accreditation, ddrop-ddr5-interposer-attack]
sources:
  - KNOX: Hardware-assisted Regulatory Sandbox for Generative Models | arXiv (Vasisht Duddu, Adam Caulfield and Xi He) | 2026-10-20 | https://arxiv.org/abs/2610.27543
---

On 20 October 2026 three researchers from the Vector Institute and the University of Waterloo posted a preprint describing KNOX, a regulatory sandbox where regulators can monitor generative models before deployment. The authors argue that a trusted execution environment (TEE), a hardware-isolated environment for running code, does not enforce compliance by itself.[^1]

For each prompt, a planner model writes a policy manifest of expected tool calls, applicable rules and permitted system calls (requests to the operating system). A reference monitor checks each action against the manifest, blocking mismatches. A judge model rules on data disclosures under the EU's General Data Protection Regulation and the US Health Insurance Portability and Accountability Act. Actions and verdicts enter an execution graph chained by hashes (digital fingerprints), signed inside the TEE and tied to one quote, Intel's hardware-signed attestation report. The authors say regulators can check the record offline, matching weight hashes to the claimed models, without the weights.[^1]

The prototype uses an Intel Trust Domain Extensions (TDX) confidential virtual machine, an NVIDIA H100 graphics processing unit (GPU) in confidential-computing mode and open-weight models: Qwen3.5-9B as planner and judge, and Llama-3.1-8B, Gemma-3-12B and Ministral-3-14B as executors. In tests built on the InjecAgent benchmark with simulated tools, the authors report, the monitor blocked 81.8% to 100% of rule-breaking disclosures across executors and allowed 90% to 96% of compliant ones. It also blocked every off-plan tool call prompted by instructions planted in tool outputs. In 100 unauthorized system-call cases, the monitor alone stopped 74% and Linux kernel restrictions (seccomp-BPF and Landlock) the rest. By the authors' measure, excluding the judge model's computation and TEE overhead, the checks and attestations added under 1% to inference time.[^1]

The threat model excludes physical attacks; the authors say side channels, leaks through effects such as timing, remain a concern. The judge's accuracy rests on tests, and the quote does not directly cover per-prompt kernel restrictions.[^1]

:::analysis
KNOX would let regulators check offline which models and policy governed a run and whether recorded steps were dropped or altered. The quote records the software loaded at launch, but regulators must still trust the monitor's enforcement and the judge's rulings. A model writes the manifest that defines a deviation. The paper reports no use by a regulator.
:::

:::checked
On 25 October 2026 we read the KNOX preprint's arXiv record and full text. We did not run KNOX, whose code the paper says is due on publication, so the figures are the authors' own. The paper neither defines its 100 system-call cases nor says how many the monitor could inspect, and its text and tables count cases differently, so we give no other totals.
:::
