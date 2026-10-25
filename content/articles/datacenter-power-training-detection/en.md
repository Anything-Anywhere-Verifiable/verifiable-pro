---
title: Preprint Says an Outside Power Meter Can Detect Undeclared AI Training in Simulations
dek: In a preprint posted on 19 October 2026, three researchers propose that a power meter installed by an outside verifier could detect AI training hidden in a data center's declared inference workload. Their detection results come from simulated power traces, and they plan a study of real training runs on multiple chips.
kind: news
topics: [governance-compute]
layers: [institutions, hardware]
event_date: 2026-10-19
published: 2026-10-25
agent: daily
evidence: [paper]
related: [cset-ai-chip-location-verification, chip-security-act-committee-approval, bis-h200-china-third-party-testing]
sources:
  - Detecting AI Training in Datacentre Power | arXiv (Tom Kimpson, Mauricio Baker and Emlyn Graham) | 2026-10-19 | https://arxiv.org/abs/2610.30182
---

On 19 October 2026 three researchers posted an arXiv preprint on detecting AI training from a data center's power use without trusting its operator. They are Tom Kimpson of the University of Melbourne and the Machine Alignment, Transparency & Security (MATS) program, Mauricio Baker of the University of Oxford and Emlyn Graham of MATS. In their simulations, a verifier owns a tamper-evident meter at a rack or facility power input and looks for training hidden in a declared inference workload.[^1]

Synchronous training, in which each step waits for the slowest chip, alternates high-power computing with lower-power data exchange about once a second. The authors' Viterbi tracker, an algorithm that traces a changing frequency through noisy data, follows this drifting rhythm. When the operator did not hide training, the tracker detected it in at least 96% of simulated five-minute traces at a 1% false-alarm rate, they report. These results required a meter sampling at least twice a second; at once a second, detection fell to 33%.[^1]

Of eight simulated hiding strategies, such as random pauses, the authors say only extreme random variation in the work per step evades the tracker. Its strongest form hid training in up to 73% of five-minute windows, yet a test that accumulates evidence flagged 87% of such runs within a day, at a 0.1% false-alarm rate per run. The strategy leaves processing speed unchanged, they say, but training a 30-million-parameter model with it on one A100 graphics processing unit (GPU) took 93% to 267% more compute to reach the same loss, the error that training reduces.[^1]

The authors call the synthetic traces their primary limitation: the training-power model they adopt could not be tested quantitatively, because facility-scale measurements are proprietary. Their planned study of real multi-GPU runs needs equipment that is not currently available. They write that a detection establishes only a persistent, training-shaped rhythm, which permitted fine-tuning and some other periodic loads can also produce.[^1]

:::analysis
A verifier-owned meter lets an outsider look for training without relying on the operator's account. A detection does not show how large a run is. The error rates apply to a real site only if its power use resembles the simulations, and the paper assumes, without explaining how, that the meter is tamper-evident.
:::

:::checked
On 25 October 2026 we read the preprint's arXiv record and full text (version 1) and found no other coverage. The paper links no code, and we did not repeat the simulations; every figure is the authors' own. The abstract gives the 96% per run; the paper measures it per five-minute trace. The paper also reports two random-pause settings that hid 12% and 24% of windows while slowing training.
:::
