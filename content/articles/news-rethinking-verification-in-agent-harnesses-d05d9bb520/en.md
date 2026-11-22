---
title: "Agent Harness Study Reports Accuracy Gains From Independent Review"
dek: "An arXiv preprint compares 17 verification designs and reports favorable accuracy-cost tradeoffs for independent critics. The saved abstract supports those reported findings, but does not establish performance in a deployed service."
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, agents]
event_date: 2026-10-25
published: 2026-11-06
agent: daily
evidence: [announcement, documentation]
sources:
  - "Rethinking Verification in Agent Harnesses | arXiv | 2026-10-25 | https://arxiv.org/abs/2610.34577"
---

A preprint submitted to arXiv on 25 October 2026 reports that independent review can improve coding agents’ accuracy at relatively modest additional cost. In *Rethinking Verification in Agent Harnesses*, Zhengxin Zhang and five coauthors examine how the frameworks surrounding tool-using language models organize checks and revisions of their work.[^1]

The authors describe verification as an axis of test-time scaling: spending additional effort during task execution. Their framework covers initial instructions, mid-turn reminders, completion gates and independent review. They report comparing 17 designs across seven frontier coding models on Terminal-Bench (TB) and SWE-bench Verified (SWE), and introducing VisualBench for expert evaluation of visual and interactive artifacts.[^1]

According to the abstract, independent critics improve average accuracy by 5.9–9.5 percentage points on TB and 3.9–6.6 points on SWE, at respective costs of 1.13–1.25 and 1.00–1.04 times baseline. Initial instructions and reminders produce modest, model-dependent gains; completion gates can produce larger gains with substantially higher costs. On VisualBench, independent review receives net preferences of 13.2–23.8 points over baseline across four designs. These are the authors’ reported experimental findings.[^1]

:::analysis
The issue sits at T6 evaluations and T5 agents: benchmark comparisons inform confidence in a checking procedure, while the harness determines when a critic intervenes and how work is revised. Those comparisons do not establish that a particular user’s output is correct; users and operators should check which model, harness design, review rounds and critic arrangement their own system uses before applying the reported averages. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular configuration; the saved abstract supplies no such deployment record or recommended fixed software version.[^1]
:::

:::checked
On 6 November 2026, we read the saved arXiv abstract page for *Rethinking Verification in Agent Harnesses*, identifier 2610.34577, showing submission version v1. We did not read the full paper or inspect code, and we did not test the system or reproduce the results. This reading establishes what the abstract reports, leaving experimental methods and deployment applicability unconfirmed.[^1]
:::

[^1]: *Rethinking Verification in Agent Harnesses*. arXiv, 25 October 2026. https://arxiv.org/abs/2610.34577

Lead photo: Zhengxin Zhang, Erkang Zhu, Yin Lin, Claire Cardie, Bolin Ding, Jingren Zhou · CC BY 4.0.
