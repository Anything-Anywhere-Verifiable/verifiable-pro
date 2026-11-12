---
title: "NVIDIA 介绍 Agent Substrate 的 Kubernetes 运行时与实验性 GPU 集成"
dek: "Agent Substrate 通过常驻工作 Pod 池和会话快照减少智能体闲置开销。NVIDIA 表示，GPU 支持正在重构，部分 Dynamo 集成仍处于实验阶段。"
---

NVIDIA 于 2026 年 11 月 10 日介绍了 Agent Substrate 的 Kubernetes 架构及上游开发进展，称这一开源运行时可将大量智能体会话复用到规模较小的常驻工作 Pod 池中。公司将其定位为独立的 Cloud Native Computing Foundation（CNCF）Sandbox 项目，与 NVIDIA DSX OS 组件进行集成，而非 DSX OS 的具名组件。[^1]

据文章介绍，独立控制平面将 actor，即智能体及其运行环境，映射到工作节点。Actor 闲置时，系统从 gVisor 或微虚拟机沙箱中保存包含内存和文件系统状态的快照，随后在可用工作节点上恢复。每次激活因此无需新建 Kubernetes Pod；常规的 Pod 调度、配额和放置策略仍然适用。[^1]

NVIDIA 介绍了设有等待时限和队列容量上限的请求暂存机制，以及微虚拟机沙箱内各容器的 CPU 和内存限制。基于 Kubernetes 动态资源分配（DRA）的 GPU 设备支持仍在开发。拟议的 GPU 检查点设计会记录设备兼容性属性，在匹配硬件上恢复；找不到匹配设备时，则退回冷启动。部分 Dynamo 集成仍属实验性质，API 也在变化。[^1]

NVIDIA 宣称，该运行时可支持数百万个智能体和工具，部署密度达到标准容器的 10 倍。保存的文章没有提供足以确立这一比较的基准测试方法或结果。[^1]

:::analysis
这些主张位于 T5（agents，智能体层）和 T2（runtime，运行时层）：会话连续性和沙箱资源控制关系到用户对执行环境的信任，但仅凭文章无法确认隔离效果或智能体行为正确性。这里可核查的属性是**可识别性**：如果服务某位用户的确切版本和配置有记录且可核查，该用户就能判断自己是否曾暴露于某种具体部署条件。运营方应核实实际部署的代码修订、沙箱配置、资源限制及实验性 GPU／Dynamo 功能；用户应要求提供可核查的服务环境记录。来源没有推荐修复版本，也未描述安全公告，因此不能据此判断是否存在漏洞暴露。[^1]
:::

:::checked
我们于 2026 年 11 月 11 日阅读了 NVIDIA Technical Blog 文章《Agent Substrate: Advancing Kubernetes for Agents at Scale》的保存副本，该文发表于 2026 年 11 月 10 日。我们没有测试系统、检查代码仓库或运行基准测试；此次阅读确认的是 NVIDIA 报道了什么，无法确认实现是否兑现了这些主张。[^1]
:::

[^1]: NVIDIA Technical Blog，《Agent Substrate: Advancing Kubernetes for Agents at Scale》，2026 年 11 月 10 日。https://developer.nvidia.com/blog/agent-substrate-advancing-kubernetes-for-agents-at-scale
