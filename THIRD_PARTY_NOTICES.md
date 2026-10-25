# Third-party notices

The home page hero shows vendor marks beside its layer labels. Their path data is vendored in [`sitegen/logos.py`](sitegen/logos.py) from two icon sets and, for one mark, from Wikimedia Commons, and the build copies it into the two home pages. The licenses below cover that path data. The marks themselves are trademarks of their owners; the site shows them as examples of who works at each layer, not as endorsements.

## Lobe Icons

The marks for Microsoft Azure, DeepSeek, Qwen, Cursor, Manus, Model Context Protocol, vLLM, Claude Code, OpenAI Codex, Pi, Meta AI and Grok come from [Lobe Icons](https://github.com/lobehub/lobe-icons), version 1.98.0 of the npm package `@lobehub/icons-static-svg`. The package's `package.json` declares the MIT License, and the package ships no license file of its own. The notice below is the `LICENSE` file of the [lobehub/lobe-icons](https://github.com/lobehub/lobe-icons) repository, which publishes the package, as read on 23 October 2026. Keep it with these marks wherever they are copied.

```text
MIT License

Copyright (c) 2023 LobeHub

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Simple Icons

The other marks (NVIDIA, Intel, AMD, Arm, Google Cloud, AWS, Hugging Face, Google, OpenAI, Anthropic, Claude, Google Gemini, Meta, Mistral AI, GitHub Copilot, Apple, Qualcomm, European Union and TikTok) come from [Simple Icons](https://simpleicons.org) ([simple-icons/simple-icons](https://github.com/simple-icons/simple-icons)). Simple Icons dedicates its icons to the public domain under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/), which asks for no notice; this credit thanks the project.

## Wikimedia Commons

The mark for Muse, Meta's AI agent, comes from [File:Muse icon.svg](https://commons.wikimedia.org/wiki/File:Muse_icon.svg) on Wikimedia Commons, as read on 25 October 2026. The file page names Meta Platforms, Inc. as its author and <https://muse.ai> as its source, and marks the file as public domain because it is a simple text logo (PD-textlogo), with a trademark notice. A public-domain file asks for no notice; this entry records where the path data comes from. `sitegen/logos.py` scales the path from the file's 100-unit grid to the 24-unit grid of the other marks and draws it in one colour in place of the file's gradient.

## Adding a mark

A new mark from either set goes into the matching list above. A mark from any other source needs its license checked first, and its notice added here when the license asks for one.

## Lead photos

The notices above do not cover the photos that open the articles (`static/media/<slug>.webp` and its three copies). Each photo keeps its own license: its `content/articles/<slug>/illustration.json` names the license, the credit and the source page, and the credit line under the photo on the site links the license and the source. Under CC BY and CC BY-SA the credit line also says that the photo was cropped and color-adjusted, and a CC BY-SA photo stays under CC BY-SA.
