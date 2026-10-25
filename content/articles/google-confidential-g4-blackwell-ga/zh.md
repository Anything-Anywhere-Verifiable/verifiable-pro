---
title: Google 称配备 NVIDIA Blackwell GPU 的机密 G4 虚拟机推出正式版
dek: Google Cloud 于 2026 年 10 月 21 日表示，G4 虚拟机上的机密计算已推出正式版，这类虚拟机配备 NVIDIA RTX PRO 6000 Blackwell GPU。Google 的文档列出的处理器技术是 AMD Secure Encrypted Virtualization（SEV），而按照其远程证明页面，在 SEV 下为 CPU 证明报告签名的只有一个由 Google 管理的软件模块。
---

2026 年 10 月 21 日，Google Cloud 表示，其 G4 虚拟机（VM）上的机密计算已推出正式版，这类虚拟机配备 NVIDIA RTX PRO 6000 Blackwell 图形处理器（GPU）。机密计算的设计目的是在处理数据的同时保护数据。机密 G4 实例在 36 个可用区提供，可通过 Compute Engine 和 Google Kubernetes Engine（GKE）使用。此前，Google 于 2026 年 6 月 23 日宣布推出预览版。Confidential Space 是 Google 用于多方数据共享的服务，Google 称对它的支持将在未来几周内推出正式版。[^1, 2]

Google 的文档只列出一种机密 G4 机器类型，即 g4-standard-48。它采用 AMD EPYC Turin 中央处理器（CPU）平台，配有一块 RTX PRO 6000 GPU。其机密计算技术是 AMD Secure Encrypted Virtualization（SEV）和 NVIDIA Confidential Computing，创建指南选用的是 SEV。SEV-SNP（即带 Secure Nested Paging 的 SEV）只列在 N2D 机器类型下。[^3, 4, 5]

Google 的博文称，客户可以借助“植根于硬件的远程证明”，在交出数据之前核查代码和配置。[^1]远程证明是指机器就其加载的软件生成签名证据。对于 SEV，Google 的远程证明页面只列出一个 CPU 证明报告签名方：由 Google 管理的虚拟可信平台模块（vTPM），页面称它基于软件。由 AMD Secure Processor 这一硬件组件签名的报告，只在 SEV-SNP 下列出。在 GPU 方面，该页面介绍了 nvattest。这是 Google 在 GitHub 上发布的工具，可以在虚拟机内部检查 GPU 的视频 BIOS（VBIOS）固件。[^6]

Google 称，在它对 Llama 3、Llama 3.3、ResNet-50 和 SDXL 等模型所做的推理测试中，吞吐量比标准 G4 实例低不到 3.5%。客户 Vertebrae 表示，它的基准测试显示端到端延迟增加了 5.2%。[^1]文档为 G4 列出的限制包括：GPU 远程证明可能因索引 9 处的度量值（即记录下来的哈希值）不匹配而失败，需要把虚拟机完全停止后再重新启动才能解决；配备 GPU 的机密虚拟机也无法组成多节点集群。[^3, 4, 6]

:::analysis
Google 称，这些实例能让客户数据免受云服务商的访问。但按照 Google 的页面，SEV 的 CPU 侧证据由 Google 管理的软件签名。因此，核查这份证据能确立的是 Google 的 vTPM 记录了什么，这一环节仍需信任 Google。GPU 自身的证明报告提供了第二项核查，而我们阅读的页面没有说明它如何与同一台虚拟机的 CPU 侧报告关联。
:::

:::checked
我们于 2026 年 10 月 25 日阅读了 Google 的两篇博文（分别发布于 2026 年 10 月 21 日和 6 月 23 日），以及其文档中关于支持的配置、GPU 机器类型、创建 GPU 虚拟机和远程证明的页面。这些文档页面均于 2026 年 10 月 22 日最后更新。10 月 21 日的博文没有提到任何 CPU 技术，远程证明页面也没有提到 G4。我们没有创建实例，因此无法查看实例的证据，也无法检验性能数据。
:::
