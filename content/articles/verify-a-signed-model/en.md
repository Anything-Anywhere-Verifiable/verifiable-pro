---
title: How to verify a signed model before you load it
dek: Before any code loads the weights, use this five-step worksheet to check that a model's files are the ones the expected publisher signed, and to record which files the check covered.
needs: the model files, the signature bundle and the expected signer's identity
kind: guide
topics: [supply-chain]
layers: [models]
published: 2026-10-20
agent: research
evidence: [documentation, code, paper, announcement]
related: [sigstore-model-signing-stable-release, g7-ai-sbom-minimum-elements, etsi-en-304-223-ai-security]
disclosure: The software that researched and drafted this guide is built on Anthropic's Claude models. This guide cites a paper by Anthropic researchers and co-authors from other institutions.
sources:
  - Model Transparency README at the v1.1.1 tag | GitHub, sigstore/model-transparency | 2025-10-10 | https://github.com/sigstore/model-transparency/blob/v1.1.1/README.md
  - model-signing release metadata (JSON API) | Python Package Index (PyPI) | accessed 2026-10-20 | https://pypi.org/pypi/model-signing/json
  - Command-line interface source (_cli.py) at the v1.1.1 tag | GitHub, sigstore/model-transparency | 2025-10-10 | https://github.com/sigstore/model-transparency/blob/v1.1.1/src/model_signing/_cli.py
  - Verification API source (verifying.py) at the v1.1.1 tag | GitHub, sigstore/model-transparency | 2025-10-10 | https://github.com/sigstore/model-transparency/blob/v1.1.1/src/model_signing/verifying.py
  - Hashing API source (hashing.py) at the v1.1.1 tag | GitHub, sigstore/model-transparency | 2025-10-10 | https://github.com/sigstore/model-transparency/blob/v1.1.1/src/model_signing/hashing.py
  - Signature payload source (signing.py) at the v1.1.1 tag | GitHub, sigstore/model-transparency | 2025-10-10 | https://github.com/sigstore/model-transparency/blob/v1.1.1/src/model_signing/_signing/signing.py
  - Changelog on the main branch at commit 087c3f5 | GitHub, sigstore/model-transparency | accessed 2026-10-20 | https://github.com/sigstore/model-transparency/blob/087c3f5f05e6c84287bd25393084be6f4f7760c4/CHANGELOG.md
  - Launch of Model Signing v1.0: OpenSSF AI/ML Working Group Secures the Machine Learning Supply Chain | Open Source Security Foundation | 2025-04-04 | https://openssf.org/blog/2025/04/04/launch-of-model-signing-v1-0-openssf-ai-ml-working-group-secures-the-machine-learning-supply-chain/
  - Sigstore Bundle Format | Sigstore documentation | 2025-01-14 | https://docs.sigstore.dev/about/bundle/
  - CLI (Rekor transparency log) | Sigstore documentation | accessed 2026-10-20 | https://docs.sigstore.dev/logging/cli/
  - sigstore.dev and Rekor evolution | Sigstore Blog | 2026-06-28 | https://blog.sigstore.dev/rekor-evolution/
  - Rekor v2 GA - Cheaper to run, simpler to maintain | Sigstore Blog | 2025-10-10 | https://blog.sigstore.dev/rekor-v2-ga/
  - Software Bill of Materials for AI: Minimum Elements | G7 Cybersecurity Working Group, via BSI | 2026-05-12 | https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/KI/SBOM-for-AI_minimum-elements.html
  - Planting Undetectable Backdoors in Machine Learning Models | arXiv (Goldwasser, Kim, Vaikuntanathan and Zamir) | 2022-04-14 | https://arxiv.org/abs/2204.06974
  - Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training | arXiv (Hubinger et al.) | 2024-01-10 | https://arxiv.org/abs/2401.05566
---

A model signature lets you check that the files on your disk are the ones a known publisher signed, before any code loads the weights.[^1] The check is only as strong as the signer identity you compare it against, and it covers only the signed files. Each step below therefore pairs a command with the decision it supports. The guide uses `model_signing`, the command-line tool of the model-signing package from Sigstore's model-transparency project.[^1, 2] Version 1.1.1 was the current release on the Python Package Index (PyPI) on 20 October 2026.[^2] Our [brief on the 1.0 release](/articles/sigstore-model-signing-stable-release/) gives the background.

## When to use this guide

Use it when a signed model arrives and you are about to serve it, fine-tune it or hand it to another system. The AI/ML working group of the Open Source Security Foundation (OpenSSF) announced the 1.0 release in April 2025. The group says signatures should be checked each time a model is used, including when it is selected for deployment and when it becomes input to another model.[^8]

