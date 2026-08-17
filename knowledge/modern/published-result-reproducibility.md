---
type: Decision Rule
title: "Treat a published benchmark claim as an unverified hypothesis until reproduced"
description: >
  A large-scale claim-by-claim audit of ICML 2026 found roughly a quarter of examined papers had
  at least one claim falsified or contested, including spotlighted work. Peer review and venue
  prestige are not evidence tiers; reproduce the specific claim you intend to build on, at the
  scale you intend to use it. Extends /foundations/universal-workflow.md's baseline discipline to
  the literature a builder cites.
tags: [evaluation, reproducibility, evidence, research-practice, agents]
tier: frontier
applies_to:
  - citing a paper's benchmark number to justify an architecture, hyperparameter, or model choice
  - deciding how much evidence a technique needs before it enters a production pipeline
  - using coding agents to reproduce or audit published results
status: draft
stale_after: 2026-11-17
generated:
  by: expedition/weekly-2026-08-17
  at: 2026-08-17T00:00:00Z
sources:
  - id: icml-repro
    resource: https://github.com/huggingface/blog/blob/8107eda00fc59dcfcd010b60cbc1f97e0d5c5a51/icml-2026-open-reproductions.md
    title: "What We Learned by Reproducing 2,200 papers from ICML (source of huggingface.co/blog/icml-2026-open-reproductions)"
    author: Hugging Face (abidlabs)
    last_modified: 2026-08-13
---

# Rule

**A published, peer-reviewed, even spotlighted benchmark number is an unverified hypothesis. Reproduce the specific claim you intend to build on, at the scale you intend to use it, before it changes your design.** In an audit its organizers believe to be "the largest open, claim-by-claim audit of a machine learning conference to date" — their characterization, not an independently established one — community participants attempted 2,226 of the 6,341 indexed ICML 2026 accepted papers (reported as 34% of the conference) and had 35,908 individual claims judged.[^icml-repro] The outcome was not a clean pass: 51% of examined papers (1,103) had at least one claim independently verified, but **23% (496) had at least one claim falsified or contested**, 502 yielded only toy-scale evidence, and 280 established nothing either way, most often because artifacts were missing.[^icml-repro] Only 266 papers were fully reproduced with every extracted claim verified.[^icml-repro]

**Prestige does not predict correctness.** The audit's headline example is an accepted ICML 2026 **spotlight** whose reviewer wrote "My low confidence score is because I did not check all the proofs carefully"; its claimed robustness bound of \(H_k + O(1)\) was measured growing like \(0.38 \ln k\), and the organizers' own re-implementation out to k = 1,024 confirmed the growth at roughly nine sigma — the true bound being \(H_k + \Theta(\log k)\).[^icml-repro] Treat venue and reviewer scores as a filter on relevance, never as an evidence tier.

**Reproduce at your scale, not at a convenient one.** Three independent teams found counterexamples to a token-collapse theorem only at t = 224, ~3,800, and 6,416 steps; the report attributes everyone else's "verified" verdicts to finite-horizon checks that stopped too early.[^icml-repro] A short reproduction that agrees with the paper is evidence about short runs only.

**Check that the released code computes what the paper's theory analyzes.** In one confirmed finding, a paper's central equation and entire theory section analyzed reverse KL divergence while the released code's default — which per the authors produced all the paper's results — computed forward KL; the same logbook also failed to reproduce the paper's headline +4pp result under the authors' own code and data.[^icml-repro] In another, ~66% of evaluated label positions were EOS padding that trains to near-zero loss, deflating perplexity roughly threefold and turning an abstract's "3.1% quality cost for 50% cache reduction" into roughly 9.4% once corrected.[^icml-repro]

**Reproduction is adversarial, not binary — and your reproduction can be the thing that is wrong.** 242 papers had independent teams reach *opposite* verdicts on the same claims.[^icml-repro] The organizers adversarially re-verified every claimed falsification and caught at least one "false falsification": a logbook claiming a method was 2× slower than baseline had compared per-trajectory time against per-batch-of-50 time; correctly normalized, the participant's own data confirmed the paper's claimed 8× speedup.[^icml-repro] Budget a normalization/units review before acting on a negative result, exactly as you would on a positive one.

**Agent-run reproduction needs a human in the loop.** The report states that pure agent execution hit real limits — agents got stuck in local loops, misread scale-dependent behavior, and occasionally built an entire falsification on a units mismatch — and that the most reliable results came from workflows where a human re-pointed the agent, questioned assumptions, or killed a bad premise before compute was spent.[^icml-repro] Its automated judge ran an open-weights model (GLM-5.2) and was explicitly instructed to treat each logbook's self-assessment as untrusted.[^icml-repro] If you automate reproduction, budget the human steering and keep the judge adversarial to the thing it judges.

**Scope note.** This rule is about the *evidence status* of external claims; it does not change any routing decision in [the universal workflow](../foundations/universal-workflow.md), whose "beat a naive baseline first" discipline it reinforces. It is also the literature-facing analogue of this catalog's own trust tiers: a `draft` concept sourced to an unreproduced paper is exactly the case this rule warns about.

# Open questions

- The audit reports counts, not a per-paper error rate for the conference as a whole. Which papers got attempted was participant-driven, so the 23% falsified-or-contested figure describes the examined subset and may not transfer to the 66% of the conference nobody attempted; the source does not characterize that selection bias.
- The category counts overlap rather than partition: a paper can hold both a verified and a falsified claim (1,103 + 496 + 502 + 280 exceeds the 2,226 examined), so they cannot be summed into a breakdown.
- The source reports two different counts for accepted ICML 2026 papers — 6,352 in the framing section and 6,341 indexed for the challenge. This concept quotes the 6,341 figure because the 34% coverage claim is computed against the indexed set; the discrepancy is unexplained in the source and unresolved here.
- No independent source corroborates any of these figures; this is a single-source concept written by the challenge's own organizers, who have an interest in the exercise appearing valuable. Tier is `frontier` for that reason.

[^icml-repro]: Hugging Face blog, "What We Learned by Reproducing 2,200 papers from ICML" (source id: icml-repro), read at repo commit 8107eda, dated 2026-08-13. All counts, percentages, quoted reviewer text, and the four named findings are stated in that post. Figures are as of the challenge close (challenge ran July 15 – August 2, 2026); ICML 2026 submission/acceptance counts (23,918 submitted, 6,352 accepted) are quoted from the same post.
