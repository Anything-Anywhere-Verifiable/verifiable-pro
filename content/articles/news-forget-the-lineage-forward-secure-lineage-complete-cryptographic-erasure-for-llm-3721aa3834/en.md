---
title: "Researchers Propose Cryptographic Erasure for LLM-Agent Memory"
dek: "A paper proposes LinEra to make forgotten inputs and their derived memories unreadable, while reporting a tradeoff between erasure scope and retained memory."
kind: news
topics: [agents-accountability, formal-verification]
layers: [agents]
event_date: 2026-11-13
published: 2026-11-22
agent: daily
evidence: [announcement, documentation]
sources:
  - "Forget the Lineage: Forward-Secure, Lineage-Complete Cryptographic Erasure for LLM-Agent Memory | arXiv | 2026-11-13 | https://arxiv.org/abs/2611.18133"
---

Researchers proposed LinEra, a cryptographic erasure system for large language model (LLM) agent memory, in a paper submitted to arXiv on 13 November 2026. The authors say it addresses a problem that deleting a conversation message alone leaves unresolved: an agent may have already stored summaries, extracted facts or embeddings derived from it, as well as storage residue and backups.[^1]

The paper defines a goal called lineage-complete forward-secure erasure: after a forget request, an adversary that later obtains all storage and the agent's current keys learns nothing about the forgotten input or memories derived from it. The authors say LinEra derives each memory's encryption key from its parent keys in a derivation graph. A forget operation punctures a source key, intended to make descendants unreadable without locating each one. The proposed lineage rule records everything a memory writer saw as a parent. The authors claim security and lineage integrity proofs and report integrating LinEra with mem0.[^1]

In the authors' reported experiments, an attacker holding every file and current keys recovered 70 of 71 forgotten secrets after logical deletion, 67 with per-object or epoch keys, and none with LinEra, across ten conversations written by the largest model tested. The abstract reports the same LinEra outcome for every writer tested. It also reports a tradeoff: forgetting 1% of turns erased 73.0% of derived memories with session-level summaries, versus 3.8% with four-turn windows; the authors say re-derivation restores what is lost.[^1]

:::analysis
The issue sits at T5, the agents layer: a verifier needs evidence about how an agent records derivations and handles keys before trusting that a forget request covers its derived memories. Identifiability matters too: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular behavior or issue. Users and operators should check which memory system and configuration they use and whether lineage and key handling match the paper's proposed design; the saved abstract does not identify a fixed version to run or establish that a deployed service implements it.[^1]
:::

:::checked
On 22 November 2026 we read the saved arXiv abstract page for “Forget the Lineage,” including its submission history and reported results.[^1] We did not read the full paper or test LinEra, its proofs, experiments or any deployment; the reported outcomes and security claims remain the authors' claims.
:::
