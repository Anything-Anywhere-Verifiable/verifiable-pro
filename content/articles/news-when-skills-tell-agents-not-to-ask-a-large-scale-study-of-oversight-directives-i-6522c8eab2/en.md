---
title: "Study Reports Oversight-Loosening Directives in About One in 17 Agent Skills"
dek: "A preprint analyzes 1.53 million English skills and reports concentrated copying of instructions that bypass checkpoints. Its abstract reports limited scanner detection, without establishing deployed agent behavior."
kind: news
topics: [agents-accountability, evaluation-audits, supply-chain]
layers: [evaluations, agents]
event_date: 2026-10-27
published: 2026-11-01
agent: daily
evidence: [announcement, documentation]
sources:
  - "When Skills Tell Agents Not to Ask: A Large-Scale Study of Oversight Directives in Agent Skills | arXiv | 2026-10-27 | https://arxiv.org/abs/2610.37734"
---

Timofey Sanko and Yuan Tian submitted a preprint on 27 October 2026 reporting that about one in seventeen English agent skills contains instructions that loosen human oversight. The abstract of *When Skills Tell Agents Not to Ask* describes an analysis of 1.53 million skills from GitSkills, with about 88,000 containing such directives.[^1]

Skills are reusable instruction packages loaded by agents. The authors identify directives to proceed without approval, bypass checks with `--no-verify`, or continue without checking in. They report manually labeling 2,097 instruction units and training a detector to extend the analysis. Permission flags were the most common mechanism, and 70.1% of loosening directives applied unconditionally.[^1]

Among skills with comparable amounts of oversight language, those running shell code, installing packages, or using `sudo` had 1.7–1.8 times the odds of containing loosening directives, the authors report. Copying was concentrated: 2.4% of skill families carrying such directives accounted for half of their copies. These are reported associations and corpus findings; the abstract does not establish how often deployed agents followed those instructions.[^1]

The authors also report that open-source skill scanners detected at most 46% of loosening directives, with precision below 0.4. The language model behind those scanners, prompted with their labeling codebook, detected 61% at precision 0.71. These figures describe the authors’ evaluation, rather than independently reproduced results.[^1]

:::analysis
The issue sits at T6 (evaluations), where scanner results need defined coverage, and T5 (agents), where loaded instructions can alter oversight; detecting text alone does not establish execution behavior. The verifiable property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the identified directives. Users and operators should check which skill versions were loaded, their approval directives, and the scanner configuration used to review them; the saved abstract recommends no fixed software version. Exposure to a directive still leaves its effect on execution to be established.[^1]
:::

:::checked
On 1 November 2026, we read the saved arXiv abstract and submission metadata for arXiv:2610.37734v1, marked as a preprint. We did not read the full paper, inspect its dataset or code, reproduce its evaluation, or test any agent system; our reading establishes what the abstract reports.[^1]
:::

[^1]: https://arxiv.org/abs/2610.37734

Lead photo: Timofey Sanko, Yuan Tian · CC BY 4.0.
