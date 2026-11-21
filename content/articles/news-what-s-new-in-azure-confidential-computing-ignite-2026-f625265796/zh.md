---
title: "Microsoft 在 Ignite 公布 Azure 机密计算更新"
dek: "Microsoft 介绍了机密 AI 演示，以及机密虚拟机和 Kubernetes 节点的更新。该演示使用本地验证器，远程证明仍处于架构规划阶段。"
---

Microsoft 于 2026 年 11 月 17 日在 Ignite 介绍了 Azure 机密计算的新服务和演示，包括基于 NVIDIA Vera Rubin NVL72 的机密 AI 演示，以及更多机密虚拟机和 Kubernetes 选项。该公司区分了正式发布、预览和仍在开发中的功能。[^1]

Microsoft 称，AI 演示使用一个配备四块 Rubin GPU 的计算节点，通过 vLLM 运行一个拥有 3970 亿参数的模型。演示收集 CPU 和 GPU 证据，再由一个精简的本地验证器检查签名、令牌绑定和预期的 GPU 度量值，随后进行推理演示。远程证明仍是该设计的架构方向；此次演示使用本地验证。在这一裸金属模式下，租户的主机操作系统和运行时属于可信计算基，客户须负责保障其安全。[^1]

Microsoft 还宣布，基于 AMD EPYC Turin 的 v7 机密虚拟机进入受限预览。机密 Azure Kubernetes Service（AKS）工作节点现已支持 Intel TDX：搭配 Azure Container Linux 的支持已正式发布，搭配 Ubuntu 26.04 的支持仍在预览。工作节点上的 Pod 共享该虚拟机的保护边界；AKS 中按 Pod 隔离的机密容器仍在开发中。Microsoft 表示，其托管 PostgreSQL 机密计算服务不向客户提供远程证明。[^1]

:::analysis
相关层级是 T2 运行时和 T1 硬件：硬件支持的环境及其信任边界内的软件，都会影响用户需要信任什么。演示中的本地检查针对 Microsoft 所描述的证据，不能据此认定应用行为正确，也不能认定某项部署可供远程验证。可识别性同样重要：如果为用户提供服务的确切版本和配置有记录且可核查，用户就能判断自己是否受到某个受影响版本或配置的影响。运营方应检查自身系统支持的配置、信任边界、远程证明、密钥释放和恢复流程；这篇公告没有指出受影响版本，也没有推荐修复版本。[^1]
:::

:::checked
我们于 2026 年 11 月 20 日阅读了保存的 Microsoft Community Hub 文章《[What’s New in Azure Confidential Computing — Ignite 2026](https://techcommunity.microsoft.com/blog/AzureConfidentialComputingBlog/what%E2%80%99s-new-in-azure-confidential-computing-%E2%80%94-ignite-2026/4573909)》；文章发表于 2026 年 11 月 17 日。我们没有测试该系统，也没有独立核实演示、可用性或安全方面的声明。[^1]
:::
