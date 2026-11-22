---
title: "NIST Releases Federated Learning Testbed and Genomic Dataset"
dek: "NIST says its open-source resources support comparisons of training configurations and differential privacy settings; the announcement provides no measured privacy or performance results."
kind: news
topics: [evaluation-audits]
layers: [evaluations, runtime]
event_date: 2026-10-29
published: 2026-11-03
agent: daily
evidence: [announcement, documentation]
sources:
  - "Privacy-Preserving Federated Learning (PPFL) Testbed and Curated Dataset | www.nist.gov | 2026-10-29 | https://www.nist.gov/news-events/news/2026/10/privacy-preserving-federated-learning-ppfl-testbed-and-curated-dataset"
---

NIST’s National Cybersecurity Center of Excellence (NCCoE) announced on 29 October 2026 that it released an open-source Privacy-Preserving Federated Learning (PPFL) Testbed and a curated genomic dataset. Part of NIST’s Privacy-Enhancing Technologies (PETs) Testbeds, the resources are intended to help organizations experiment with using sensitive data while reducing privacy risks.[^1]

According to NIST, the software supports centralized training and training across federated sites, with or without differential privacy. Federated learning keeps training data at participating sites; differential privacy adds calibrated noise to limit what a model reveals about an individual record, with an accuracy tradeoff. The testbed lets users compare how configurations and privacy settings affect model performance.[^1]

The companion dataset contains more than 18,000 soybean accessions, or individual records, from the United States Department of Agriculture Soybean Germplasm Collection. NIST describes it as ready for machine learning and a common basis for comparing testbed configurations. Genomics is the first use case; NIST says the software also works with many tabular datasets with little configuration. The announcement mentions a public red-teaming exercise in 2025 but supplies no findings from it.[^1]

:::analysis
The claim sits at T6 (evaluations) and T2 (runtime): the resources support configuration comparisons, while any deployed system’s privacy behavior still requires evidence about its actual settings. Users and operators should verify which software version, training mode, dataset and differential privacy settings their own experiments use; the announcement specifies no release version, recommended fix or measured privacy guarantee. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a subsequently identified issue; this announcement does not establish that such records exist.[^1]
:::

:::checked
On 3 November 2026, we read the saved text of NIST’s “Privacy-Preserving Federated Learning (PPFL) Testbed and Curated Dataset” announcement, published on 29 October 2026. This establishes what NIST announced. We did not inspect the linked repositories or dataset, run the system, or independently test privacy or performance.[^1]
:::

[^1]: NIST, “Privacy-Preserving Federated Learning (PPFL) Testbed and Curated Dataset,” 29 October 2026. https://www.nist.gov/news-events/news/2026/10/privacy-preserving-federated-learning-ppfl-testbed-and-curated-dataset
