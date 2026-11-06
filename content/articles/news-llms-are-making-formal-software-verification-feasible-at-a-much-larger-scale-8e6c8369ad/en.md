---
title: "Anthropic Reports Assembly-Level Proofs Across 123 Open-Source Libraries"
dek: "Claude generated proofs for 239 fuzz-test entry points, Anthropic says. Their scope depends on exact binaries, specifications and modeled execution conditions."
kind: news
topics: [formal-verification]
layers: [evaluations, runtime]
event_date: 2026-10-22
published: 2026-11-05
agent: daily
evidence: [announcement, documentation]
sources:
  - "LLMs are making formal software verification feasible at a much larger scale | www.anthropic.com | 2026-10-22 | https://www.anthropic.com/research/formal-verification"
---

Anthropic reported on 22 October 2026 that, working with Theorem, it used Claude to patch bugs and produce formal proofs for 239 fuzz-test entry points across 123 open-source libraries. The company says the proofs cover compiled RISC-V binaries and total about 180 million lines of Rocq proof code. These are reported research results, rather than results independently reproduced for this article.[^1]

The workflow converts existing fuzz tests into mathematical specifications: the compiled test must exit normally without triggering specified crashes, including assertions and AddressSanitizer checks, for inputs smaller than 64 MB. Claude writes proofs that the Rocq kernel checks against those specifications. The modeled setting assumes a single-threaded, statically linked RISC-V binary, a fixed memory budget and Linux process semantics.[^1]

Anthropic says it is publishing trusted components and complete proofs for fuzz tests that required no patches, alongside specifications it could not prove. It is withholding proofs that could expose unpatched bugs. Its stated trust base includes the exact theorem statements, the RISC-V and Linux formal models, and the Rocq checker.[^1]

The limitations are substantial: the proofs concern binaries linked against musl libc, while deployments may use other architectures and dynamic linking. AddressSanitizer misses some memory-safety bugs; tested entry points do not cover an entire library, and callers can misuse it.[^1]

:::analysis
This claim sits at T6 (evaluations) and T2 (runtime): a verifier can check a stated property against a modeled executable, while deployment coverage depends on matching the actual binary and execution conditions. Users and operators should verify their library build, architecture, linking, input limits and caller assumptions against the proved specification; this source gives no general fixed-version recommendation. The operational property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a subsequently identified affected configuration; proof coverage still requires the source’s narrower conditions.[^1]
:::

:::checked
On 5 November 2026, we read the supplied saved text of Anthropic’s “LLMs are making formal software verification feasible at a much larger scale,” published on 22 October 2026. The saved text ends mid-conclusion. We did not inspect released proof artifacts, run the checker or test the system; our reading establishes what the announcement claims and qualifies.[^1]
:::

[^1]: Anthropic, “LLMs are making formal software verification feasible at a much larger scale,” 22 October 2026. https://www.anthropic.com/research/formal-verification
