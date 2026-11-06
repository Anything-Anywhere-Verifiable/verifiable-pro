# Wave editorial and figure provenance

The bilingual `wave-gpu-model-oversight` explainer is an editor-requested research
article prepared on 2026-11-06 through the existing daily editorial pipeline.
It remains a draft pending editorial approval. The `pipeline-research` byline
describes its actual use of OpenAI Codex. This work did not change scheduled
news discovery or use its single-source news publisher.

## Sources and scope

- [Author-hosted paper](https://terryxu.site/assets/pdf/wave-asplos26.pdf).
- [Artifact revision reviewed](https://github.com/sept-usc/Wave/tree/29773cdce6bf06313dc340bce5df86d920e2ed21).
- [Publisher record](https://doi.org/10.1145/3779212.3790247).

Mengyuan Li co-authored Wave; the article discloses that relationship. Review
included the analyzer and solver entry points, experiment thresholds, dataset
counts and source limitations. Replaying the bundled overhead logs and plotting
committed CSV rows did not collect new GPU measurements or rerun the full solver
suite. The article distinguishes authenticated measurements assumed by the
design from the released Nsight Compute prototype.

## Pipeline and editorial review

Run `wave-editorial-20261106` invoked `pipeline.agents.call_agent('codex')` through
`Store.step` with a source packet and the paper's full extracted text. The raw
generated response is retained in the private pipeline run. Subsequent review
shortened the titles, corrected GEMM terminology, expanded an abbreviation and
integrated original figures with native video controls. A final self-contained
bilingual preview, exact file hashes and original model provenance are retained
in the pipeline review bundle. Pipeline logs and paper text are not published
with this repository.

## Original figures

Assets live under `static/figures/`:

| Basename | Content and formats |
| --- | --- |
| `wave-observation` | Original 12-second conceptual workflow; MP4, GIF, PNG, SVG, Excalidraw |
| `wave-bounds` | Original 16-second toy counterexample search; MP4, GIF, PNG, SVG, Excalidraw |
| `wave-observed-flops` | Plot of bundled RTX 5080 Q and FFN-up kernel observations; SVG, PNG, JSON data and input hashes |

The first two figures use schematic data; they are not recordings of actual
inference or solver runs. The third selects the unique Q and FFN1 rows from
the six-layer, batch-one motivating-example CSVs and compares them with `2d²`
and `8d²`. Both axes use logarithmic spacing. These points are per-layer
projections, not entire inference requests.

Original figure outputs are dual licensed MIT OR
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); captions use CC BY 4.0.
The renderer, editable specifications and third-party MIT attribution are
provided with the Wave repository's `docs/figures/` presentation update.
The figures were drawn from source-grounded facts and recorded data, without
copying or modifying paper images. The paper's separate license is not
relicensed by this article.

The videos are silent H.264/yuv420p, 1280×800 at 10 fps. They start paused,
have native controls, and offer static images, GIF downloads and editable
sources. No autoplay or new JavaScript is required. Figure explanations also
appear in the captions and article text.

## Validation

The site tests passed: 418 tests, with one existing environment-dependent skip.
The draft preview passed internal-link, accessibility and content-lint checks.
English and Chinese layouts were inspected at 390, 768 and 1440 pixels, including
reduced-motion preference, without horizontal overflow. The animation renderer
checked decoded GIF durations and changing frames, and fully decoded both MP4s.
Production builds were compared for determinism; the public build continues to
exclude the draft article until editorial approval removes its `draft` field.
