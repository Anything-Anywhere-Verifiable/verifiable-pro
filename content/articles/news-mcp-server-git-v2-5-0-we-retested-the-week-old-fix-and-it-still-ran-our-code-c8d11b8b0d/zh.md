---
title: "AgentStack 称此前修复版 MCP Git 服务器仍可执行代码"
dek: "AgentStack 称，其测试在 mcp-server-git 2026.11.11 中发现两条代码执行路径和一处仓库外文件读取问题，并建议升级至 2026.11.18。"
---

2026 年 11 月 19 日，AgentStack 报道称，其测试发现，mcp-server-git 一周前发布的安全更新仍会运行仓库提供的代码。该媒体称，Model Context Protocol（MCP）参考服务器的 v2.5.0 版本修复了 Git 服务器中的另外六项漏洞，以及其他参考服务器中的两项问题。[^1]

AgentStack 称，它通过标准输入输出使用 MCP 客户端，测试了 mcp-server-git 2026.11.11 和 2026.11.18。据其报道，在旧版本中，仓库设置分别使一次 `git_merge` 调用和一次只读的 `git_show` 调用运行了用于标记的命令。一个经过构造的 Git 索引还使 `git_diff_unstaged` 返回了配置的仓库边界之外的文件。AgentStack 称，新版本在其测试中拒绝了这三条路径；其余三项 Git 问题则未被复现。[^1]

该媒体报道，11 月 19 日，六项 Git 安全公告尚未收录到 OSV.dev，其针对受影响版本运行的 `pip-audit` 扫描也没有报告问题。这是当日的观察，不能说明数据库目前的状态。AgentStack 建议将 mcp-server-git 升级至 2026.11.18、filesystem 服务器升级至 2.4.0，everything 服务器升级至 2.3.1。[^1]

:::analysis
这个问题涉及智能体层（T5）和运行时层（T2）：前者是智能体调用仓库工具的地方，后者是 Git 处理仓库配置和文件的地方。工具带有只读标签，单凭这一点不能确认调用不会执行仓库提供的代码；用户和运营者需要掌握实际提供服务的版本和配置。这里涉及的可核查属性是可识别性：如果为某个用户提供服务的确切版本和配置有记录且可供检查，该用户就可以判断自己是否曾暴露于受影响的配置。运营者应核对实际运行的软件包版本，包括缓存副本，并与建议的修复版本比较；还应将仓库视为不可信内容。报道中的测试不能确认其他所有路径都是安全的。[^1]
:::

:::checked
我们于 2026 年 11 月 25 日阅读了保存的 AgentStack 文章 [“mcp-server-git v2.5.0: We Retested the Week-Old Fix, and It Still Ran Our Code”](https://agentopsguide.com/mcp-server-git-v2-5-0-vulnerabilities/)。[^1] 我们没有独立查阅文中提及的发布说明或安全公告，也没有测试该系统或独立确认其测试结果。
:::
