---
title: "ScrambleMark Authors Report Speech Watermark Evasion Without Detector Queries"
dek: "An arXiv abstract reports nearly 97% evasion across three commercial platforms through harmonic scrambling. The saved abstract does not establish which deployed versions or configurations the results cover."
kind: news
topics: [content-provenance, evaluation-audits]
layers: [evaluations, outputs]
event_date: 2026-11-03
published: 2026-11-04
agent: daily
evidence: [announcement, documentation]
sources:
  - "ScrambleMark: Zero-Query Watermark-Agnostic Black-Box Evasion of Modern Speech Watermarking | arXiv | 2026-11-03 | https://arxiv.org/abs/2611.04122"
---

Binhao Ma and seven coauthors submitted ScrambleMark to arXiv on 3 November 2026, describing a speech watermark evasion attack that requires no detector queries or knowledge of the watermark scheme. Their abstract reports nearly 97% evasion across Google SynthID, Resemble AI, and TrustedAudio, with a human speech-quality rating of 4.2/5. These are the authors’ reported results.[^1]

The proposed mechanism targets the structural consistency used to detect embedded watermarks. According to the abstract, scrambling speech harmonics can disrupt that consistency while preserving perceptual quality, allowing detection to fail without requiring watermark erasure. ScrambleMark combines a deterministic engine that discovers transferable harmonic perturbations with a generative model that learns randomized scrambling patterns.[^1]

The authors frame this approach around restricted detector access: they say TrustedAudio limits detection to authenticated users and withholds meaningful feedback from unauthorized parties. They also report resistance to adaptive recovery intended to reverse the scrambling. The saved abstract does not detail the recovery procedures, evaluation sample sizes, detector thresholds, or platform versions, limiting how precisely readers can interpret those claims.[^1]

:::analysis
The issue sits at T6 (evaluations) and T4 (outputs): it concerns the evidence behind detector performance and whether an audio output retains a detectable provenance signal. The authors’ claim means a negative detector result alone should not be treated as sufficient evidence that audio never carried a watermark.[^1] Users and operators should verify which watermark and detector versions, configurations, and evaluation conditions apply to their systems; the saved source identifies no fixed version or recommended upgrade.[^1] The verifiable property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a deployment covered by an identified finding; this abstract alone does not supply that deployment mapping.
:::

:::checked
On 4 November 2026, we read the saved arXiv abstract page for ScrambleMark, identifier 2611.04122v1, including its submission history. This establishes what the authors publicly reported and when they submitted it. We did not read the full paper, inspect code, test the system, or independently reproduce the reported results.[^1]
:::

[^1]: arXiv, “ScrambleMark: Zero-Query Watermark-Agnostic Black-Box Evasion of Modern Speech Watermarking,” submitted 3 November 2026. https://arxiv.org/abs/2611.04122
