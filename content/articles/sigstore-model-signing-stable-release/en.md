---
title: Sigstore Model-Signing Library Reaches Version 1.0
dek: Google's Open Source Security Team released version 1.0 of the model-signing package on 4 April 2025, after a year of work with the Open Source Security Foundation, NVIDIA and HiddenLayer. A publisher can sign a model's files, and anyone downstream can check that the files match what a known identity signed.
kind: news
topics: [supply-chain]
layers: [models]
event_date: 2025-04-04
published: 2026-10-20
agent: daily
evidence: [announcement, code, documentation]
sources:
  - Taming the Wild West of ML: Practical Model Signing with Sigstore | Sigstore Blog | 2025-04-04 | https://blog.sigstore.dev/model-transparency-v1.0
  - Launch of Model Signing v1.0: OpenSSF AI/ML Working Group Secures the Machine Learning Supply Chain | Open Source Security Foundation | 2025-04-04 | https://openssf.org/blog/2025/04/04/launch-of-model-signing-v1-0-openssf-ai-ml-working-group-secures-the-machine-learning-supply-chain/
  - Model signing 1.0 (release notes) | GitHub, sigstore/model-transparency | 2025-04-04 | https://github.com/sigstore/model-transparency/releases/tag/v1.0.0
  - Model Transparency README at the v1.0.0 tag | GitHub, sigstore/model-transparency | 2025-04-04 | https://github.com/sigstore/model-transparency/blob/v1.0.0/README.md
related: [g7-ai-sbom-minimum-elements]
---

Google's Open Source Security Team announced version 1.0 of the model-signing project in a Sigstore blog post on 4 April 2025. The team says it built the package over the previous year with the Open Source Security Foundation (OpenSSF), NVIDIA and HiddenLayer, on top of the sigstore-python library.[^1] On the same day, OpenSSF announced the release as a project of its AI/ML working group.[^2] The GitHub release notes describe 1.0 as the first stable release, with a backward-compatible programming interface, a command-line tool and a defined signature scheme.[^3]

The library can sign with public keys and certificates or with Sigstore. The project describes Sigstore as a way to make code signatures transparent without managing cryptographic keys.[^4] The post recommends Sigstore as the default. In that workflow, signing obtains a short-lived certificate bound to the OpenID Connect identity of the developer or workload. OpenID Connect is a standard sign-in protocol. The signature and certificate are then recorded in Sigstore's transparency log, a public record of signing events. According to the post, the log helps monitor signing events so that a rogue insider cannot release models as if the company had signed them. The post adds that model hubs and users can verify a model after its certificate expires, because the certificate and a proof of inclusion in the log are uploaded with the model.[^1]

The signature is stored as a Sigstore bundle whose signed statement lists the model's files with their hashes. Verification checks the signature and then recomputes the file hashes.[^4] The team designed the library to be built into model hubs such as Kaggle and Hugging Face, which could verify signatures at upload. It was also designed to be built into frameworks such as PyTorch, where saving a model could sign it.[^1] OpenSSF's announcement says signatures should be checked when a model is uploaded to a hub, selected for deployment or used as input to another model.[^2]

:::analysis
A model signature shows only that the files are the ones a given identity signed. It does not establish how the model was trained or whether it is safe to run. The check is only as useful as the verifier's knowledge of which identity should have signed. A signature also cannot show which files a hosted service actually loads; that would need separate evidence, such as remote attestation of the serving environment.
:::

:::checked
On 20 October 2026 we read the Sigstore blog post, OpenSSF's announcement, the v1.0.0 release notes on GitHub and the project's README at the v1.0.0 tag. This brief covers the April 2025 release; we did not review later versions. We did not install the library or verify any signed model, and we test no systems ourselves.
:::
