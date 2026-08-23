---
type: Decision Rule
title: "Reading Hub signals when picking an open-weight base model"
description: >
  Likes and downloads measure different things and must not be substituted for one another;
  derivative count is the signal for ecosystem durability; and permissive licensing at the
  frontier can no longer be assumed, so the licence must be checked per release. Extends the
  licensing gate in /modern/tsfm-financial-forecasting.md to open-weight LLM selection generally.
tags: [model-selection, open-weights, licensing, hugging-face, gguf, ecosystem]
tier: frontier
applies_to:
  - choosing an open-weight base model to fine-tune, deploy, or standardize a team on
  - judging whether a model will still be maintained and supported in a year
  - clearing a model for commercial use
status: draft
stale_after: 2026-11-17
generated:
  by: expedition/weekly-2026-08-17
  at: 2026-08-17T00:00:00Z
sources:
  - id: hf-state-summer26
    resource: https://github.com/huggingface/blog/blob/f68cf553ac0a030dc8edb29d184ede3e01affd88/state-of-open-models-summer-2026.md
    title: "State of Open Models: Summer 2026 Observations (source of huggingface.co/blog/state-of-open-models-summer-2026)"
    author: Hugging Face (AdinaY, multimodalart, irenesolaiman)
    last_modified: 2026-08-16
---

# Rule

**Never substitute likes for downloads, or either for a quality judgement.** Of the top 25 Hub repositories by downloads accumulated in 2026 and the top 25 by likes, **exactly one repository appears on both lists**.[^hf-state-summer26] Not one model published in 2026 reaches the download top 25, while thirteen of the twenty-five date from 2022; `all-MiniLM-L6-v2` was pulled 1.55 billion times in seven months against 5,156 likes, and Kimi-K3 about 60 times per like.[^hf-state-summer26] The two numbers record different acts: a like says a release matters and accrues to frontier models in the weeks after they ship; a download says something is wired into a pipeline that runs on a schedule, and accrues to small, stable models over years.[^hf-state-summer26] **Use likes to read excitement, downloads to read current dependence, and neither to read quality** — the source states explicitly that these metrics "should not be interpreted as direct measures of model quality, commercial adoption, or overall market share," and that downloads miss API usage and private deployments entirely.[^hf-state-summer26]

**For "will this still be supported when I need it", the signal is derivatives, not either of the above.** Qwen-based models account for 151,448 derivatives on the Hub — 2.6× Meta's total footprint and 4.7× the Llama repositories specifically — with Google second at 82,506; Qwen derivatives grew at roughly 180–210 new repositories per day across the first seven months of 2026.[^hf-state-summer26] The report attributes the position to consistency of cadence, coverage across sizes, and Apache-2.0 licensing, and notes it was built by the community rather than the lab: of 28,531 GGUF conversions of Qwen models, Qwen published only 54.[^hf-state-summer26] **The corollary is a real risk: if the quantized build you deploy is community-produced, the weights you run are not the weights the lab tested.** The report makes the same point, recommending labs ship official conversions and document quantization choices.[^hf-state-summer26]

**Check the licence on the specific release, every time — permissive-at-the-frontier is no longer a safe default.** The report states that in the last few weeks before publication, Kimi K3 and Qwen3.8 began "to include some non-commercial restrictions and revenue share requirements to their licenses."[^hf-state-summer26] **Revenue share is a materially different obligation from a non-commercial clause and from Apache-2.0, and it will not be caught by a lab-level or family-level assumption.** This generalizes the licensing gate already recorded for time-series models in [TSFM financial forecasting](tsfm-financial-forecasting.md): clear the licence before evaluating the model, not after.

**Deployment reach, not parameter count, decides what you can actually run — and that layer is where the movement is.** Among models declaring a parameter count, those under 1B take 83% of all-time downloads and everything above 100B takes 1%; restricting to 2026 downloads, only 3% of volume goes to models above 70B.[^hf-state-summer26] Meanwhile repositories declaring the `gguf` library rose 464% over the seven-month window, `lerobot` 194% and Apple `mlx` 148%, against 16% for `transformers` and `peft` and 21% for `diffusers`, on a base of 21.5% growth in model repositories overall.[^hf-state-summer26] **When choosing a family, weight the availability of a runtime path for your hardware at least as heavily as the benchmark table** — on the local-inference route the traffic runs on Qwen at 39.6M GGUF downloads/month, nearly twice Gemma's 20.8M and more than five times Llama's 7.5M, a gap the report notes is not explained by supply since Llama-derived GGUF repositories slightly outnumber Qwen's.[^hf-state-summer26]

**Read all Hub aggregates against the underlying distribution.** Roughly 85.6% of models have fewer than 200 lifetime downloads and 1.5% of repositories account for 99.2% of all downloads.[^hf-state-summer26] Any "N models support X" claim is compatible with almost nobody using them.

# Open questions

- **The source contradicts itself on licensing and this concept does not resolve it.** It states that of 178 Chinese releases above 20B parameters this year "59% carry Apache 2.0 and 22% carry MIT, and **most carry a non-commercial restriction**" — figures that cannot all hold, since 81% permissive leaves no room for a non-commercial majority. This concept therefore relies only on the report's specific, named claim about Kimi K3 and Qwen3.8, and treats the aggregate licence percentages (including the American-side 29% Apache-or-MIT / 41% custom / 30% undeclared split) as unusable until corrected. Do not cite those aggregates from this concept.
- Derivative count measures community activity, not maintenance commitment by the publishing lab; the source offers no evidence that a high-derivative family is better supported, only that it is more built-upon.
- Every figure here is Hub-internal, single-source, and published by the platform being measured. There is no independent corroboration, and the report itself frames Hub activity as "one perspective on ecosystem development rather than a complete measurement of the AI market." Tier is `frontier` for that reason.
- Whether the Kimi K3 / Qwen3.8 licence changes represent a durable industry shift or two isolated cases cannot be determined from a single report written days after they appeared. This is the main reason for this concept's short `stale_after`.

# Conflict with a stable concept

The stable [scope boundary](../foundations/scope-boundary.md) lists "LLM / foundation-model
fine-tuning (LoRA, PEFT, instruction tuning)" as not covered by any stable concept, and this
draft speaks to choosing a base model to fine-tune or deploy. **The stable concept wins:** the
advisor must still give the canonical OUT-OF-SCOPE response for fine-tuning *methodology*
questions. This draft covers only the selection-and-licensing decision that precedes that work,
and only at `Evidence: unverified`. Recorded here rather than resolved; promotion of this concept
would require the boundary to be revised deliberately.

# Out of scope for this concept

The source's geopolitical and business-model analysis (release-size ceilings by country, valuation commentary, the agent-traffic dataset, the July security incident) carries no builder decision and is deliberately not distilled here.

[^hf-state-summer26]: Hugging Face blog, "State of Open Models: Summer 2026 Observations" (source id: hf-state-summer26), read at repo commit f68cf55, dated 2026-08-16. All counts, percentages, and quoted method caveats are stated in that post; the analysis window is the first seven to eight months of 2026 and the post carries an "edited to include latest releases in early August" note.
