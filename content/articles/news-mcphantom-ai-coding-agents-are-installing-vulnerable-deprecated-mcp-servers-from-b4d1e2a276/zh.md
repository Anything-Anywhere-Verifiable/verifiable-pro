---
title: "Glow Labs 称编程智能体会安装已弃用的 MCP 服务器"
dek: "Glow Labs 报告称，已停止维护的参考服务器存在四个高危漏洞。其发现提示，团队需要核查智能体实际在开发者机器上安装了哪些软件包，以及如何配置它们。"
---

Glow Labs 于 2026 年 11 月 2 日报告称，AI 编程智能体会在开发者机器上安装已弃用的模型上下文协议（MCP）服务器，可能引入已停止接收安全更新的软件漏洞。该公司将这一现象称为 McPhantom。[^1]

Glow 称，研究团队审阅了真实编程会话记录，并通过终端资产盘点发现了本地服务器。在涉及安装已弃用服务器的会话中，公司认为 98% 的软件包选择似乎源自模型训练数据；其余 2% 则是用户直接指定了已弃用的软件包。保存的文章没有给出会话总数，也没有提供可复现的方法来确认训练数据归因，因此读者难以评估这一解释。[^1]

该公司报告称，已弃用的 Anthropic 参考服务器存在四个高危漏洞，其中 Puppeteer 服务器存在远程代码执行漏洞。Glow 表示，攻击者可通过提示注入，让智能体利用原本用于浏览器操作的权限启动任意进程。据其转述，维护者因仓库已归档且不再维护而拒绝修复。Glow 称，截至报告时尚未发现这些漏洞被利用。[^1]

Glow 建议检查开发者机器上的 MCP 配置，找出已弃用的 `@modelcontextprotocol` 服务器；在有替代方案时，改用服务提供方维护的实现；每项服务统一批准一个服务器，并在批准前检查 npm 弃用状态。来源没有列出这些漏洞的修复版本，而是表示已归档的服务器不会获得修复。[^1]

:::analysis
问题位于 T5（agents，智能体）和 T2（runtime，运行时）：前者涉及软件选择与配置，后者涉及本地服务器进程执行；智能体选中某个软件包，本身不能作为它仍在维护的证据。这里需要核验的属性是可识别性：如果为用户提供服务的确切版本与配置有记录且可查，用户就能判断自己是否曾暴露于受影响的部署，但这并不表示漏洞已被利用。用户和运营方应按照来源的替换建议，核对终端配置、已安装版本、获批替代方案及 npm 弃用状态。[^1]
:::

:::checked
我们于 2026 年 11 月 11 日阅读了 Glow 文章《MCPhantom: AI Coding Agents Are Installing Vulnerable Deprecated MCP Servers from Training Data》的保存副本。这只能确认 Glow 报告了什么；我们没有测试系统、复现漏洞，也没有独立检查会话记录、软件包或维护者通信。来源日期采用所提供的发布时间戳，即 11 月 2 日，而非保存页面中同时出现的较晚日期。[^1]
:::

[^1]: Glow，《MCPhantom: AI Coding Agents Are Installing Vulnerable Deprecated MCP Servers from Training Data》，2026 年 11 月 2 日。https://www.glow.io/blogs/mcphantom-ai-coding-agents-are-installing-vulnerable-deprecated-mcp-servers-from-training-data
