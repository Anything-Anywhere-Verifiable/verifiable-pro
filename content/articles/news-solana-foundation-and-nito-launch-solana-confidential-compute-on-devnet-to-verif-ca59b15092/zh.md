---
title: "Solana Compass 报道：Solana Confidential Compute 在开发网上线"
dek: "据报道，这一测试版可在链上检查 AI 应用的硬件远程证明。目前它尚未接受审计，仅供开发使用。"
---

据 Solana Compass 2026 年 11 月 13 日报道，Solana Foundation 与 Nito 已发布 Solana Confidential Compute 开发网测试版。这套开源工具旨在让应用在接受签名的 AI 输出前，于链上检查硬件远程证明。报道指出，该软件尚未接受审计，仅供开发使用。[^1]

可信执行环境（TEE）是一种由硬件支持的环境，旨在将代码和数据与外围系统隔离。根据 Solana Compass 对发布内容的转述，机密虚拟机会生成签名密钥，并取得一份由硬件签名的报告，将密钥与近期的 Solana slot 关联起来。链上程序检查报告后，记录密钥、硬件类型和到期时间；接收方随后可以检查回答的签名及密钥的链上记录。[^1]

报道说，验证程序会检查芯片签名、代码是否符合获准列表，以及报告的新鲜度。测试版支持 Intel TDX 和 AMD SEV-SNP 远程证明，NVIDIA GPU 远程证明仍在开发中。Solana Compass 还报道称，审计正在进行，主网计划在审计完成后推出；报道没有给出主网上线日期。[^1]

:::analysis
这一声明涉及运行时（T2）和硬件（T1）层：验证者需要依赖链上检查、硬件远程证明和获准代码列表。检查通过可以提供有关所证明环境及密钥的证据，但不能确立 AI 回答正确，也不能独立确立隐私得到保护。这里涉及的可核验属性是可识别性：如果服务于某位用户的确切版本和配置有记录且可供检查，该用户就能判断自己是否受到特定问题的影响；报道并未确立这一系统会记录这些细节。用户和运营方应检查密钥状态、到期时间及适用的获准代码，并确认自己的部署是否处于报道所述的仅供开发使用范围内。[^1]
:::

:::checked
在准备这篇 2026 年 11 月 18 日的预览时，我们阅读了保存的 [Solana Compass 文章](https://solanacompass.com/news/solana-foundation-and-nito-launch-solana-confidential-compute-on-devnet-to-verify-private-ai-onchain)文本；该文章发表于 2026 年 11 月 13 日。Solana Compass 自称独立于 Solana Foundation；我们没有直接阅读基金会的公告或产品页面。我们没有测试该系统，也没有独立核实发布情况、系统安全性或审计状态。[^1]
:::