## What you need before you start

- **The model directory**, exactly as you will load it and made of regular files. The tool stops with an error at a symbolic link unless you allow links.[^5]
- **The signature bundle** distributed with the model, which the tool names `model.sig` by default.[^1, 3]
- **The expected signer**, from a channel you already trust, such as the publisher's documentation. Never copy it from the bundle: the bundle names whoever signed, who may not be the publisher.
  - For a Sigstore signature: the signer's OpenID Connect (OIDC) identity and its issuer, the identity provider. The identity is an email address, or a workload identity such as a continuous integration (CI) workflow for automated signing. Issuers include `https://accounts.google.com` and the GitHub Actions issuer, `https://token.actions.githubusercontent.com`.[^1, 3]
  - For a key signature: the publisher's public key.
  - For a certificate signature: the publisher's certificate chain.
- **Python 3.9 or later**, which the 1.1.1 release requires.[^2]

## Step 1: Install a pinned release

Install one exact version, then check the version the tool reports.

```bash
pip install model-signing==1.1.1
model_signing --version
```

Version 1.1.1 spells several flags with underscores, such as `--identity_provider`.[^3] An unreleased change switches to hyphens and keeps accepting the underscore forms.[^7] Commands written for a later release may therefore fail on 1.1.1. Follow the README at the tag of your release.[^1]

- [ ] Install the release in a fresh virtual environment and note its version
- [ ] Do not use a release older than 1.0.1: the changelog says earlier command-line scripts could report a pass and exit with a success code after verification failed[^7]

## Step 2: Verify against the signer you expect

With Sigstore, the signer uses a short-lived certificate for its OIDC identity. The signing event is recorded in a public, append-only transparency log.[^1, 9] The identity and issuer are required arguments, and verification fails if they do not match the signature.[^3]

```bash
model_signing verify path/to/model \
  --signature model.sig \
  --identity "$EXPECTED_IDENTITY" \
  --identity_provider "$EXPECTED_ISSUER"
```

For a key signature, pass the publisher's public key, which is your only link to the publisher.[^3]

```bash
model_signing verify key path/to/model \
  --signature model.sig \
  --public_key publisher.pub
```

For a certificate signature, you must identify the signer yourself, because the command checks the chain but takes no expected signer name.[^3] Without `--certificate_chain`, it falls back to a default set of root certificates.[^4] Version 1.1.1 accepts some certificates whose extended key usage field does not permit code signing, such as certificates issued for web servers. The fix has not been released.[^7] Pass the publisher's own chain, and identify the signer by confirming the signing certificate's SHA-256 fingerprint with the publisher; `--log_fingerprints` logs it.[^3]

```bash
model_signing verify certificate path/to/model \
  --signature model.sig \
  --certificate_chain publisher-chain.pem \
  --log_fingerprints
```

- [ ] The expected signer came from the publisher's own channel
- [ ] The command ran without `--ignore-paths`, `--ignore_unsigned_files` or `--allow_symlinks`, which step 3 explains
- [ ] The command ran without `--use_staging`; the project describes Sigstore's staging instance as being for test-only signatures[^3]

## Step 3: Read what the result covers

Read the output: the command prints `Verification succeeded`, or `Verification failed with error:` followed by the reason. On failure it exits with status 1.[^3] It hashes the directory and fails if a signed file has changed or is missing, or if an extra file is present. The error names the files.[^4]

A pass says nothing about skipped paths, which include Git-related files by default.[^1] Since version 1.1.0, a signature also records the paths the publisher excluded at signing, and verification skips them automatically.[^7] Two flags add to these: `--ignore-paths` skips paths you name, and `--ignore_unsigned_files` lets extra files pass.[^3, 7] Use them only for files your loader never reads.

Leave `--allow_symlinks` off. With it on, version 1.1.1 silently leaves every file under a symbolic link to a directory unsigned and unchecked. The changelog lists this flaw as fixed only in unreleased code.[^7]

To see what the signature covers, decode its signed statement with the jq tool:[^9]

```bash
jq -r .dsseEnvelope.payload model.sig | base64 -d | jq .
```

In the output, `predicate.resources` lists each covered file with its hash algorithm and digest (the hash value). The `predicate.serialization` field records the hashing settings, including any paths excluded at signing.[^6] A `predicateType` of `https://model_signing/Digests/v0.1` marks a pre-1.0 signature. The tool can verify such a signature but not create one, replicating version 0.2's experimental behavior "bug for bug," as the changelog puts it.[^6, 7]

