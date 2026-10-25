---
title: NVIDIA 推出 Confidential Bare Metal，供模型开发商在第三方基础设施上使用
dek: NVIDIA 于 2026 年 10 月 21 日推出 Confidential Bare Metal 模式，让模型开发商在其他公司运营的专用 NVIDIA 系统上运行自己的主机软件，并自行执行远程证明检查。其文档称，运营方处在开发商的运行时信任边界之外，但这一模式不会把开发商终端用户的数据与开发商本身隔离开来。
---

2026 年 10 月 21 日，NVIDIA 推出 Confidential Bare Metal（CBM），这是 NVIDIA Confidential Computing 的一种部署模式。该公司称，模型开发商可以借助 CBM，在第三方云服务商和企业运营的专用 NVIDIA 系统上运行自己的软件（包括主机软件），同时保持对自身模型和数据的控制。[^1]

文档称，这一版本支持 Grace Blackwell 机架级平台和 Vera Rubin 平台。开发商掌控主机操作系统和驱动程序、工作负载、自己的密钥以及远程证明策略。在释放模型权重或其他机密之前，开发商要评估新采集的平台证据和启动时的度量记录。这些记录由动态可信度量根（DRTM）生成，内容是已加载软件的度量值（哈希值）。CBM 不需要机密虚拟机（CVM），NVIDIA 提醒开发商做好投入大量工程工作的准备。[^2]

NVIDIA 称，完成交接和上述评估之后，运营方处在开发商的运行时信任边界之外，无权读取工作负载的未加密数据。它仍然负责供电、基板管理控制器（BMC）、互连网络（fabric）和存储，并且可以断电或阻断流量。由于开发商的管理员和软件仍在信任范围之内，CBM 不会把开发商终端用户的数据与开发商本身隔离开来。针对这种情况，NVIDIA 介绍了另加一台 CVM 的做法。[^2, 3]

文档还列出了一些局限。在 Grace Blackwell 基线配置上，CPU 与 GPU 之间、CPU 与 CPU 之间的链路都没有加密，PCI Express 流量也无法使用硬件加密；用于 GPU 间流量的 NVLink 加密既不覆盖上述链路，也不覆盖网络流量。仅靠 CPU 内存加密，无法防范数据被篡改或重放；对于侵入式硬件攻击，以及基于耗时、缓存和功耗的侧信道，CBM 也没有提供通用的防护。[^3]

NVIDIA 称，Cohere 计划把 CBM 集成到 [Model Vault](/articles/cohere-model-vault-confidential-computing/) 中。[^1]Google Cloud 表示，它正在为配备 GB300 NVL72 系统的 A4X Max 实例引入 CBM。[^4]

:::analysis
有了 CBM，模型开发商可以在释放密钥之前，核查由别人运营的硬件。开发商仍然要信任 NVIDIA 的硬件、固件和参考值；在链路没有加密的地方，还要依靠运营方的物理防护措施。仅靠 CBM，开发商的终端用户无从核查任何东西：读取证据的是开发商自己的验证方，终端用户的数据也仍要托付给开发商的软件。
:::

:::checked
我们于 2026 年 10 月 25 日阅读了 NVIDIA 的博客文章、CBM 文档中两个未标注日期的页面，以及 Google Cloud 的博客文章。文档仅有的一个版本 Dev 标注为 Beta，这些来源也都没有给出可用日期。博客列举了支持 NVIDIA Confidential Computing 的系统和云服务商，但说的是这项技术的总体支持情况；除 Google Cloud 和文档点名的平台之外，我们无法确认其中哪些提供 CBM。文档没有说明 DRTM 依靠哪种 CPU 机制实现，也没有说明 NVLink Switch 或 BMC 的状态是否纳入远程证明。我们没有测试任何实际部署。
:::
