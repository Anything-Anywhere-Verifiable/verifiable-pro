---
title: "CNCF 会员文章详解 OpenShell 在 Kubernetes 上的策略边界"
dek: "这篇面向平台工程师的文章介绍了针对智能体每次请求的控制机制，并指出运维团队在生产部署前需要补齐的准入策略。"
---

CNCF 于 2026 年 11 月 11 日刊发了 Nirmata 的 Jim Bugwadia 撰写的会员文章，介绍 OpenShell 如何将智能体请求控制与 Kubernetes 准入策略结合。文章强调了一项运维责任边界：OpenShell 检查部分 Pod 设置，平台团队仍需负责允许使用的镜像、资源限制、凭据管理，以及修改其 Kubernetes 访问规则的权限。[^1]

据文章介绍，OpenShell 使用 SIG Apps 的 Agent Sandbox，而非自建调度器。每个智能体沙箱外部都有一个监督进程，按目标地址、端口、发起请求的二进制程序及 HTTP 请求检查出站访问。智能体拿到的是凭据占位符，监督进程只会在访问提供方允许的端点时替换为真实密钥。文章称，策略可在不重启沙箱的情况下更新，并报告了一个允许读取 GitHub 内容、拒绝创建 issue 的演示。[^1]

示例使用 OpenShell 0.1.3 和 Kyverno 1.18.2。其准入策略要求通过摘要固定镜像，限制权限和资源，并拒绝通过 `envFrom` 直接注入 Secret。不过，文章明确提醒，网关的 ServiceAccount 仍可直接创建 Pod 和 NetworkPolicy。对于生产环境，作者建议将策略扩展至 Pod，以及所有选择 OpenShell 工作负载的 NetworkPolicy。镜像签名校验和更强的 RuntimeClass 要求等控制措施并未纳入演示。[^1]

:::analysis
这些主张涉及 T5（智能体）和 T2（运行时）：请求授权依赖监督进程，部署限制则依赖 Kubernetes 配置与准入策略的覆盖范围。这里需要关注的可核验属性是可识别性：如果为用户提供服务的确切版本和配置有记录且可查，用户就能判断自己是否曾暴露于文中描述的策略缺口。用户和运维团队应核对部署版本、生效策略、镜像摘要，以及直接创建 Pod 和 NetworkPolicy 的路径是否受控；文章提供的是演示版本，并未推荐某个安全修复版本。[^1]
:::

:::checked
我们于 2026 年 11 月 16 日阅读了 CNCF 文章《OpenShell on Kubernetes: A guide for platform engineers》的保存副本，该文发表于 11 月 11 日。我们没有打开文中链接的代码仓库或文档，没有运行演示，也没有测试系统。此次阅读仅确认作者描述了哪些机制、提出了哪些建议，不能独立确认策略执行效果或系统是否适合生产使用。[^1]
:::

[^1]: [OpenShell on Kubernetes: A guide for platform engineers](https://www.cncf.io/blog/2026/11/11/openshell-on-kubernetes-a-guide-for-platform-engineers/) — CNCF，2026 年 11 月 11 日。
