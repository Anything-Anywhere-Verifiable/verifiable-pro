---
title: "SEAL Authors Report Lower Prompt Injection Success With Local Tool-Output Sanitization"
dek: "An arXiv abstract describes a defense that deletes selected tool-output text using a frozen task model. Its benchmark figures are author-reported; we read the saved abstract page and did not test the system."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents]
event_date: 2026-10-29
published: 2026-10-30
agent: daily
evidence: [announcement, documentation]
sources:
  - "SEAL: Sealed Queries for Local Sanitization against Indirect Prompt Injection | arXiv | 2026-10-29 | https://arxiv.org/abs/2610.39758"
---

Doohyun Kim, Donghwa Kang, Mingyu Jun and Brent ByungHoon Kang submitted SEAL to arXiv on 29 October 2026, describing a defense against indirect prompt injection in local large language model (LLM) agents. The abstract targets attacks entering through untrusted tool outputs, while seeking to preserve evidence needed for the user's task under limited inference budgets.[^1]

According to the authors, SEAL learns a soft prompt and scoring readout offline, then sanitizes tool outputs using a frozen task model. It constructs scoring queries from trusted initial context and the learned prompt, keeping that reference independent of the tool text being inspected. Token scores avoid normalization across context tokens; preservation regularization encourages retention of useful evidence during localized deletion. The authors say the design needs neither defense-generated tokens nor a separate verifier model.[^1]

The abstract reports evaluations on AgentDojo and AgentDyn. On AgentDojo, the authors report attack success falling from 34.6% to 0.1%, and Joint, defined as task completion without attack success, rising from 51.4% to 77.5%. They also report approximately 127 times fewer defense-related tokens than PISanitizer. Replication on a second backbone using the same training recipe is presented as supporting applicability across model families.[^1]

:::analysis
The claim sits at T6 evaluations and T5 agents: benchmark results concern how an agent handles untrusted tool evidence, so users still depend on whether their deployment matches the evaluated setup. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the relevant setup; this alone cannot establish that an attack occurred or succeeded. Users and operators should check those deployment records against the reported method and evaluation conditions; the saved abstract names no fixed software version or recommended upgrade.[^1]
:::

:::checked
On 30 October 2026, we read the supplied saved arXiv abstract page for SEAL, identifier 2610.39758v1, including its submission history. This establishes what the authors reported, not independent confirmation of the results. We did not read the full paper, inspect code, reproduce benchmarks or test the system; the saved abstract does not provide enough detail to assess deployment-specific protection.[^1]
:::

[^1]: SEAL: Sealed Queries for Local Sanitization against Indirect Prompt Injection. arXiv, submitted 29 October 2026. https://arxiv.org/abs/2610.39758
