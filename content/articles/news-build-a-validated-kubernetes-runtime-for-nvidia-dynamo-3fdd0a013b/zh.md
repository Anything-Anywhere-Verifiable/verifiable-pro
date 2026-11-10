---
title: "NVIDIA 详解 Dynamo 在 Kubernetes 上的配方化运行时验证"
dek: "AICR 固定基础设施组件版本，并按配方要求检查已部署的集群。NVIDIA 的教程介绍了运行时符合性检查，性能验证则单独进行。"
---

NVIDIA 于 2026 年 10 月 30 日发布教程，介绍 NVIDIA AI Cluster Runtime（AICR）如何将 Dynamo 及其 Kubernetes 基础设施打包为带版本的配方。配方记录固定的组件版本、兼容性约束、配置值、校验和与验证预期，让运维人员有一套明确的配置依据来核对部署。[^1]

文章指定使用 1.4.2 版 Dynamo Platform Helm chart。示例中的 AICR v1.0.0 配方面向运行于 NVIDIA GB200 NVL72 和 GB300 NVL72 系统上的 Amazon EKS。NVIDIA 表示，团队已在这些平台和硬件上对所列组件版本进行了组合测试；这一说法不能直接推广到其他环境。[^1]

流程依次为采集集群快照、生成配方、渲染部署包、安装运行时，以及在部署应用前验证实际集群。部署与符合性检查的具体内容取决于配方，可涵盖 GPU 容量、Operator 健康状态和版本、加速器访问、调度、指标及入口就绪状态。离线验证只评估声明式约束，会跳过行为检查。性能验证另行执行，通过临时服务工作负载占用待测 GPU。[^1]

教程还区分了 Dynamo Frontend 路由与结合端点选择插件（EPP）的 Gateway API Inference Extension 路由。示例配置中的两条路径都使用工作进程上报的键值（KV）缓存事件。NVIDIA 提醒，仅根据此前的路由决策预测缓存内容，无法观察缓存逐出，因此路由器掌握的状态可能偏离实际情况。[^1]

:::analysis
这项主张位于 T2（runtime，运行时）层：检查通过所确立的是部署符合所选配方的要求，模型行为和应用正确性仍在这一结果的范围之外。这里涉及的可验证属性是可识别性：如果实际为用户提供服务的确切版本和配置有记录且可核查，用户就能判断自己是否曾接触该部署。运维人员应依据所选配方核对已安装版本、节点放置设置、路由模式和在线验证结果；用户则需要获得这些记录，才能完成可识别性核查。文章介绍的是兼容性验证，没有指出安全修复，也没有推荐用于修复漏洞的版本。[^1]
:::

:::checked
我们于 2026 年 11 月 10 日阅读了所提供的 NVIDIA Technical Blog 文章《Build a Validated Kubernetes Runtime for NVIDIA Dynamo》的保存副本，该文发表于 2026 年 10 月 30 日。我们没有测试该系统、检查实际部署的集群，也没有独立复现 NVIDIA 所述测试；本次核查仅确认保存的教程描述了哪些内容。[^1]
:::

[^1]: NVIDIA Technical Blog，《Build a Validated Kubernetes Runtime for NVIDIA Dynamo》，2026 年 10 月 30 日。https://developer.nvidia.com/blog/build-a-validated-kubernetes-runtime-for-nvidia-dynamo
