---
title: "Hao AI Lab Reports Verification Workflow and Prototype for LLM Serving"
dek: "The lab reports concurrency bugs in two serving engines and a formal safety proof for an abstract page-lifecycle design. The proof does not establish that the implementation is bug-free."
kind: news
topics: [formal-verification, verifiable-inference]
layers: [runtime]
event_date: 2026-11-10
published: 2026-11-18
agent: daily
evidence: [announcement, documentation]
sources:
  - "Towards Verifiable LLM Infra | haoailab.com | 2026-11-10 | https://haoailab.com/blogs/verifiable-llm-infra/"
---

On 10 November 2026, UC San Diego’s Hao AI Lab introduced vstack, a five-stage verification workflow for coding agents, and veriserve, a prototype large language model serving engine. The lab reports that applying the workflow to SGLang and vLLM uncovered three classes of concurrency problems and led to proposed upstream fixes.[^1]

The work examines serving systems that split prompt processing from token generation and transfer key-value (KV) cache pages between them using remote direct memory access (RDMA). The authors report reproducing races in which a page or transfer identity was reused before an earlier transfer stopped. They say late transfers could read or overwrite another request’s cache while the server returned HTTP 200. They also report a corrupted page entering a shared prefix cache and stalled transfers leaving requests waiting.[^1]

Vstack pins specifications, maps model transitions to code, checks model fidelity against buggy and patched behavior, and applies model checking and theorem proving. In veriserve, a design called PdLedger tracks page generations and separates pages awaiting evidence that transfers have stopped from pages quarantined when that evidence is unavailable. The authors report a TLAPS safety proof for the abstract design under stated assumptions, and a mean 0.18% median time-per-output-token overhead across six paired runs. These are the authors’ reported results; the proof does not establish that the Python implementation, GPU kernels or RDMA providers are bug-free.[^1]

:::analysis
The issue sits at T2, the runtime layer: a verifier’s trust in a serving system depends on how its actual implementation and configuration manage cache pages, as well as on the fidelity and assumptions of any model used to assess them. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the affected conditions described by the authors. Users and operators should check their own deployed versions, configurations and relevant fix status against the reported conditions; the source lists proposed fixes but does not recommend a fixed release version. A proof of the abstract model alone does not identify which software served a particular request.[^1]
:::

:::checked
For this preview, prepared on 18 November 2026, we read the saved copy of Hao AI Lab’s “Towards Verifiable LLM Infra,” published on 10 November 2026: https://haoailab.com/blogs/verifiable-llm-infra/.[^1] We did not test vstack, veriserve or the reported bugs, independently verify the proof or benchmark, or establish whether the proposed fixes have been merged or deployed.
:::
