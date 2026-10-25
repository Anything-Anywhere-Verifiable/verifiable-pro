---
title: Apple 称将把 Private Cloud Compute 扩展到 Google Cloud
dek: Apple 于 2026 年 6 月 8 日表示，新的 Apple Intelligence 工作负载将在 Google Cloud 硬件上运行，并受其 Private Cloud Compute 承诺约束。Apple 的发布说明称，其研究工具目前还无法解析这一新部署的证明报告。
---

Apple 于 2026 年 6 月 8 日表示，正在把 Private Cloud Compute（PCC）扩展到自有数据中心之外。PCC 是 Apple 的云端系统，负责处理设备端模型难以胜任的复杂 Apple Intelligence 任务。针对要求最高的任务，包括智能体式工具调用和复杂推理，Apple 与 Google 和 NVIDIA 合作，把 PCC 扩展到配备 NVIDIA GPU 的 Google Cloud 系统。Apple 称，这是其 PCC 隐私承诺首次延伸到第三方数据中心。[^1]

Apple 表示，PCC 的核心要求没有改变。它介绍说，新方案结合了 NVIDIA GPU 上的 NVIDIA Confidential Computing、支持 Trust Domain Extensions（TDX）的 Intel CPU，以及 Google 的 Titan 芯片。[^1]NVIDIA 次日表示，这一部署使用的是其 Blackwell GPU。[^2]

为降低供应链攻击的风险，Apple 称它为 PCC 集群中的全部 Google Cloud 硬件维护着一份只追加账本，账本可用密码学方法验证。对于一旦遭到攻破就可能泄露用户数据的组件，Apple 称其软件的远程证明植根于至少两个信任根，它们来自相互独立的厂商。远程证明会给出一份签名记录，载明机器加载了哪些软件；信任根则是无需进一步核查即被信任的组件。Apple 还表示，其设备只会信任 Apple 以密码学方式批准过的 PCC 软件。[^1]

Apple 表示将公开全部二进制文件，向研究人员提供公开工具，并通过 Apple Security Bounty 计划让他们以研究模式访问正在运行的 PCC 节点。Apple 还称，在夏季预览期内，Google Cloud 上的 PCC 将逐步向全套保护措施过渡。[^1]

截至 2026 年 10 月 20 日，Apple 的《PCC 安全指南》（PCC Security Guide）中的发布说明称，针对 Google Cloud 上的 PCC，一项公开安全研究计划将于今年晚些时候推出。说明列出的一项已知问题指出，Apple 的研究工具 `pccvre` 目前还不能解析 Google Cloud 上 PCC 的证明报告，也不能解析该部署在 PCC 透明日志中登记的版本。Apple 称，研究计划推出时，工具将加入这方面的支持。[^3]

:::analysis
PCC 的透明机制依赖研究人员把设备信任的软件与 Apple 公开的软件相比对。Google Cloud 上没有 Apple 自研芯片。Apple 称同样的保护措施在这里依然适用，这一说法因此要靠硬件账本和两个信任根等新机制支撑。在 Apple 的工具能够读取新的证明报告和日志条目之前，外界无法用 Apple 的工具核查这一部署，只能依赖 Apple 自己的描述。
:::

:::checked
2026 年 10 月 20 日，我们阅读了 Apple 于 2026 年 6 月 8 日发布的博客文章、NVIDIA 于 6 月 9 日发布的博客文章，以及《PCC 安全指南》的发布说明。发布说明没有标注日期，因此来源列表中的日期是我们阅读它的日期。我们在 Apple 的安全研究网站上没有找到该研究计划已公布的细节。我们不自行测试任何系统，也没有核实 Apple 关于硬件账本、远程证明机制设计或预览进展的说法。
:::
