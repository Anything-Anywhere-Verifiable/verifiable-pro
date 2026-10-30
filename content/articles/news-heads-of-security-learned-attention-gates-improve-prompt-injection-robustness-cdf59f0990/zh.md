---
title: "Heads of Security 作者报告提示注入防御能力提升"
dek: "一篇 arXiv 预印本提出用学习得到的注意力门控区分指令与不可信数据。摘要报告了对自适应攻击更强的抵抗能力，但未确立任何已部署服务的防护效果。"
---

Igor Shilov 等九位作者于 2026 年 10 月 27 日向 arXiv 提交预印本 *Heads of Security: Learned Attention Gates Improve Prompt Injection Robustness*。论文提出 Heads of Security（HoS）：通过少量针对各注意力头学习得到的门控，将可信指令与不可信数据分开处理，以抵御提示注入。[^1]

据摘要介绍，这些门控学习如何在可信与不可信词元之间重新分配注意力。作者在 Llama-3.3-70B-Instruct 和 GPT-OSS-20B 上评估了 HoS，并与通过微调实现防御的 SecAlign++、通过模型架构实现防御的 ASIDE 进行了比较。[^1]

作者报告，黑盒攻击 RL-Hammer 对 GPT-OSS-20B 的攻击成功率（ASR）为 97%，对 SecAlign 为 85%，对 HoS 为 10%。摘要在介绍比较对象时使用“SecAlign++”，在报告这些结果时使用“SecAlign”；保存的页面没有解释这一名称差异。摘要还称，经过针对性调整的白盒攻击 Claudini，要在 HoS 上达到相同攻击成功率，所需浮点运算量是攻击 GPT-OSS-20B 或 SecAlign 时的三倍。[^1]

摘要称，HoS 在标准多项选择基准和不同提示设置下保留了基础模型的任务表现。在使用静态攻击的智能体基准中，作者报告 HoS 与 SecAlign 表现相近。这些均是作者报告的研究结果。[^1]

:::analysis
这项主张涉及 T6（evaluations，评估层）和 T3（models，模型层）：基准结果针对的是学习得到的模型干预机制，用户仍需信任实际提供服务的系统与评估设置相符。这里涉及的可核验属性是**可识别性**：如果为用户提供服务的确切版本和配置有记录且可查，用户就能判断自己是否曾使用所讨论的配置；这些记录本身并不确立抵御攻击的能力。用户和运营方应核对实际服务的模型、门控配置，以及可信与不可信词元的处理方式是否符合评估设置；保存的摘要没有指定修复版本或建议升级到的版本。[^1]
:::

:::checked
我们于 2026 年 10 月 29 日阅读了保存的 arXiv:2610.37657v1 摘要页面，包括提交历史。这次阅读确认了作者报告的内容及提交日期。我们没有阅读全文、检查代码、复现基准或测试系统；实际部署中的行为仍未得到确认。[^1]
:::

[^1]: [Heads of Security: Learned Attention Gates Improve Prompt Injection Robustness](https://arxiv.org/abs/2610.37657)，arXiv，2026 年 10 月 27 日。

主图： Igor Shilov, Xiaoxue Yang, Alexander Panfilov, Evgenii Kortukov, Matthieu Meeus, Peter Romov, Wojciech Samek, Jonas Geiping, Yves-Alexandre de Montjoye · CC BY 4.0。
