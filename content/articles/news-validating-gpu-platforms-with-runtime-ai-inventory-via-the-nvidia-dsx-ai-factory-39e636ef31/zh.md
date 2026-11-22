---
title: "NVIDIA 为 GPU 平台配置方案加入 AI 运行时清单"
dek: "NVIDIA 表示，AI Cluster Runtime 现已集成 k8s-aibom，可为受支持的 Kubernetes AI 工作负载生成清单。清单的覆盖范围和核验能力仍有限制。"
---

2026 年 11 月 11 日，NVIDIA 介绍了一项集成：在 DSX AI Factory Platform 的 NVIDIA AI Cluster Runtime（AICR）中，为受支持的 Kubernetes 工作负载生成 AI 物料清单（AIBOM）。NVIDIA 表示，这项集成将版本锁定的 GPU 平台配置方案与开源项目 k8s-aibom 的工作负载清单结合起来。[^1]

AICR 配置方案记录期望的平台配置；k8s-aibom 则观察工作负载和 Pod API，为识别出的 AI 工作负载生成 CycloneDX 1.6 清单。两个面向 H100 的 Google Kubernetes Engine 配置方案默认选择该组件，其他 GKE 配置方案可以选择启用。NVIDIA 的示例使用 AICR v1.2.0，其组件目录将 k8s-aibom 固定为 1.6.2。[^1]

清单覆盖已选择生成报告的命名空间中，带有可识别 AI 信号的受支持工作负载类型。每个记录属性都附有置信等级和证据定位信息。Pod 运行之前就可能已有 AIBOM：清单记录工作负载声明，并在 Pod 存在后记录可获得的解析证据，但不能说明工作负载已成功执行。命名空间标签控制哪些命名空间生成清单，控制器仍会在整个集群范围内缓存工作负载和 Pod 规格。[^1]

NVIDIA 表示，其资格验证流程将特定的上游构件与按摘要固定的控制器镜像绑定，检查来源，并在经过测试的部署路径上验证部署操作。运行时观察记录本身没有签名，模型声明的签名验证默认关闭，平台来源信息与运行时清单的关联仍有待实现。此外，存储版本匹配本身不能说明完整的自定义资源定义模式已经更新。[^1]

:::analysis
这一问题涉及 T3 模型层和 T2 运行时层：清单可以帮助核验者识别模型与运行时属性，但覆盖范围和证据决定了哪些信息可以信任。这里涉及的可核验属性是可识别性：如果为用户提供服务的确切版本和配置已被记录且可供核查，用户就能判断自己是否受到影响。用户和运营方应检查自己的工作负载及命名空间是否在覆盖范围内，审阅相关属性的证据和置信等级，并根据自身部署核对已安装版本、模式及控制器健康状态；NVIDIA 的示例指定使用 AICR v1.2.0 和 k8s-aibom 1.6.2。[^1]
:::

:::checked
我们于 2026 年 11 月 18 日阅读了保存的 NVIDIA Technical Blog 文章[《Validating GPU Platforms with Runtime AI Inventory via the NVIDIA DSX AI Factory》](https://developer.nvidia.com/blog/validating-gpu-platforms-with-runtime-ai-inventory-via-the-nvidia-dsx-ai-factory)，该文发表于 2026 年 11 月 11 日。[^1] 我们没有测试该系统，也没有独立核实 NVIDIA 对资格验证流程或清单行为的说法。
:::
