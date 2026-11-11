---
title: "Cymulate 报告称，智能体攻击链可延伸至 Azure 和 GCP"
dek: "两条演示攻击链将恶意输入、跨用户入侵与云凭据串联起来。保存的文章未列出修复版本号。"
---

Cymulate 于 2026 年 11 月 3 日发布研究综述，称其构建的两条智能体攻击链最终触及了具有高权限的 Azure 和 Google Cloud Platform（GCP）身份。文章由 Ben Zamir 撰写，概述了他在 SecTor 2026 的报告。演示场景以多人共用 Windows 主机、智能体连接企业账号为前提；文中描述的是研究演示，并非客户组织遭入侵的证据。[^1]

第一条链中，Cymulate 称，恶意网页诱导 AWS Kiro 写入执行配置，从而获得一名用户的代码执行权限。随后，攻击者利用 Codex CLI 权限宽松的命名管道和配置缺陷，窃取另一名用户的 OpenAI 令牌。研究人员描述了如何借此身份修改共享 Codex 云环境，再通过环境初始化脚本收集 QA 工作流中的秘密信息，其中包括具有广泛权限的 Azure 应用注册凭据。[^1]

第二条链据称始于遭投毒的 README，它诱导 Cursor CLI 在项目目录写入可执行文件。攻击者利用可执行文件搜索顺序和机器级配置实现跨用户执行，再通过修改后的代码仓库植入程序，使 Gemini CLI 在启动沙箱之前就在主机上运行该程序。文章还描述了 Google OAuth 凭据暴露。Cymulate 称，AWS 已修复 Kiro 的 CVE-2026-10591，而 Cursor 的初始执行问题在撰文时仍未解决。这些是作者报告的修复状态，保存文本未提供修复版本号。[^1]

:::analysis
问题位于 T5（agents，智能体层）和 T2（runtime，运行时层）：前者涉及不可信内容如何转化为受委托的操作，后者涉及程序搜索、配置权限和本地通信如何决定操作使用谁的权限。仅阅读这份报告，用户仍需信任作者对演示和修复状态的陈述。这里可核验的关键属性是**可识别性（identifiability）**：如果为用户提供服务的确切版本与配置有记录且可检查，用户就能判断自己是否曾处于受影响范围。用户和运营方应将这些记录与文中的 Windows 条件逐项对照，检查共享配置和云环境初始化脚本，并确认所部署版本的修复情况；这份保存来源没有给出可直接对照的修复版本号。[^1]
:::

:::checked
我们于 2026 年 11 月 11 日阅读了所提供的 Cymulate 文章《Across the Kill Chain: How Agents Became the Enterprise's New Front Door》保存副本，其发布日期为 2026 年 11 月 3 日。副本在第二条攻击链的描述中途结束，末句不完整。我们没有打开文中链接的研究文章，没有测试任何系统、复现攻击或独立核实修复情况。本次检查所能确认的是保存文本报告了哪些内容。[^1]
:::

[^1]: Cymulate，《Across the Kill Chain: How Agents Became the Enterprise's New Front Door》，2026 年 11 月 3 日。https://cymulate.com/blog/ai-agent-security-kill-chains/
