---
title: "NVIDIA 称 Snapshot 可在数秒内恢复 GPU 工作负载"
dek: "NVIDIA 报告称，在所测推理配置中，Snapshot 将启动速度提升至冷启动的 8 至 36 倍。测量不含基础设施配置和容器镜像加载，恢复还须满足软硬件兼容条件。"
---

NVIDIA 于 2026 年 11 月 10 日在技术博客中介绍了 Snapshot。这一开源组件为 Kubernetes 上的 GPU 工作负载提供检查点与恢复功能。公司报告称，在所测配置中，已完成初始化的推理副本可在 3.6 至 42.7 秒内恢复，启动速度为冷启动的 8 至 36 倍。[^1]

Snapshot 在工作负载初始化完成后保存 CPU 和 GPU 内存状态。NVIDIA 称，新 Pod 可在 GPU 型号和驱动相同的节点上从该制品恢复，跳过权重加载、编译和 CUDA 图捕获。符合条件的工作负载可跨越单个节点内的多块 GPU。工作负载还须实现一个简单的暂停与恢复握手机制，并满足检查点、恢复及运行时兼容要求。[^1]

公布的基准测试使用 NVIDIA B200 GPU、615.71.09 驱动和 VAST NFS 存储，推理引擎为 vLLM 0.31.0、SGLang 0.5.21 和 TensorRT LLM 1.3.0。冷启动计时从进程启动开始，到引擎初始化返回结束，此时尚未开始推理；恢复计时则从发出恢复请求开始，到重新提供服务结束。基础设施配置和容器镜像加载不在恢复计时范围内。NVIDIA 还表示，每次创建检查点前都会释放键值缓存，因此制品不包含该缓存。[^1]

:::analysis
这项主张涉及 T6 评估层、T2 运行时层和 T1 硬件层：读者要将结果用于自身服务，须先核对计时边界、恢复进程的配置及 GPU 兼容条件。用户和运营方应将实际部署的引擎与驱动版本、GPU 型号、检查点配置和存储条件，与文中测试环境及兼容要求逐项比对；该文没有指出安全修复或推荐的修复版本。[^1] 这里可核查的属性是可识别性：如果为用户提供服务的确切版本和配置有记录且可查，用户就能判断自己是否曾处于相关部署条件之下。这类记录可支持判断，但本文并未确认记录是否存在，也未确认其他系统能获得同等性能。
:::

:::checked
我们于 2026 年 11 月 12 日阅读了保存的 NVIDIA Technical Blog 文章《Start and Restore GPU Workloads in Seconds with NVIDIA Snapshot》，包括其测试方法、环境说明和三张结果表。[^1] 这次阅读确认的是 NVIDIA 报告了哪些内容。我们没有测试 Snapshot、复现基准测试或检查文中链接的代码仓库；性能和兼容性仍属于厂商报告的主张。
:::

[^1]: NVIDIA，《Start and Restore GPU Workloads in Seconds with NVIDIA Snapshot》，2026 年 11 月 10 日。https://developer.nvidia.com/blog/start-and-restore-gpu-workloads-in-seconds-with-nvidia-snapshot
