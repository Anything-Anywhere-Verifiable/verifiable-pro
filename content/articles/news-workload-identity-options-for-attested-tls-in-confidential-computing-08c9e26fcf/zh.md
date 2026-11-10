---
title: "Internet-Draft 提出用于远程证明 TLS 的工作负载身份方案"
dek: "这份个人草案区分了获准工作负载的类型与具体实例，并介绍两种将 TLS 密钥与远程证明绑定的方案。身份授权和私钥来源是其中的关键限制。"
---

2026 年 10 月 28 日发布的一份个人 Internet-Draft，为结合远程证明的传输层安全协议（TLS）提出两种工作负载身份方案。草案 draft-reddy-seat-cc-workload-identity-00 由 Tirumaleswar Reddy.K、Nathanael Ritz、Yaron Sheffer 和 Ionuț Mihalcea 撰写，供 SEAT 讨论。它介绍部署模式和可选方案，并未规定协议；这仍是进行中的工作，未经 IETF 背书，在其标准流程中没有正式地位。[^1]

草案区分了工作负载的类型与具体实例：两个实例可以具有相同的度量值。方案 A 使用工作负载生成的密钥，将公钥写入已签名的远程证明证据，并以原始公钥或自签名证书的形式在 TLS 握手中出示。它不需要公钥基础设施（PKI），也不提供独立的工作负载标识符。方案 B 使用 WIMSE 工作负载身份证书，同时通过远程证明绑定同一个公钥；其中的标识符可以在密钥轮换后保持不变。[^1]

作者提醒，分别检查证书和远程证明，不能确认度量值所描述的环境获准使用证书声明的身份。需要这项保证时，依赖方必须联合评估身份与度量值。两种方案也都依赖对密钥生成、不可导出性和存储方式的核查：仅将公钥放入证据或证书，并不能确立这些属性。[^1]

:::analysis
问题位于 T2 运行时层和 T1 硬件层：解读工作负载度量值与 TLS 密钥绑定，仍依赖草案所述的远程证明信任根和评估策略。用户与运营方应核查公钥是否匹配、策略是否将身份与获准度量值关联，以及所选方案有何证据支持私钥来源等属性。这里涉及的可核查属性是可识别性：如果向用户提供服务的确切版本与配置有记录且可核查，用户就能判断自己是否曾接触相关部署条件；仅有类型度量值无法区分相同的实例。这些检查建议来自草案中的区分，并非漏洞通报或修复版本建议。[^1]
:::

:::checked
我们于 2026 年 11 月 9 日阅读了所提供的 IETF Datatracker 文档《Workload Identity Options for Attested TLS in Confidential Computing》00 版保存摘录。摘录在第 7 节中途结束，因此这次阅读可确认上述方案和限制，无法确认完整的密钥远程证明机制或后续安全考虑。我们没有测试系统、检查实现，也没有独立验证草案综述的云部署。[^1]
:::

[^1]: Workload Identity Options for Attested TLS in Confidential Computing。IETF Datatracker，个人 Internet-Draft，发布于 2026 年 10 月 28 日。https://datatracker.ietf.org/doc/html/draft-reddy-seat-cc-workload-identity-00
