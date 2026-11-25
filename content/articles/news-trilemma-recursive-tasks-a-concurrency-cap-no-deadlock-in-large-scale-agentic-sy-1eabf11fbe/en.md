---
title: "CocoIndex Describes Slot Lending to Bound Recursive Task Concurrency"
dek: "The company says its scheduling rule bounds executing and in-flight tasks while avoiding a particular deadlock. Its published argument has assumptions, and a concurrency cap is not a memory cap."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-17
published: 2026-11-25
agent: daily
evidence: [announcement, documentation]
sources:
  - "Trilemma: recursive tasks, a concurrency cap, no deadlock in large-scale agentic systems | cocoindex.io | 2026-11-17 | https://cocoindex.io/blogs/bounded-concurrency-task-tree/"
---

On 17 November 2026, CocoIndex described a scheduling rule for recursive task trees that it says limits concurrency without the deadlock caused when waiting parents hold all available slots. The company says it has used the rule, called slot lending, since CocoIndex 1.0.26.[^1]

The problem can arise in an agent’s context pipeline: a task starts children and waits for them, while the children need slots from the same limited pool. If parents retain every slot, none of their children can start. CocoIndex says its earlier approach released a parent’s slot when it mounted its first child, avoiding that deadlock but leaving the number of started tasks holding state unbounded.[^1]

Under lending, a parent keeps its slot and lends it to one child at a time; other children use free pool slots or wait. The article argues that, for its model, tasks holding an unlent slot stay within the cap and in-flight tasks stay within the cap multiplied by the number of tree levels. Its deadlock argument assumes tasks wait only on their own children; an external dependency that never opens can still block progress.[^1]

CocoIndex reports a benchmark in which an indexer-shaped workload under a cap of 16 reached more than 1,100 file components in flight on version 1.0.25, compared with 16 on version 1.1.1. These are the company’s reported results, not an independent test. The article also says a concurrency cap is not a memory cap.[^1]

:::analysis
The issue sits at T5, the agents layer, and T2, the runtime layer: an agent’s context pipeline depends on the scheduler’s behavior, so its operator must assess the implementation and workload as well as the model’s argument. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the earlier behavior. Users and operators should check their deployed version and concurrency settings, whether recursive tasks wait on external gates, and how much memory tasks retain; the article identifies 1.0.26 as the start of lending and reports its benchmark on 1.1.1. Version information alone does not establish that a particular deployment cannot stall or exhaust memory.[^1]
:::

:::checked
On 25 November 2026, we read the saved copy of [CocoIndex’s engineering article on bounded concurrency](https://cocoindex.io/blogs/bounded-concurrency-task-tree/), published on 17 November 2026.[^1] We did not run its examples, inspect the engine independently, or test the system; the reported benchmark and implementation behavior remain CocoIndex’s claims.
:::
