---
title: Brave 称 Leo 现已加密 GLM 5.3 Flash 对话，密钥由经过远程证明的 NEAR AI 飞地持有
dek: Brave 于 2026 年 10 月 15 日表示，其浏览器内置的 AI 助手 Leo 现在会加密用户与开放权重模型 GLM 5.3 Flash 的对话，所用密钥存放在 NEAR AI 运营的可信执行环境中。Brave 称，其网关先核查这些环境的远程证明，再把对应的公钥交给浏览器；浏览器端的核查和对已加载权重的远程证明仍在计划之中。
---

Brave 于 2026 年 10 月 15 日表示，其浏览器内置的 AI 助手 Leo 已在 Release、Beta 和 Nightly 渠道为 GLM 5.3 Flash 的对话启用端到端加密，用户选择该模型即可使用。GLM 5.3 Flash 是 Z.ai 发布的开放权重模型，由 NEAR AI 托管。[^1, 2]

浏览器使用不经意 HTTP（OHTTP）为 NEAR AI 的可信执行环境（TEE）加密每个请求。可信执行环境是硬件隔离的区域，按设计将其中的代码和数据与机器的运营方隔离开来。Brave 称，解密密钥只由这些 TEE 持有。TEE 运行在 Intel Trust Domain Extensions（TDX）和 NVIDIA 的机密计算图形处理器（GPU）之上。Brave 称，其 AI Gateway 会去掉用户的互联网协议（IP）地址；它还会把 TEE 当前的远程证明与验证预言机（verification oracle）的批准结果相比对，核查通过后才把 TEE 的公钥交给浏览器。[^1]

Brave 称，预言机在批准一次部署之前，会核验 Intel 在 TDX quote（即处理器签名的证明报告）上的签名，并通过 NVIDIA 的远程证明服务（Remote Attestation Service）核查 GPU。它还会检查 NEAR AI 自有镜像的签名构建记录，用 Brave 审查过的源代码重新构建这些镜像，再与已部署的镜像比对。第三方模型运行时不会重新构建；一份经过硬件远程证明的部署日志锁定了它，并记录了模型镜像。[^1]预言机的代码已由 Brave 以 near-verifier 为名公开，其 README 称，任何持有 NEAR AI API 密钥的人都可以用它核查线上服务。[^1, 3]

README 还称，预言机不会重新构建 NEAR AI 的 compose-manager-launcher 镜像；它按 Hugging Face 上的版本（revision）锁定权重，但不对下载的文件计算哈希值；它也无法确立请求是由哪块 GPU 处理的。[^3]Brave 计划把网关的这项核查移入浏览器，公布一份 TEE 密钥日志，让任何人都能确认所有用户拿到的是同一把密钥，并让 TEE 对其加载的权重进行远程证明，但没有给出时间表。Brave 称，这些核查仍然依赖 Intel、NVIDIA、Sigstore、GitHub、Hugging Face、公共域名系统（DNS），以及 TEE 的操作系统 dstack。[^1]

:::analysis
按 README 的说法，外界现在可以重复预言机的核查，但 Leo 用户收到的密钥仍以 Brave 网关的核查为准，而这个网关还能看到用户的 IP 地址。除了 Brave 列出的各方，权重文件的内容、运行时的源代码以及每个请求由哪块 GPU 处理，也都不在核查范围之内，只能依靠信任。
:::

:::checked
我们于 2026 年 10 月 25 日阅读了 Brave 和 NEAR AI 于 2026 年 10 月 15 日发布的文章，以及 near-verifier 的 README。两篇文章都没有说明这项功能适用于哪些平台，也没有说明 Leo 用户如何查看证明证据；README 也没有说明如何获取 API 密钥。我们没有运行 near-verifier，也没有测试该服务。关于谁能读取对话的表述，均为这两家公司的说法。
:::
