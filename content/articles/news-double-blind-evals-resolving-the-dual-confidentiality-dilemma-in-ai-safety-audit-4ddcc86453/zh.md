---
title: "Double Blind Evals 作者报告双向保密的 AI 安全评估试点"
dek: "一篇 arXiv 预印本介绍了利用 NVIDIA H100 安全飞地和 PySyft，以 AILuminate 私有提示词评估 Gemini 2.5 Flash Lite 的试点。保存的摘要声称实现了双向保密，但其保证尚未得到独立核实。"
---

Andrew Trask 及合作者于 2026 年 11 月 9 日向 arXiv 提交了预印本 *Double Blind Evals: Resolving the Dual Confidentiality Dilemma in AI Safety Auditing*。论文报告了一项试点，目标是在不向模型所有者透露评估提示词的同时，保护专有模型权重和推理代码的机密性。[^1]

摘要描述了双方的保密需求：评估方希望提示词保持秘密，避免有意或无意的数据泄漏，延长基准的使用寿命；模型所有者则希望权重和推理代码留在自己的安全基础设施内。作者提出使用安全飞地，并将其描述为在硬件层面对 RAM 中的数据进行加密的机制。[^1]

作者称，试点使用 AILuminate 私有基准语料中的一部分，评估了 Google DeepMind 的 Gemini 2.5 Flash Lite。摘要列出的组件包括 Google Cloud Platform 上的 NVIDIA H100 安全飞地，以及 OpenMined 的 PySyft。作者声称，该方案为提示词保密提供密码学保证，同时保护权重和推理代码，并将试点称为首例。这些均为作者的主张；保存的摘要没有给出评估分数、详细威胁模型或独立验证结果。[^1]

:::analysis
这项主张涉及 T6 评估层、T2 运行时层和 T1 硬件层：对审计保密性的信任，取决于评估安排、软件及飞地机制，而保密本身不能确立模型的安全性。用户和运营方应寻求可核查的记录，将自己的评估或服务会话与确切的模型、软件版本和飞地配置对应起来；保存的摘要列出了组件，但没有提供修复版本或配置核查清单。这里涉及的可核验属性是可识别性：如果为用户提供服务的确切版本与配置有记录且可核查，用户就能判断自己是否接触过所讨论的部署；摘要并未确立系统已经具备这一能力。[^1]
:::

:::checked
我们于 2026 年 11 月 13 日阅读了保存的 arXiv:2611.12604 摘要页文本，其提交历史标明了 v1。此次阅读确认了页面所报告的内容，包括提交日期和试点所用组件。我们没有阅读全文、检查代码或远程证明证据，也没有测试系统；因此无法独立确认其保密性主张或首创性主张。[^1]
:::

[^1]: *Double Blind Evals: Resolving the Dual Confidentiality Dilemma in AI Safety Auditing*。arXiv，2026 年 11 月 9 日。https://arxiv.org/abs/2611.12604
