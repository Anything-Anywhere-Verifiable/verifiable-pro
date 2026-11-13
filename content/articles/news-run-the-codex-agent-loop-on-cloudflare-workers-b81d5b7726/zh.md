---
title: "Cloudflare 发布在 Workers 上运行 Codex 智能体循环的实验示例"
dek: "该 Agents SDK 示例记录已完成的模型调用和工具执行结果，以便重启后恢复。被中断的步骤可能重新执行，因此部署身份与恢复行为是核查重点。"
---

Cloudflare 于 2026 年 11 月 9 日发布一个实验性的 Agents SDK 示例，将 Codex 智能体循环运行在 Cloudflare Durable Object 中。该公司称，对话、文件以及已完成的模型调用和工具执行结果可在重启后保留，使智能体能在中断后恢复。示例将 Codex 的 Rust 轮次处理代码适配为 WebAssembly，并使用 Agents SDK 的存储与恢复能力。[^1]

公告介绍了四个组件。Tasks 记录模型调用和工具执行：重启后，已完成的步骤复用记录中的结果，被中断的步骤则可能再次运行。Sessions 存储对话历史并压缩模型上下文；Streams 存储有序事件，供重新连接后回放；Workspace 提供读写持久化文件的工具。因此，理解这项恢复能力时，关键是区分已完成的工作与被中断的工作。[^1]

配置示例通过 `createAI` 和 AI Gateway 接入 OpenAI 的 GPT-6.1 Sol，并通过 Lifecycle 安装 Tasks、Streams、Sessions 和 Codex harness。Cloudflare 表示，使用该模型需要为默认网关配置 Unified Billing，或存储 OpenAI API 密钥。公告还引导读者查阅另一份 harness 指南，了解设置、模型、工具及恢复行为；本次阅读未涵盖该指南。[^1]

:::analysis
这项主张涉及 T5（智能体）和 T2（运行时）：前者对应模型与工具步骤，后者对应持久化和恢复；读者仍需信任具体实现能兑现所述行为。这里需要核查的属性是**可识别性**：如果服务某位用户的确切版本与配置有记录且可核查，该用户就能判断自己是否接触过相关部署及其恢复行为。用户和运营方应核对部署记录、模型与网关配置，并检查自己的工具如何处理被中断后再次运行的步骤；公告没有指定修复版本，也没有提出安全补救措施。[^1]
:::

:::checked
我们于 2026 年 11 月 12 日阅读了 Cloudflare 官方更新日志《Run the Codex agent loop on Cloudflare Workers》的保存文本，该文发表于 2026 年 11 月 9 日。本次阅读确认了 Cloudflare 公告的内容，包括示例的实验性质及其恢复能力主张。我们没有检查链接中的代码或指南，没有部署示例，也没有测试持久化、事件回放或工具重复执行。[^1]
:::

[^1]: Cloudflare，《Run the Codex agent loop on Cloudflare Workers》，2026 年 11 月 9 日。https://developers.cloudflare.com/changelog/post/2026-11-09-codex-harness/
