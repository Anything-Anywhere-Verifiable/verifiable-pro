---
title: "EasyProver 作者报告 Lean 数学证明结果，推出 Aegis 代码验证任务"
dek: "一篇 arXiv 投稿报告了现有基准上的较高成绩，以及源自实际实现的更难任务样本上 52.7% 的数学证明成功率。保存的摘要记录了这些主张，但不足以独立验证结果。"
---

2026 年 10 月 28 日，Debargha Ganguly 等九位作者向 arXiv 提交了论文 *Scaling Lean Theorem Proving for Real-World Code Verification*，介绍 Lean 数学证明系统 EasyProver，以及旨在从竞赛编程实现中构建更难验证任务的 Aegis 流水线。[^1]

作者称，EasyProver 结合了上下文隔离的递归智能体、异步搜索、并行策略探测和弹性 elaboration 服务。系统使用未经额外训练的现成前沿模型，据报完成了 PutnamBench 的 672 道题中的 669 道，以及全部六项 IMO 2026 形式化题目的数学证明。作者还称，系统通过数学证明或反驳，解决了 NTP4VC 的 600 个验证条件中的 597 个，以及全部 189 项 VERINA 任务；这些解决数量不能直接视为仅靠数学证明取得的成功率。[^1]

Aegis 编写安全 Rust 解决方案，通过 Aeneas 将其转换为 Lean，并生成规约。摘要称，冻结后的陈述会获得经过内核检查的数学证明或反驳，并报告生成了 2,045 对经过差分验证的 Rust–Lean 程序，以及 11,533 项候选规约。这些任务包含定长整数运算、显式失败、生成的循环、类型转换，以及将可变状态改写为函数式表达所带来的实现层验证义务。在分层抽取的 2,000 项陈述中，EasyProver 据报在每项 30 分钟的预算内完成了 1,054 项数学证明，比例为 52.7%。[^1]

:::analysis
这些主张涉及 T6 评估层、T5 智能体层和 T4 输出层：基准选择、数学证明搜索的编排，以及最终的形式化陈述，都会影响验证者可以信任什么。报告中的内核检查针对冻结后的陈述；用户和运营方还应核对，自身检查覆盖的是哪份实现、转换结果和规约。这里涉及的可验证属性是**可识别性**：如果向用户提供服务的确切版本和配置有记录且可核查，用户就能判断自己是否接触过所评估的系统设置；这份摘要没有提供部署记录、受影响版本范围或修复版本建议。[^1]
:::

:::checked
我们于 2026 年 11 月 6 日阅读了保存的 arXiv 摘要页文本，标题为 *Scaling Lean Theorem Proving for Real-World Code Verification*，页面标明其为 2026 年 10 月 28 日提交的 v1。我们没有阅读全文、检查代码或数学证明产物，也没有测试系统。这次阅读只能确认摘要报告了哪些内容，不能独立确认结果的可复现性或正确性。[^1]
:::

[^1]: Scaling Lean Theorem Proving for Real-World Code Verification。arXiv，2026 年 10 月 28 日。https://arxiv.org/abs/2610.38174

主图： Debargha Ganguly, Divya Raghunathan, Dejan Jovanović, Vikash Singh, Soonho Kong, Aaron Tomb, Aman Goel, Ferhat Erata, Sam Bayless · CC BY 4.0。
