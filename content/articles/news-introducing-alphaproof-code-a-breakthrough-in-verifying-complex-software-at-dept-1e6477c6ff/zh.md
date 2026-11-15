---
title: "Google DeepMind 称 AlphaProof Code 已对 Signal 核心密码代码完成形式化验证"
dek: "公告称，AI 生成的数学证明经 Lean 检查，覆盖指定的安全性质，但未说明具体验证结果对应哪些已部署版本。"
---

Google DeepMind 于 2026 年 11 月 10 日公布 AlphaProof Code，称研究人员使用这一多模型智能体框架，对 Signal 核心密码实现的关键安全性质进行了形式化验证。公司表示，数学证明深入到编译后的代码，覆盖设备遭到短暂入侵前后的消息保护性质。这些是公告中的研究主张，我们并未独立复现相关结果。[^1]

据 DeepMind 介绍，人类专家与模型合作，将安全目标转化为数学规约，并逐一审核。随后，由 Gemini Carbon 驱动的智能体生成了超过 600 万行 Lean 代码。公告称，Lean 检查数学证明，智能体则将代码库中百分之一的内容标记出来，交由人类进一步复核。DeepMind 报告称，验证过程耗时四周。[^1]

公司还表示，研究人员在隔离的 Signal 代码版本中重新引入了两个此前已修复的缺陷，两次实验都生成了经过机器检查、表明修改后版本不安全的数学证明。公司称将开源验证产物；但这份保存的公告未给出经过验证的准确发布版本标识、部署配置，也未推荐某个修复版本。[^1]

:::analysis
这一主张涉及 T5（智能体）、T4（输出）和 T2（运行时）：智能体构造数学证明，Lean 检查这些输出，所宣称的结果则针对实现代码。核验者仍需判断，经人类审核的规约是否准确表达了预期保护，以及接受检查的代码是否对应实际部署的系统；仅阅读公告无法确认这两点。[^1] 这里关系到的可核验性质是**可识别性（identifiability）**：如果为用户提供服务的准确版本和配置有记录且可核查，用户就能判断自己是否曾受相关实现问题影响。因此，用户和运营方应先核实这种对应关系，再将研究结果用于评估自身系统；该来源没有提供针对具体版本的修复指引。[^1]
:::

:::checked
我们于 2026 年 11 月 13 日阅读了 Google DeepMind 公告《Introducing AlphaProof Code: a breakthrough in verifying complex software at depth》的保存文本，其发布日期为 2026 年 11 月 10 日。我们没有阅读所链接的技术论文或验证产物，没有运行 Lean、检查 Signal 构建版本，也没有测试该系统。本次核查仅确认公告报告了哪些内容，未确认其数学证明的正确性或对实际部署版本的覆盖范围。[^1]
:::

[^1]: Google DeepMind，《Introducing AlphaProof Code: a breakthrough in verifying complex software at depth》，2026 年 11 月 10 日。https://deepmind.google/blog/introducing-alphaproof-code/
