---
title: AVERI Launches and Proposes Four Assurance Levels for Frontier AI Audits
dek: The AI Verification and Evaluation Research Institute launched on 15 January 2026 with a 48-author paper on third-party audits of frontier AI developers. The paper's four AI Assurance Levels grade how much confidence an audit provides, starting from audits that rely heavily on the company's own statements.
kind: news
topics: [evaluation-audits]
layers: [evaluations]
event_date: 2026-01-15
published: 2026-10-20
agent: daily
evidence: [paper, press]
sources:
  - "Frontier AI Auditing: Toward Rigorous Third-Party Assessment of Safety and Security Practices at Leading AI Companies | AVERI | 2026-01-15 | https://www.averi.org/ourwork/frontier-ai-auditing"
  - "Frontier AI Auditing: Toward Rigorous Third-Party Assessment of Safety and Security Practices at Leading AI Companies (arXiv:2601.11699v4) | arXiv | 2026-02-07 | https://arxiv.org/abs/2601.11699v4"
  - "Exclusive: Former OpenAI policy chief creates nonprofit institute, calls for independent safety audits of frontier AI models | Fortune | 2026-01-15 | https://fortune.com/2026/01/15/former-openai-policy-chief-creates-nonprofit-institute-calls-for-independent-safety-audits-of-frontier-ai-models/"
---

Miles Brundage, a former policy researcher at OpenAI, formally announced the AI Verification and Evaluation Research Institute (AVERI) on 15 January 2026, Fortune reported.[^3] AVERI is a US nonprofit that advocates external audits of frontier AI developers, the companies that build the most capable AI systems. It is also working on auditing standards.[^1, 3] Its launch coincided with a paper by Brundage and 47 co-authors.[^2, 3] The paper defines frontier AI auditing as rigorous third-party verification of developers' safety and security claims, and evaluation of their systems and practices against relevant standards. Under this definition, auditors rely on deep, secure access to non-public information.[^1]

The paper proposes four AI Assurance Levels (AALs) to communicate how much confidence an audit's conclusions provide.[^1] An AAL-1 audit covers one system, typically over a few weeks, and the auditor still relies heavily on the company's own statements. An AAL-2 audit spans months and adds gray-box system access, meaning partial access to the system's internals. It also adds internal documents such as safety cases, and interviews with staff across several functions. Its methods include reproducing a sample of internal evaluations and developing statistical model signatures to confirm that audited models correspond to deployed ones.[^2] The two higher levels add white-box access to internals such as model weights, and more extensive continuous monitoring. AAL-4 further aims to detect active deception. Its tools include tamper-evident logging and hardware attestation, in which a chip signs evidence about its identity, configuration and operating state.[^2]

The authors recommend AAL-1 as a baseline for frontier AI and AAL-2 as a near-term goal for the most advanced developers. They say AAL-3 and AAL-4 are not yet technically and organizationally feasible.[^1] The paper names three challenges to making them feasible: confirming that auditors receive complete information, monitoring continuously, and letting auditors examine sensitive information without exposing it. The research priorities it lists include proof-of-training techniques, change-detection infrastructure and model fingerprinting.[^2]

:::analysis
The levels make explicit what an audit result rests on. At AAL-1 the auditor depends largely on what the company says, so the word *audited* tells a reader little unless the level is stated. The framework also gives verification research a defined place in audit practice, because the authors call for it to make the higher levels feasible. Proof-of-training and model fingerprinting are among the techniques they name.
:::

:::checked
On 20 October 2026 we read AVERI's paper page, version 4 of the paper on arXiv (revised 7 February 2026) and Fortune's report of 15 January 2026. The level details above come from that arXiv version. We did not review any audit conducted under this framework, and we test no systems ourselves.
:::
