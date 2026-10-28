---
title: "NVIDIA 介绍 Sentry 面向 AI 智能体的硬件隔离管控"
dek: "NVIDIA 称，Sentry 在 BlueField-4 上结合流量检查、主机内存观测和硬件执行管控，计划于 2027 年初推出。保存的公告不能确立实际部署中的性能。"
---

NVIDIA 于 2026 年 10 月 21 日介绍了 Sentry：据公司称，这一安全软件框架在 BlueField-4 数据处理单元（DPU）的独立硬件信任域中监测 AI 智能体并执行访问策略，不依赖主机软件。Sentry 属于 OpenShell 参考架构，计划于次年初，即 2027 年初推出。现有 DOCA 库和微服务可供开发者先行开展实验。[^1]

NVIDIA 表示，DOCA Flow 为每个智能体设置网络防火墙，将获准通过的流量转发给基于 Envoy 的代理 DOCA Tower。对于配置为接受检查的连接，Tower 会终止传输层安全协议（TLS）连接，并使用 Open Policy Agent 评估请求。DOCA Argus 则独立检查主机内存的选定区域，提供进程、容器和库的上下文。策略可以要求容器哈希值属于批准清单，并对照软件物料清单检查发起请求的进程。[^1]

NVIDIA 还介绍了对通信进行在线或带外分类的专用模型。公司称，BlueField-4 可以在毫秒级时间内遏制智能体，并保存带远程证明的遥测数据及可显示篡改痕迹的活动记录。这些属于厂商对能力的陈述。文章将远程证明描述为遥测来源和完整性的证据，并未确立每次策略决策或行为分类都正确。[^1]

:::analysis
这些主张涉及 T5 智能体层、T2 运行时层和 T1 硬件层：访问决策依赖智能体上下文、运行时观测以及独立的执行管控域。用户和运营方应核对自身部署是否确实将所有相关流量送经 BlueField-4、哪些连接接受检查，以及实际采用哪些策略和批准的哈希值；公告中的架构描述本身不能确立这些部署事实。这里关系到的可核验属性是**可识别性**：如果为用户提供服务的确切版本和配置有记录且可核查，用户就能判断自己是否曾暴露于相关情形。文章没有指定修复版本或漏洞补救措施，也没有确立用户能够获得上述部署记录。[^1]
:::

:::checked
我们于 2026 年 10 月 28 日阅读了 NVIDIA Technical Blog 于 2026 年 10 月 21 日发布的《Inside NVIDIA Sentry: Secure AI Agents at Runtime》的保存文本。这次阅读仅确立 NVIDIA 如何描述该框架及其计划；我们没有测试 Sentry、检查实际部署，也没有独立核验遏制延迟或遥测完整性。[^1]
:::

[^1]: NVIDIA Technical Blog，《Inside NVIDIA Sentry: Secure AI Agents at Runtime》，2026 年 10 月 21 日。https://developer.nvidia.com/blog/inside-nvidia-sentry-secure-ai-agents-at-runtime/
