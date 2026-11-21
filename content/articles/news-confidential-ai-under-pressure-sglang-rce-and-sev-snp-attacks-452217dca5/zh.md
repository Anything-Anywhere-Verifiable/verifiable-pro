---
title: "CSA 报告 SGLang 安全事件与 SEV-SNP 攻击对机密 AI 的影响"
dek: "Cloud Security Alliance 的研究报告分析了一起推理服务器入侵事件和两种针对 AMD 机密虚拟机技术的攻击，指出软件与硬件面临不同的信任边界。"
---

Cloud Security Alliance（CSA）于 2026 年 11 月 16 日发布研究报告，分析 NEAR AI 的 SGLang 安全事件，以及两种针对 AMD SEV-SNP 机密虚拟机技术的攻击。报告汇集了事件通报、安全公告和研究成果；其内容不能说明这些攻击彼此有关联。[^1]

CSA 报告称，NEAR AI 披露，攻击者利用 SGLang 推理引擎中的一个远程代码执行漏洞，入侵了一台推理服务器，并进一步进入其他基础设施。NEAR AI 表示，11 月 8 日由该服务器处理的请求，包括机密模式请求，可能被查看；公司没有说明是否有人实际读取了这些请求。NEAR AI 未指明被利用的是哪个 SGLang 漏洞。CSA 称，该公司已自行部署修复，并向上游报告了所遇漏洞。[^1]

CSA 还介绍了 Mior 和 Skyfall 两种攻击，其前提是主机或虚拟机管理程序存在恶意。报告称，Mior 需要控制虚拟机管理程序和 BIOS，在未修补的平台上可用于访问客户虚拟机内存并伪造远程证明报告。Skyfall 则可通过侧信道泄露客户虚拟机的寄存器状态。CSA 表示，完整缓解依赖平台所有者和设备制造商提供固件及 BIOS 更新。[^1]

:::analysis
这些问题涉及 T2 运行时层和 T1 硬件层：用户需要信任处理请求的推理软件，验证方则依赖平台及其固件。远程证明证据可以标识加载的软件构建，但不能说明该构建没有漏洞；报告还警告，Mior 可在未修补的平台上伪造报告。[^1]

这里涉及的可核验属性是可识别性：如果为某位用户提供服务的确切版本和配置都有记录且可供核查，该用户就能判断自己是否受到影响。运营方应盘点 SGLang 部署、限制访问并跟踪上游修复；CSA 称，截至 11 月 16 日，其中一个被追踪的漏洞尚无已报告的修复版本。用户和验证方应向服务商询问缓解进度，执行适用的 SEV 固件最低版本要求，并确认 BIOS 更新已安装，因为仅凭固件版本值可能无法确认 BIOS 更新状态。[^1]
:::

:::checked
我们于 2026 年 11 月 21 日阅读了保存的 Cloud Security Alliance 研究报告《[Confidential AI Under Pressure: SGLang RCE and SEV-SNP Attacks](https://labs.cloudsecurityalliance.org/research/csa-research-note-confidential-ai-inference-tee-limits-20261/)》。[^1] 我们没有独立查阅报告所引用的事件通报或安全公告，也没有测试相关系统、攻击或修复措施。
:::
