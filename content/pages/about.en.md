---
title: About verifiable.pro
dek: What we cover, how we check it, and how you can check our work.
published: 2026-10-20
updated: 2026-10-31
changes:
  - 2026-10-31 | Clarified the publication scope and added direct links to the lab, editor and learning guides.
---
## What verifiable.pro publishes {#overview}

verifiable.pro is an English and Simplified Chinese publication on verifiable AI, maintained by [SEPT Lab at the University of Southern California](https://septlab.com/) and edited by [Mengyuan Li](https://mengyuanli.com/). We publish news, explainers, comparisons and practical guides to the evidence behind claims about model identity, data privacy and agent behavior. Our coverage starts from trusted execution environments (TEEs) and remote attestation, and compares them with proofs, re-execution, audits and provenance. [Start learning about verifiable AI](/learn/#start-here). This page explains how we work. [What verifiable.pro is for](/vision/) sets out the site's focus and goals.

## What we report, and how {#coverage}

We cover a development when it changes what an outsider can check about an AI system. We skip announcements that do not.

A news brief is written from the primary source: the organization's own announcement, paper, standard or documentation. If a brief has to rely on another outlet's reporting, it names that outlet. Analysis pieces build an argument from cited evidence and keep our interpretation in a separate "Why it matters" box. Explainers set out a concept and what it leaves to trust. Guides turn a check into numbered steps with a worksheet.

Each item carries a "Filed" date, the day it appeared on verifiable.pro. News briefs also carry a "Source date", the date on the primary source. So a brief filed today about a standard published last month shows both dates.

Invented scenarios sit in a hatched *Worked example* box, so they cannot be mistaken for reporting. Our pictures carry no evidence either; the evidence for a story is in its sources. The drawing on the home page is a conceptual picture made for this site, and it depicts no real person, product, system or event. The labels beside it show the logos and names of real companies, products and institutions as examples at each layer, not as endorsements. The pictures that open our articles are usually real photographs. When a photo shows a stand-in for the story's subject, such as a data center, its caption says what the photo does not show. [How we choose photos and make illustrations](#illustrations) explains where the photos come from and how we prepare them. When an article has a photo, its link preview shows that photo. Other link previews use generated cards that pair a title with a pattern, and our pages do not show those cards.

## How we check claims {#verification}

Every news brief ends with a "What we checked" box. It names the primary sources we opened, the day we opened them, and what we could not confirm.

We report a vendor's security claim as the vendor's claim. When a company calls its service "attested" or "private", the word tells readers what the company says, and our wording keeps that distinction.

We also separate what a mechanism protects from what it establishes. A TEE is designed to isolate the software running inside it. A remote attestation report is evidence about which software was loaded. Neither shows that the software behaves correctly. When a story depends on such a boundary, the analysis states it, often in a "What this does not show" box.

## How you can check our pages {#integrity}

A site about verification should let readers check its own text. Each article is a plain-text Markdown file. The build computes the SHA-256 digest of every source file. A digest is a short fingerprint of a file's exact contents. Each article shows its digest in the Verification record at the end of the article. The [site manifest](/manifest.json), a list of every source file, also records the digest, together with the address of the source file. The manifest's own digest is its `digest` field, and the footer links to the manifest.

To check that an article's published source matches its recorded digest, download the source and compute its digest:

```bash
curl -s https://verifiable.pro/articles/<slug>/en.md | shasum -a 256
```

The result should equal the digest in the article's Verification record and the matching entry in the manifest. To check every entry at once, run `python3 tools/verify_manifest.py https://verifiable.pro` from a copy of the site's source repository.

A match shows that the text you received is the text the site recorded at build time. It does not show that the reporting is correct. It also cannot reveal an earlier version that was replaced before the build. That is why corrections are also recorded in the article itself.

## How we use AI tools {#ai}

Software built on Anthropic's Claude models drafts our articles. Every day it scans primary sources and drafts news briefs about the developments it finds; the briefs appear under the byline verifiable.pro Wire. Explainers, analysis and guides, which it drafts after studying the sources on a subject, appear under verifiable.pro Research. AI tools also translate between English and Chinese, and they help choose and caption the pictures that open our articles.

Each article's byline says who drafted it. The software's two bylines carry an "Automated" tag, so readers can tell them from a person's byline, which reads "By" and the person's name. When someone submits a story and gives a name to credit, the byline also says "Submitted by" and that name.

The editor decides which drafts are published and is responsible for every article. Before publication, the editor checks each factual claim against its cited source. An article about a company whose AI tools we use carries a disclosure.

## How we choose photos and make illustrations {#illustrations}

Every news brief opens with a lead picture, usually a real photograph. Other articles may have one too. We use photos only from sources whose licenses allow reuse: Wikimedia Commons, US government sites and the photo libraries Unsplash and Pexels. The licenses are CC0, CC BY, CC BY-SA, Unsplash's and Pexels' own licenses, and the public domain, which covers the works of the US federal government. The credit line under every photo names its author and its source and links its license and its source page. Where the license asks that changes be indicated, the credit line also says that we cropped the photo and adjusted its colors.

When we find no photo of a story's own subject, we use a stand-in that shows the kind of thing the story concerns, such as a data center or a chip, and its caption says what the photo does not show. A caption gives only what the source says about the photo, so we never add a name, a place or a date. A photo is never an AI-generated image or a composite of different scenes or subjects, and we never change what it shows. A focus stack, which merges frames of a single subject taken at different focus distances so that all of it is sharp, counts as a photograph. `tools/photos.py` in the site's source repository crops every photo to the same 3:2 frame and gives all of them one gentle color grade, slightly lower saturation and contrast with a faint warm tone, so that they read as one series. It also removes the metadata that cameras record, such as the location. AI tools help us find candidate photos and draft their alt text and captions, and the editor checks each photo, its license and its texts before publication.

Each photo's details are published beside its article as `illustration.json`: the credit, the license, the source and the day we downloaded it, the crop and the grade, and the SHA-256 digests of the published files, which the [site manifest](/manifest.json) also lists. A matching digest shows that a file is the one the site recorded when it was built. It does not show that the reporting is correct.

An article can also open with a conceptual illustration, drawn by code from a published scene description. The site's generator, `tools/illustrate.py`, turns the scene description into an SVG picture in the style of the home page drawing, and the description is published beside the article as `illustration.json`. We draft scene descriptions, alt text and captions with help from Anthropic's Claude models, and the editor checks each picture and its texts before publication.

Anyone can draw an illustration again and compare it with the published one. Each scene description records the SHA-256 digest of the picture drawn from it, and the site manifest lists the digests of the description and the picture. From a copy of the site's source repository, at the commit that `/build.json` names, draw a published description again and compute the digest of the result:

```bash
curl -s https://verifiable.pro/articles/<slug>/illustration.json -o illustration.json
python3 tools/illustrate.py --spec illustration.json --out redrawn.svg
shasum -a 256 redrawn.svg
```

The result should equal the digest recorded in the description and the picture's entry in the manifest. `python3 tools/illustrate.py --check` draws every picture in the repository again and reports any that differ. A match shows that the picture is what the code draws from that description. It does not show that the reporting is correct.

The illustrations do not depict real events, people or products. They show the parts of an AI system that a story concerns, such as hardware, software or a check, as generic shapes, and each caption says what its picture does not show. The evidence for a story is in its sources, not in its picture.

## The assistant {#assistant}

Pages on verifiable.pro have an "Ask" button in the header. It opens a small assistant for questions about our coverage. The assistant answers from passages of this site's own published pages and data. Each answer lists the pages it drew on, so you can open the source and compare.

The assistant runs in demo mode today. Your browser searches the site's published index and assembles an answer from the passages that match. No language model is involved, and nothing you type is sent anywhere: the question stays in the page, and the conversation is kept only in this browser tab until you close it. Demo answers are extracts from our pages, labeled as demo answers.

An answer is only as good as the passages it quotes, and the assistant can pick the wrong ones. It does not check claims for you, and it is not a source. Cite the articles and their primary sources instead. Demo answers come with no attestation of any kind.

We plan to run the assistant on a language model inside GPU confidential computing. In that setup, the model runs in an environment that the hardware is designed to isolate from the host and the cloud operator. The hardware also signs an attestation report on the software and settings it loaded. Your browser will still choose the passages from the site's published files. So the service receives only your question, the earlier turns of the conversation, the address of the page you asked from and those passages. Like any web service, it also sees the network address a request comes from.

Your browser will fetch the attestation report and check what it can on its own. It will then show which of the service's statements about its environment it checked, and which ones the service only reports. Until such checks run in your browser, the assistant shows the service's claims as reported, never as verified. Even a checked attestation report shows only which software the answering environment loaded. It does not show that the answer is correct.

## What the resource library includes {#resources}

The resource library lists papers, standards, specifications, tools, benchmarks and organizations. An entry is included because it helps someone check a claim about an AI system. Listing an entry is not an endorsement or a certification. The "Link checked" date records when we last opened the link. If the editor builds or co-authors a listed project, its entry says so and marks it as a maintainer project.

## Who edits verifiable.pro {#editor}

verifiable.pro is maintained by [SEPT Lab at USC](https://septlab.com/) and edited by [**Mengyuan Li**](https://mengyuanli.com/). The site takes no payment for coverage and certifies nothing. A story here is reporting, not an attestation about the systems it describes.

## Corrections {#corrections}

Tell us the sentence that is wrong and the primary source that contradicts it. You can do this in public or privately. In public, open a correction issue (a report that anyone can read) in the site's [source repository](https://github.com/Anything-Anywhere-Verifiable/verifiable-pro). Privately, email the address below. Each article ends with a "Check or correct this page" box that opens such an issue with the page address filled in. When we confirm an error, we fix the article, change its "Updated" date and list the correction, with its date, at the end of the article. The fix also changes the article's source digest.

## Contributing {#contribute}

The site's text, data and code live in a public [GitHub repository](https://github.com/Anything-Anywhere-Verifiable/verifiable-pro). An issue there is the preferred route for suggesting a story, a source, a resource for the library or a glossary term. We also welcome pull requests (proposed edits) that change the Markdown sources. The repository's [contribution guide](https://github.com/Anything-Anywhere-Verifiable/verifiable-pro/blob/main/CONTRIBUTING.md) explains the steps and the review rules. If you prefer email, send the link and a sentence or two on what it lets someone check. Write in English or Chinese.

## Related publications {#related}

[Audit Commons](https://auditcommons.org/) is an editorial site on AI auditing. Its subject is adjacent to ours: it follows how AI systems are audited, while verifiable.pro follows the evidence that lets an outsider check a claim about an AI system.

## Contact {#contact}

Write to the editor: hello@verifiable.pro

## Reuse {#license}

The site's original text, data files and illustrations are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). You may copy, adapt and republish them, including commercially, if you credit verifiable.pro, link the page you used and say whether you changed it. The code that builds the site is under the [MIT License](https://github.com/Anything-Anywhere-Verifiable/verifiable-pro/blob/main/LICENSE). Quoted material, other organizations' logos and linked sources stay under their owners' terms, and each photo stays under the license that its credit line names.
