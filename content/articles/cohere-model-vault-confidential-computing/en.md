---
title: Cohere Introduces Confidential Computing for Model Vault in Beta
dek: On 16 September 2026 Cohere announced an encrypted option for Model Vault, its single-tenant model deployment service, that runs models in confidential virtual machines with NVIDIA GPUs. Its documentation describes attestation checks on the client and an attestation record returned with every response.
kind: news
topics: [confidential-computing]
layers: [runtime, hardware]
event_date: 2026-09-16
published: 2026-10-20
agent: daily
evidence: [announcement, documentation]
sources:
  - Introducing Confidential Computing in Model Vault | Cohere on X | 2026-09-16 | https://x.com/cohere/status/2100255182579769721
  - Remote Attestation (Model Vault Encrypted documentation) | Cohere | accessed 2026-10-20 | https://docs.cohere.com/docs/model-vault/encrypted/attestation
  - Frequently Asked Questions About Model Vault Encrypted | Cohere | accessed 2026-10-20 | https://docs.cohere.com/docs/model-vault/encrypted/faq
---

On 16 September 2026 Cohere announced Confidential Computing in Model Vault in a post on X. It said that no one, including Cohere, can access customers' workloads.[^1] Model Vault gives customers dedicated, single-tenant model deployments. Cohere's documentation calls the new option Model Vault Encrypted and says it is in beta for customers who contact the company.[^3]

According to the documentation, inference runs inside a hardware-based confidential virtual machine (VM) paired with an NVIDIA GPU in confidential-computing mode. In a confidential VM, the hardware encrypts the VM's memory and is designed to isolate it from the host. The documentation's examples are VMs using Intel Trust Domain Extensions (TDX) or AMD Secure Encrypted Virtualization-Secure Nested Paging (SEV-SNP).[^3] Clients encrypt requests with Oblivious HTTP (OHTTP) to a key generated inside the attested environment, so the load balancer and network carry only ciphertext.[^2]

The documentation describes a deployment on Intel TDX. In that deployment, Intel Trust Authority, Intel's attestation service, appraises the evidence from the CPU and GPU against an approved policy and issues a signed token. Before sending any data, Cohere's client proxy verifies Intel's signature and the measurements (hashes of the loaded code and configuration) that the token reports. It also checks that the encryption key is bound to the attested environment, and it refuses to connect if a check fails.[^2]

Every inference response also includes an attestation certificate that customers can keep as a record of the environment that served the request. Cohere says the approved measurements come from reproducible builds of open-source code, so an independent party can rebuild the artifacts and compare them.[^2, 3]

The documentation's frequently asked questions (FAQ) page also lists what stays visible outside the protected environment: routing metadata such as the model name, operational metrics, and network timing and byte volume. The residual risks it names include hardware side channels (indirect leaks through effects such as timing), attacks that require deep physical access, and the operator's ability to stop or restart the environment.[^3]

:::analysis
In the Intel deployment, the attestation that customers check and keep depends on Intel's appraisal of the hardware evidence. It is also only as informative as the approved measurements behind it. Much of the weight therefore rests on Cohere's statement that the measurements come from reproducible builds of open-source code. Outsiders can test that statement only by rebuilding the image and comparing the results.
:::

:::checked
On 20 October 2026 we opened Cohere's 16 September 2026 post on X and the Remote Attestation and FAQ pages of the Model Vault documentation. We found no Cohere blog post or press release about the launch, so the details come from the documentation. Its pages are undated, so the dates in our source list are the day we read them. We did not rebuild the vault image, check Cohere's statement that its code is open source, or test a deployment. Statements about who can access customer data are Cohere's claims.
:::
