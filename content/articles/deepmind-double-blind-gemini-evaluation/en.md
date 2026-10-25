---
title: Google DeepMind Pilots Double-Blind Evaluation of a Gemini Model Inside a Secure Enclave
dek: Google DeepMind said on 27 August 2026 that outside evaluators had tested Gemini 2.5 Flash-Lite on secret safety prompts inside a hardware-isolated enclave designed to keep each side's assets hidden from the other. The accompanying technical report also lists the trust the setup still places in Google.
kind: news
topics: [evaluation-audits, confidential-computing]
layers: [evaluations]
event_date: 2026-08-27
published: 2026-10-20
agent: daily
evidence: [announcement, report]
sources:
  - Piloting the world's first double-blind AI evaluations | Google DeepMind | 2026-08-27 | https://deepmind.google/blog/piloting-the-worlds-first-double-blind-ai-evaluations/
  - Double Blind Evals: Resolving the Dual Confidentiality Dilemma in AI Safety Auditing | Google DeepMind (technical report) | 2026-08-27 | https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/piloting-the-worlds-first-double-blind-ai-evaluations/double-blind-evaluations-technical-report.pdf
  - AVERI Pilot Report: The World's First Double-Blind Evaluation of a Proprietary Language Model | AVERI | 2026-08-27 | https://www.averi.org/ourwork/averi-pilot-report-the-worlds-first-double-blind-eval
  - The key to trustworthy AI evaluation is secrecy by design | MLCommons | 2026-08-27 | https://mlcommons.org/2026/08/double-blind-reliability-evaluation/
---
Google DeepMind said on 27 August 2026 that it had piloted what it calls the first double-blind evaluation of a proprietary frontier-class model. Its partners were the Singapore AI Safety Institute, OpenMined, the AI Verification and Evaluation Research Institute (AVERI) and MLCommons.[^1] DeepMind says Google Cloud's Confidential Space kept the evaluators from seeing the Gemini weights and Google from seeing their test prompts.[^1]

The technical report names the model as Gemini 2.5 Flash-Lite. It was served on a Google Cloud virtual machine with Intel Trust Domain Extensions (TDX) memory encryption and an NVIDIA H100 GPU in confidential mode. OpenMined's PySyft software ran only code that both parties had approved. Before sending its assets in, each party checked the enclave's hardware attestation, signed evidence of the software the enclave had loaded.[^2]

For one track, MLCommons supplied prompts from a reserved set of its AILuminate safety benchmark that no Google DeepMind model had seen.[^2, 4] AVERI encrypted the prompts, and the run took place in an enclave Google configured. Afterward, AVERI graded the decrypted outputs and reported confidentially to Google DeepMind.[^3] A second track, with the Singapore institute, used a private prompt set on harmful content in Singapore's context. Neither the report nor AVERI's post publishes benchmark scores.[^2, 3]

The report also states limits: not all of the Gemini inference code could be inspected or restricted to an allowlist of approved operations. It says AVERI accepted the setup knowing this. The guest operating system's source is open, but its builds cannot be reproduced independently because they take private signing keys as inputs. Google's services sign and verify the attestation report, which the authors say places Google in the verification path.[^2] AVERI writes that the design addressed many but not all ways the developer could in theory tamper with the evaluation. It adds that less trusting settings, such as verifying an international agreement, would need more assurances.[^3]

:::analysis
The pilot shows a way to run a secret benchmark against proprietary weights without either party handing over its asset. That directly addresses benchmark contamination, in which test items end up in a model's training data. The prompts' confidentiality rests on the attested software, the hardware vendors and, in this pilot, Google, whose inference code was partly uninspectable and whose services verified the attestation. Because the evaluated company also configured the enclave, independent attestation checks and reproducible builds would reduce how much that confidentiality rests on Google.
:::

:::checked
On 20 October 2026 we read Google DeepMind's post, the technical report it links, AVERI's pilot report and MLCommons' post. We did not examine the enclave, its attestation evidence or the PySyft code, and we could not see the results AVERI gave Google DeepMind. The report gives two AILuminate versions, so we name neither.
:::
