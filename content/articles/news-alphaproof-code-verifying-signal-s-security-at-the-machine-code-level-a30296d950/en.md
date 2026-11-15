---
title: "Google DeepMind Reports Machine-Code Security Proofs for libsignal"
dek: "AlphaProof Code connects selected Signal security properties to a compiled binary, according to the authors. The result still depends on trusted specifications, execution semantics and cryptographic assumptions."
kind: news
topics: [formal-verification]
layers: [runtime]
event_date: 2026-11-10
published: 2026-11-15
agent: daily
evidence: [announcement, documentation]
sources:
  - "AlphaProof Code: Verifying Signal’s Security at the Machine-Code Level | google-deepmind.github.io | 2026-11-10 | https://google-deepmind.github.io/code-verification/"
---

Google DeepMind and Google researchers introduced AlphaProof Code on 10 November 2026, reporting machine-code proofs of selected security properties of libsignal, the Signal protocol’s reference implementation. The framework combines human-reviewed Lean specifications with autonomous proof agents; Lean’s kernel checks the resulting mathematical proofs.[^1]

The authors say they linked unmodified libsignal into a small command-line harness and compiled it with stock rustc for AArch64 Linux. They report about 6.5 million lines of Lean proofs, resting on roughly 26,000 lines of trusted specifications and machine-code semantics. A comparator checks that theorem statements and their dependent definitions match an approved, held-out specification, addressing the risk that proof generation silently weakens the claim.[^1]

The reported results cover PQXDH and Triple Ratchet. The introduction describes confidentiality, authenticity, forward secrecy and post-compromise security against classical attackers, plus symbolic handshake secrecy against a future quantum attacker. These claims have explicit boundaries: cryptographic primitives are idealized or assumed secure, and some called routines use trusted contracts. The execution model covers a single-threaded, statically linked process and excludes features including threads and dynamic linking.[^1]

:::analysis
The claim sits at T2 (runtime): a verifier can check a relationship between specified properties and particular executable bytes, while still trusting the specification, Lean’s kernel and the execution model’s correspondence to real systems. Users and operators should check whether their deployed binary and configuration fall within that scope; the supplied text identifies no fixed version to install. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a relevant issue, provided its affected scope is established; this report alone establishes no deployment’s exposure status.[^1]
:::

:::checked
On 15 November 2026, we read the supplied saved text of “AlphaProof Code: Verifying Signal’s Security at the Machine-Code Level,” dated 10 November 2026. We did not inspect the linked repository, rerun Lean or test the system. Our reading establishes what the authors report and the stated assumptions, without independently validating their proofs or deployed applications.[^1]
:::

[^1]: Google DeepMind and Google, “AlphaProof Code: Verifying Signal’s Security at the Machine-Code Level,” 10 November 2026. https://google-deepmind.github.io/code-verification/
