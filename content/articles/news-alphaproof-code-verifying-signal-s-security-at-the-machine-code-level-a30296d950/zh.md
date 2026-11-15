---
title: "Google DeepMind 报告 libsignal 机器码级安全数学证明"
dek: "作者称，AlphaProof Code 将 Signal 的部分安全性质与编译后的二进制程序联系起来。结果仍依赖可信规范、执行语义和密码学假设。"
---

Google DeepMind 与 Google 的研究人员于 2026 年 11 月 10 日介绍了 AlphaProof Code，称其已在机器码层面，为 Signal 协议参考实现 libsignal 的部分安全性质构建数学证明。该框架把经过人工审阅的 Lean 规范与自主证明代理结合起来，生成的数学证明由 Lean 内核检查。[^1]

作者称，他们将未经修改的 libsignal 接入一个小型命令行测试驱动程序，再用标准 rustc 编译器生成 AArch64 Linux 机器码。项目据称包含约 650 万行 Lean 数学证明，依赖约 2.6 万行可信规范和机器码语义。比较工具会检查定理陈述及其依赖的定义是否与获批、隔离保存的规范一致，以检查生成数学证明的过程是否悄然削弱了原本的命题。[^1]

报告涉及 PQXDH 与 Triple Ratchet。引言列出的性质包括针对经典攻击者的机密性、真实性、前向保密和失陷后安全性，以及符号模型下针对未来量子攻击者的握手保密性。这些结论有明确边界：密码学原语被理想化处理或假定安全，部分被调用例程以可信契约建模。执行模型仅覆盖单线程、静态链接的进程，不包括线程和动态链接等特性。[^1]

:::analysis
这项主张位于 T2（runtime，运行时）层：验证者可以检查指定性质与特定可执行文件字节之间的关系，但仍须信任规范、Lean 内核，以及执行模型与真实系统的对应关系。用户和运营方应核对自身部署的二进制程序与配置是否落在这一范围内；所提供文本没有指定需要安装的修复版本。这里涉及的可核验性质是可识别性：如果为用户提供服务的确切版本与配置有记录且可核查，在相关问题的受影响范围得到确认后，用户就能判断自己是否曾受其影响；本报告本身没有确定任何部署的暴露状态。[^1]
:::

:::checked
我们于 2026 年 11 月 15 日阅读了所提供的《AlphaProof Code: Verifying Signal’s Security at the Machine-Code Level》保存文本，其来源日期为 2026 年 11 月 10 日。我们没有检查文中链接的代码仓库、重新运行 Lean，也没有测试该系统。本次阅读确认的是作者报告了什么及其列明的假设，没有独立验证数学证明或实际部署的应用。[^1]
:::

[^1]: Google DeepMind 与 Google，《AlphaProof Code: Verifying Signal’s Security at the Machine-Code Level》，2026 年 11 月 10 日。https://google-deepmind.github.io/code-verification/
