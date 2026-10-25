---
title: Google DeepMind 在安全飞地中试行 Gemini 模型双盲评测
dek: Google DeepMind 于 2026 年 8 月 27 日表示，外部评测方已在一个硬件隔离的飞地中，用保密的安全测试提示词评测了 Gemini 2.5 Flash-Lite；飞地的设计目标是让双方都看不到对方的资产。随附的技术报告也列出了这套方案在哪些方面仍需信任 Google。
---
Google DeepMind 于 2026 年 8 月 27 日表示，它试行了一次双盲评测，并称这是首次对专有前沿级模型开展此类评测。合作方为新加坡 AI 安全研究所、OpenMined、AI Verification and Evaluation Research Institute（AVERI）和 MLCommons。[^1] DeepMind 称，Google Cloud 的 Confidential Space 让评测方看不到 Gemini 的权重，也让 Google 看不到评测方的测试提示词。[^1]

技术报告写明，受测模型是 Gemini 2.5 Flash-Lite。模型部署在一台 Google Cloud 虚拟机上，这台虚拟机采用 Intel Trust Domain Extensions（TDX）内存加密，并配有一块以机密模式运行的 NVIDIA H100 GPU。OpenMined 的 PySyft 软件只运行双方都批准过的代码。双方在送入各自的资产之前，都检查了飞地的远程证明，即飞地就其已加载的软件给出的签名证据。[^2]

其中一项评测由 MLCommons 提供提示词，取自其 AILuminate 安全基准的一个保留题集，Google DeepMind 的任何模型都没有见过这些题目。[^2, 4] AVERI 先对提示词加密，评测随后在 Google 配置的飞地中运行。运行结束后，AVERI 对解密后的输出评分，并以保密方式向 Google DeepMind 报告。[^3]另一项评测与新加坡 AI 安全研究所合作，使用一组非公开提示词，内容涉及新加坡语境下的有害内容。技术报告和 AVERI 的文章都没有公布基准分数。[^2, 3]

报告也说明了局限：Gemini 的推理代码并非全部可供检查，也不能全部限定在只含经批准操作的允许列表之内。报告称，AVERI 是在知情的前提下接受这一设置的。客户机操作系统的源代码是公开的，但构建时需要输入私有签名密钥，因此无法由他人独立复现。证明报告由 Google 的服务签名和验证，作者称这让 Google 处在验证路径上。[^2] AVERI 写道，这一设计应对了开发者理论上可能篡改评测的许多途径，但并非全部。AVERI 还表示，在信任程度更低的场景下，例如核查国际协议时，需要更多保证。[^3]

:::analysis
这次试点展示了一种做法：双方都不必交出自己的资产，就能用保密基准测试专有权重。这直接应对了基准测试污染问题，即基准的测试题目出现在模型的训练数据中。提示词的保密性依赖经过远程证明的软件和硬件厂商，在这次试点中还依赖 Google：它的推理代码有一部分无法检查，远程证明也由它的服务验证。由于受评测的公司还负责配置飞地，独立的远程证明核查和可复现构建可以减少这种保密性对 Google 的依赖。
:::

:::checked
我们于 2026 年 10 月 20 日阅读了 Google DeepMind 的文章及其链接的技术报告、AVERI 的试点报告和 MLCommons 的文章。我们没有检查飞地、其证明证据或 PySyft 代码，也看不到 AVERI 交给 Google DeepMind 的结果。技术报告给出了两个不同的 AILuminate 版本，因此我们没有写明版本。
:::
