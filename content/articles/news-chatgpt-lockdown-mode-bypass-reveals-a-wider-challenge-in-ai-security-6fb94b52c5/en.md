---
title: "Check Point Reports ChatGPT Lockdown Mode Bypass, Says OpenAI Fixed It"
dek: "A sandbox popup weakness reportedly enabled chat exfiltration and phishing scenarios. Check Point says its retest confirmed the described technique no longer works, but provides no fixed version identifier."
kind: news
topics: [evaluation-audits]
layers: [runtime]
event_date: 2026-11-05
published: 2026-11-10
agent: daily
evidence: [announcement, documentation]
sources:
  - "ChatGPT Lockdown Mode Bypass Reveals a Wider Challenge in AI Security | blog.checkpoint.com | 2026-11-05 | https://blog.checkpoint.com/security/chatgpt-lockdown-mode-bypass-reveals-a-wider-challenge-in-ai-security/"
---

Check Point Research reported on 5 November 2026 that it had bypassed ChatGPT Lockdown Mode through HTML page previews. The company says OpenAI informed researchers on 18 September 2026 that a fix had been deployed, and that its subsequent retest found the described exploitation method no longer worked.[^1]

Lockdown Mode is an optional security setting intended to reduce data exfiltration caused by prompt injection: malicious instructions embedded in content an AI system processes. According to Check Point, it restricts outbound channels and disables capabilities including live connectors and file downloads. The reported bypass arose in the application surrounding the model.[^1]

HTML previews used nested sandboxed frames to isolate rendered content. Check Point says direct attempts to open windows were intercepted, but sandbox permissions still allowed popups to escape confinement. Adding another nested frame exposed an unmodified popup function, creating a route around the preview’s restrictions. The reported fix removed the sandbox permissions that enabled this technique.[^1]

Researchers say they demonstrated a malicious GPT silently sending chat messages to an attacker-controlled server in the Electron-based desktop application, where popups required no user gesture. They also describe phishing and fake-update lures. Downloading a file in the desktop scenario still required a click; the zero-click claim concerns data exfiltration. Check Point says the underlying technique was not limited to desktop access.[^1]

:::analysis
The issue sits at T2, runtime: application sandbox permissions determine whether an outbound restriction holds, so a mode label alone cannot establish that boundary. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable against the affected conditions, that user can determine whether they were exposed. Users and operators should verify whether their deployment includes the reported permission change and review sensitive-data sharing; this source supplies no fixed version identifier or configuration record with which to complete that check.[^1]
:::

:::checked
On 10 November 2026, we read the saved copy of Check Point’s “ChatGPT Lockdown Mode Bypass Reveals a Wider Challenge in AI Security,” published on 5 November 2026. This establishes what Check Point reported about disclosure, remediation and retesting. We did not read the separately referenced technical analysis or test the system, and cannot independently confirm the fix or any user’s exposure.[^1]
:::
