---
type: Architecture Pattern
title: "LLM agents paired with formulaic alpha factor mining"
description: >
  Pairing LLM-driven research loops (RD-Agent(Q)) and RL alpha generators (AlphaGen) with
  the qlib backtest stack to automate factor discovery — promising results, immature field,
  strict leakage controls required.
tags: [quant-finance, llm-agents, factor-mining, formulaic-alpha, rd-agent, alphagen, automation]
tier: frontier  # NOTE(skeptic): value undefined in house rules; trust tier derives from `verified` (none yet => unverified)
status: draft
stale_after: 2026-12-01
generated:
  by: expedition/qlib-2026-08-03
  at: 2026-08-03T12:00:00Z
sources:
  - id: rd-agent-repo
    resource: https://github.com/microsoft/RD-Agent
    title: "microsoft/RD-Agent README (RD-Agent(Q) performance claims)"
    author: Microsoft
    last_modified: 2026-08-03
  - id: rdagentq
    resource: https://arxiv.org/abs/2505.15155
    title: "R&D-Agent-Quant: A Multi-Agent Framework for Data-Centric Factors and Model Joint Optimization"
    author: Microsoft Research
    last_modified: 2025-05-21
  - id: qlib-readme
    resource: https://github.com/microsoft/qlib
    title: "Qlib README (LLM-driven Auto Quant Factory news entry, 2024-08-08)"
    author: Microsoft
    last_modified: 2026-08-03
  - id: alphagen
    resource: https://arxiv.org/abs/2306.12964
    title: "Generating Synergistic Formulaic Alpha Collections via Reinforcement Learning (AlphaGen)"
    author: Yu et al. (KDD 2023)
    last_modified: 2023-06-22
  - id: survey
    resource: https://arxiv.org/abs/2503.21422
    title: "From Deep Learning to LLMs: A survey of AI in Quantitative Investment"
    author: Cao et al.
    last_modified: 2025-03-27
---

# Pattern

**The pairing:** automated factor-discovery agents (LLM-driven or RL-driven) on top of the qlib backtest stack, replacing manual formulaic-alpha engineering.

**Why formulaic alphas are the target.** Practitioners favor formulaic (symbolic) alphas because they are interpretable where risk oversight matters, and in practice alphas are deployed as sets fed to a combination model rather than used individually.[^alphagen][^survey] Deep models' opacity is a cited reason interpretable pipelines persist despite an accuracy edge.[^survey] The traditional pipeline is also siloed — factor mining, model training, and evaluation lack cross-stage feedback, limiting joint gains.[^rdagentq]

**RL variant (AlphaGen).** Mining alphas one at a time by maximizing single-alpha IC is a flawed objective because it ignores downstream combination; AlphaGen instead rewards each new alpha's *marginal contribution* to the combined pool's performance.[^alphagen] On Chinese A-shares it reached IC 0.0725 on CSI300 vs 0.0404 for XGBoost (~79% higher), while genetic-programming baselines with mutual-IC filtering did far worse (0.0183).[^alphagen] A notable side finding: high pairwise correlation does not imply redundancy — two alphas with mutual IC 0.9746 still improved pool IC.[^alphagen]

**LLM-agent variant (RD-Agent(Q)).** The "LLM-driven Auto Quant Factory" was released in the RD-Agent project on 2024-08-08, automating factor mining and model optimization on top of qlib.[^qlib-readme] RD-Agent(Q) is described by its authors as the first data-centric multi-agent framework automating full-stack quant R&D via coordinated factor-model co-optimization, running a research (hypothesis/factor proposal) → development (code + backtest) → feedback loop; it claims roughly 2x higher annualized return than benchmark factor libraries while using over 70% fewer factors, at under $10 per run.[^rd-agent-repo] The paper reports up to ~2x ARR vs classical factor libraries (Alpha101/158/360, AutoAlpha), outperformance of SOTA deep time-series models, and a best config of IC 0.0532, ARR 14.21%, IR 1.74 on CSI300 (test Jan 2017–Aug 2020).[^rdagentq]

**Non-negotiable leakage control for LLM-in-the-loop research:** the LLM is never exposed to raw market data or explicit temporal split boundaries — only schema-level information — explicitly to prevent leakage into generated factors and models.[^rdagentq] See (/domains/quant-finance/leakage-and-evaluation.md) — expedition sibling, not yet landed as of 2026-08-03.

**Maturity check.** The 2025 survey judges LLM applications in alpha strategy "less mature compared to other deep learning methods" with practical deployment "still in its early stages."[^survey] Treat the headline numbers as promising single-team results, not settled consensus.

# Conflicts with stable concepts

- (/foundations/scope-boundary.md) (stable) lists "Quantitative-finance ML workflows" and "Reinforcement learning" as not covered by the catalog. Stable wins while this concept is a draft: quant-finance asks route to draft-tier advice at best, and scope-boundary must be revised when expedition #1 lands. Recorded per house rule — conflicts are disclosed, never silently resolved.

# Open questions

- RD-Agent(Q)'s ~2x ARR / 70%-fewer-factors claims are self-reported by the framework's authors; scouts found no independent replication.
- Generalization evidence is limited to the paper's own CSI500/NASDAQ100 tests (test windows 2024–2025)[^rdagentq]; robustness across regimes and markets beyond those runs is unestablished.

[^alphagen]: AlphaGen, arXiv:2306.12964 (KDD 2023). CSI300 IC figures from Table 2 (AlphaGen 0.0725, XGBoost 0.0404, GP with mutual-IC filter 0.0183); the mutual-IC 0.9746 synergy case from Table 3. Verified against full text 2026-08-03.
[^rdagentq]: R&D-Agent-Quant, arXiv:2505.15155. Best config (o3-mini backbone): IC 0.0532, ARR 14.21%, IR 1.74 on CSI300, test Jan 1 2017–Aug 1 2020; CSI500/NASDAQ100 generalization runs test 2024–2025. Leakage control quote: "the LLM is never exposed to raw market data or explicit temporal splits, but only to schema-level information." Verified against full text 2026-08-03.
[^rd-agent-repo]: microsoft/RD-Agent README (accessed 2026-08-03): "at a cost under $10, RD-Agent(Q) achieves approximately 2× higher ARR than benchmark factor libraries while using over 70% fewer factors."
[^qlib-readme]: microsoft/qlib README news table (accessed 2026-08-03): "LLM-driven Auto Quant Factory — Released in RD-Agent on Aug 8, 2024." Note this entry no longer appears in the RD-Agent repo's own README.
[^survey]: arXiv:2503.21422, "From Deep Learning to LLMs: A survey of AI in Quantitative Investment" (Cao et al., 2025): "their application remains less mature compared to other deep learning methods"; "the practical deployment of LLMs is still in its early stages"; deep models "often lack transparency, making them less preferable in domains where understanding decision-making processes is crucial, such as finance."