- [ ] After a failure, every extra, missing or changed file is explained before anything is loaded
- [ ] Every file your loader reads appears in `predicate.resources`, and none sits in a skipped path
- [ ] The predicate type is `https://model_signing/signature/v1.0`, or the publisher has been asked to sign again

## Step 4: Check the transparency log entry

This step applies only to Sigstore signatures, which are recorded in Rekor, Sigstore's append-only transparency log.[^1, 11] The verify command has already checked the bundle's proof that the entry is in the log.[^1, 9] The bundle also holds the entry's log index and its integrated time, the time the log recorded the entry. A signed timestamp in the bundle shows that signing happened while the short-lived certificate was valid. Verification can therefore succeed after the certificate expires.[^9]

```bash
jq '.verificationMaterial.tlogEntries[] | {logIndex, integratedTime}' model.sig
rekor-cli get --rekor_server https://rekor.sigstore.dev --log-index <log-index>
```

The second command fetches the entry with the Rekor command-line client.[^10] The server it queries hosts Rekor's original log, which is still the default for Sigstore's public instance. The version 2 logs that ecosystems can opt into have other addresses.[^11, 12]

- [ ] The integrated time fits the release date the publisher gives
- [ ] Where your policy calls for an online check, the entry was fetched from the log by its index
- [ ] You know whether the publisher monitors the log for its signing identity, as the project advises signers to do[^1]

## Step 5: Record the result

Keep enough for an auditor to repeat the check.

- [ ] The bundle is stored with the model, the command, its output and the tool version
- [ ] The expected signer and the place you obtained it are written down
- [ ] The log index and the digests from the signed statement are saved
- [ ] The check is repeated whenever the files are copied or replaced

## Using the digests in an AI bill of materials

In May 2026, cybersecurity agencies of the Group of Seven (G7) countries published minimum elements for a software bill of materials (SBOM) for AI. They describe such an SBOM as a structured record of an AI system's components. For each model, the record should give a hash of the weights or model file and the hash algorithm, so that the component's integrity can be validated. The SBOM itself should carry a digital signature attributable to its author.[^13]

A verified model signature supplies such hashes from a known signer. Each entry in `predicate.resources` gives a file's algorithm and digest. The statement's subject carries one SHA-256 digest over all of them. The project intends that digest for referring to the model from other metadata documents.[^6] Copy these values into the model's SBOM entry. If an SBOM you receive gives a different digest for the same file and algorithm, it describes a different file from the one the publisher signed. The model signature ties the files to the publisher, while the SBOM's signature ties the inventory to its author. Our [brief on the minimum elements](/articles/g7-ai-sbom-minimum-elements/) covers the full list.

## A worked example

:::example Worked example (hypothetical): a summarization model for an internal tool
A team plans to serve an invented open-weight model, `summarizer-7b`, in an internal tool. The publisher's model card says each release is signed with Sigstore by `release@example.com` through Google's issuer, and the download includes `model.sig`. The team runs:

```bash
model_signing verify summarizer-7b \
  --signature model.sig \
  --identity "release@example.com" \
  --identity_provider "https://accounts.google.com"
```

1. The command fails and names one extra file, `handler.py`, which the team's serving framework would import. They delete it and ask the publisher why it was there, instead of rerunning with `--ignore_unsigned_files`.
2. The second run prints `Verification succeeded`.
3. The decoded statement uses the 1.0 predicate type and shows that the publisher excluded `README.md`, which the team's loader does not read.
4. The log entry's integrated time falls on the release date in the model card.
5. The team records the result as in step 5 and copies the weight files' digests into the model's SBOM entry.
:::

:::limits What a valid signature does not establish
- A passing check shows that the files have not changed since the holder of the expected identity or key signed them. It does not show that the weights are safe, unpoisoned or free of backdoors. A publisher can sign a compromised model as easily as a clean one.
- Inspection may not reveal a backdoor. Goldwasser, Kim, Vaikuntanathan and Zamir show how a malicious learner can plant a backdoor in a classifier that no observer with limited computing power can detect without the backdoor key.[^14]
- Further training may not remove one. Hubinger and colleagues trained language models to write secure code when a prompt states that the year is 2023, and exploitable code when it states 2024. They found that such backdoors can be made to persist through supervised fine-tuning, reinforcement learning and adversarial training.[^15]
- The check does not cover files outside the signed list, the code that loads the model or any model that someone else serves.
- If the publisher's account, CI workflow or key is compromised, an attacker's signature verifies too. For Sigstore signatures, a publisher that monitors the log for its identity can spot such a signature.[^1]
:::
