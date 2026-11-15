---
title: "CSA 警告 Claude Dispatch 可能让浏览器会话成为桌面命令通道"
dek: "CSA 研究说明梳理了一条据报可通过共享 Claude 会话、从浏览器扩展操控桌面的攻击路径。CSA 未复现该攻击，也未找到针对这一问题的已公开修复。"
---

Cloud Security Alliance（CSA）AI Safety Initiative 于 2026 年 11 月 7 日发布研究说明，分析 Anthropic 的 Claude Dispatch 中一个被称为 ThisBash 的据报设计弱点。说明称，能够在已登录的 claude.ai 页面中运行脚本的浏览器扩展，可利用该账户的已认证会话，向配对的 Claude Desktop 智能体发送指令，目标甚至可以是另一台电脑。CSA 明确表示，尚未独立复现这条攻击路径。[^1]

据说明对研究员 Gal Weizman 演示的转述，脚本先找到桌面智能体的会话，再提交指令并自动点击批准提示。随后，智能体安装了一个 npm 包，其 preinstall 钩子执行载荷，打开计算器应用。这条据报攻击路径直接使用用户已认证的命令通道，无须让智能体把恶意内容误当作指令。[^1]

CSA 称，Anthropic 接受了报告的有效性，但以重复问题为由将其关闭；尽管曾计划停用 Dispatch，该功能在 10 月下旬仍向现有用户开放。说明未找到针对这一问题的已公开厂商修复，也未列出修复版本，并称截至撰写时没有已知的实际在野利用。关于 Claude Cowork 和 Claude Code Remote Control 仍存在类似风险的说法，说明仍将其列为未经验证。[^1]

:::analysis
问题位于 T5 智能体层（agents）和 T2 运行时层（runtime）：共享会话把浏览器发出的请求接入本地执行权限，因此，账户认证和网页内的批准操作本身不足以确认用户亲自授权。这里涉及的可核验属性是可识别性：如果为用户提供服务的确切版本和配置有记录且可查，在受影响条件已经明确的前提下，用户就能判断自己是否曾处于风险之中。依据 CSA 的建议，用户和运营方应核查远程控制设置、跨设备账户共用情况、扩展权限及桌面智能体权限；Team 和 Enterprise 管理员还应检查“Chat and Cowork unified”设置，因为这份来源没有提供可供核对的修复版本。[^1]
:::

:::checked
我们于 2026 年 11 月 14 日阅读了 CSA 的《ThisBash: Browser Sessions as Remote Shells via Claude Dispatch》保存副本，该说明发表于 2026 年 11 月 7 日。我们没有打开其引用资料，也没有测试系统。此次阅读仅确认 CSA 报告了哪些情况、提出了哪些建议，并未独立确认攻击效果、功能当前是否可用或修复状态。[^1]
:::

[^1]: Cloud Security Alliance AI Safety Initiative，《ThisBash: Browser Sessions as Remote Shells via Claude Dispatch》，2026 年 11 月 7 日。https://labs.cloudsecurityalliance.org/research/csa-research-note-claude-dispatch-thisbash-20261107-csa-styl/
