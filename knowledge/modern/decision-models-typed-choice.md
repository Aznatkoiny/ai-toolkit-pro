---
type: Decision Rule
title: "Typed choice, score and boolean questions have a non-generative option: decision models"
description: >
  llama.cpp added a `/v1/systemone` endpoint serving "decision models" — non-generative models that
  answer typed `choice`, `score` and `noul` questions about a state and return a probability per
  option with `output_tokens` always 0. For routing, triage, scoring and classification this replaces
  a generative call plus schema parsing. Three gates before you plan on it: the returned probabilities
  are explicitly NOT guaranteed calibrated for your data, option counts are capped per model, and the
  weights' licences are published off-repo and could not be verified.
tags: [classification, routing, inference, llama-cpp, local-inference, calibration]
tier: frontier
applies_to:
  - choosing an architecture for routing, triage, intent classification, or rubric scoring
  - replacing a generative LLM call whose only output is a label, a score, or a boolean
  - needing a per-option probability or a confidence value rather than a sampled token
  - deploying classification locally on CPU or a consumer GPU
status: draft
stale_after: 2027-04-05
generated:
  by: expedition/weekly-2026-10-05
  at: 2026-10-05T00:42:00Z
sources:
  - id: lcpp-systemone-readme
    resource: https://github.com/ggml-org/llama.cpp/blob/a4cb4c61fd9d9c2066c7c1747821d3d65b8943bd/tools/server/README.md
    title: "llama.cpp server README — POST /v1/systemone: TypeSafe-compatible System One API"
    author: "llama.cpp contributors (endpoint authored by Xuan-Son Nguyen)"
    last_modified: 2026-10-02
  - id: lcpp-systemone-commit
    resource: https://github.com/ggml-org/llama.cpp/commit/a4cb4c61fd9d9c2066c7c1747821d3d65b8943bd
    title: "llama.cpp commit a4cb4c6 — llama, server: add /v1/systemone API (models: laya, julia-1, lev, openjev, kev) (#29818)"
    author: "Xuan-Son Nguyen"
    last_modified: 2026-10-02
  - id: lcpp-constants
    resource: https://github.com/ggml-org/llama.cpp/blob/99b95488cac0f00ce3f05af113a8c1e287753f87/gguf-py/gguf/constants.py
    title: "llama.cpp gguf-py constants.py — decision-model backend enumeration and readout mechanisms"
    author: "llama.cpp contributors"
    last_modified: 2026-10-03
  - id: lcpp-clef-commit
    resource: https://github.com/ggml-org/llama.cpp/commit/99b95488cac0f00ce3f05af113a8c1e287753f87
    title: "llama.cpp commit 99b9548 — model: add support for clef decision model (text-only) (#29831)"
    author: "Xuan-Son Nguyen"
    last_modified: 2026-10-03
---

# Rule

**When the entire output of an LLM call is a label, a level, or a boolean, a generative model plus JSON-schema parsing is no longer the only local option. Evaluate a decision model instead — and evaluate it on the three gates below before you plan a migration around it.** As of 2026-10-02 llama.cpp serves these through `POST /v1/systemone`, which "Answers typed questions about a `state` with a decision model."[^lcpp-systemone-readme] The endpoint takes a `state` (string, object, or array — non-strings are passed as JSON text) and a map of question ids to questions, each typed `choice`, `score`, or `noul`.[^lcpp-systemone-readme]

**What you get back is a distribution, not a sample, and it costs no generated tokens.** A `choice` answer returns the highest-probability option, "`probabilities`: The probability of each option, they sum to 1", and a confidence "value from 0 to 1, where 0 means all options are equally likely". A `score` answer returns "The expected level index, weighted by probability", so it "can be between two levels", plus the per-level distribution. A `noul` answer returns the probability that the answer is true. In the usage block, "`output_tokens` is always 0."[^lcpp-systemone-readme] **That is the structural argument for this class:** schema-conformance failures, refusals, and output-token cost all disappear, because nothing is generated. A graded rubric score arriving as a probability-weighted expectation rather than a sampled integer is a different and generally better primitive than parsing a number out of prose.

**Gate 1 — the probabilities are not calibrated, and the source says so plainly.** "The probabilities are scaled with the temperatures stored in the model file. They are not guaranteed to be calibrated for your data."[^lcpp-systemone-readme] **So do not wire `confidence` or a probability straight into a routing threshold or an escalation rule.** Treat the numbers as an ordering you must calibrate against your own labelled set before thresholding — the same discipline any classifier output needs, and the opposite of what the convenient `confidence` field invites.

**Gate 2 — capacity and shape limits are per-model, and one backend silently truncates.** "The number of options of a `choice` question is limited by the model, for example: 52 for openjev, 255 for laya. For laya, long questions and options are truncated to the token budget the model was trained with."[^lcpp-systemone-readme] A taxonomy that outgrows the cap, or option descriptions longer than the budget, degrades rather than erroring on `laya`. Streaming is unavailable ("streaming is not supported"), image input requires both a model that supports it and its multimodal projector via `--mmproj`, and the error contract is narrow: 400 for an invalid request, **501 if the loaded model is not a decision model**, and 501 for images against a model or configuration that cannot take them.[^lcpp-systemone-readme] One useful property for batching several questions about the same state: "The questions of a request are answered independently, an answer does not depend on the other questions."[^lcpp-systemone-readme]

**Gate 3 — the weights' licences could not be verified, and the publishers are not one organization.** Six backends are registered, and `constants.py` names the readout mechanism of each: `laya` ("head blocks + scorer on the hidden state of one marker token per option"), `openjev` ("logits of one label token per option"), `lev` ("same as openjev, noul is read from a rating scale"), `kev` ("dot product of the hidden states of the last token and of one end token per option"), `nimble` ("same as openjev, the prompt lists all the questions of the request"), and `clef` ("joint head over all questions, one score per option").[^lcpp-constants] **These come from several different publishers, so there is no single licence to reason about**, and every model card lives on a host this expedition's network could not reach — see Open questions. **Do not assume a permissive licence for any of them.**

**Read the mechanism list as a selection hint, not trivia.** Five of the six read out per option, so cost grows with the option count; `clef` alone uses a joint head over all questions at one score per option.[^lcpp-constants] Where you have many questions about one state, that distinction is the one likely to matter.

**Maturity: this is days old and partially wired.** The endpoint landed 2026-10-02 (`a4cb4c6`), `nimble` support the same day, and `clef` on 2026-10-03 (`99b9548`), all authored by one contributor.[^lcpp-systemone-commit][^lcpp-clef-commit] `clef` is text-only as merged, and its commit title says so.[^lcpp-clef-commit] **Pin a build and re-read the server README before relying on any specific backend**, because the capability surface moved three times in two days.

# Open questions

- **Licences are unverified, and this is the blocking item before any deployment.** The weights and their model cards are published on a host blocked by this expedition's network policy, so not one licence could be read from a re-fetchable artifact. The repository identifiers appearing in the llama.cpp converters span at least six distinct publishers, several of them individual or small, and one backend's publisher (`clef`) is not named in the repository at all. Anyone acting on this concept must read each model's own licence first.
- No accuracy, latency, or cost measurement is published in any source read here — not against a generative baseline, and not against a conventional fine-tuned classifier head. The structural advantages (no schema failures, zero output tokens, a distribution instead of a sample) follow from the API contract; **the claim that a decision model is more accurate than the alternatives is made by no source cited here.**
- Whether these models beat the catalog's existing book-canon route for classification — a task-appropriate output head trained on your own data, per the [pairing concepts](/foundations/pairing-multiclass-single-label.md) — is untested. The plausible read is that decision models compete with *zero-shot generative* classification, not with a trained classifier on a task where you have labels, but no source establishes this.
- Converter TODOs disclose incomplete support: the `lev` converter notes the head for large option sets is not converted ("only the label readout is supported"), and image input is unimplemented for `nimble`.[^lcpp-constants] The practical option ceiling for `lev` is therefore lower than the per-model caps above imply.
- Single-stack, single-author, three-day-old evidence. Nothing here is corroborated by a second serving stack or an independent party; tier is `frontier` accordingly.

# Related

- This is a new route for work the catalog currently sends to a trained output head — compare [modality → architecture map](/foundations/modality-architecture-map.md) and [pairing: multiclass single-label](/foundations/pairing-multiclass-single-label.md). **No stable concept is contradicted:** those concepts route a task you have labelled training data for, and nothing in the sources here displaces them.
- The uncalibrated-probability gate is the load-bearing caveat; see [published-result reproducibility](published-result-reproducibility.md) for the evidence discipline that applies to a capability this new.

[^lcpp-systemone-readme]: llama.cpp `tools/server/README.md`, section "POST `/v1/systemone`: TypeSafe-compatible System One API" (source id: lcpp-systemone-readme), read at commit `a4cb4c6` and re-fetched 2026-10-05. Supplies the endpoint description, the `state`/`questions`/`criteria` contract, the three question types, the full response shape for `choice`/`score`/`noul` including `probabilities` and `confidence`, `output_tokens` always 0, the "not guaranteed to be calibrated for your data" statement, the per-model option caps (52 openjev, 255 laya) and `laya` truncation, the no-streaming constraint, the `--mmproj` image requirement, the 400/501 error contract, and the independence of questions within a request.
[^lcpp-systemone-commit]: llama.cpp commit `a4cb4c6`, "llama, server: add /v1/systemone API (models: laya, julia-1, lev, openjev, kev) (#29818)", author Xuan-Son Nguyen, commit date 2026-10-02 (source id: lcpp-systemone-commit). Date, author and subject confirmed by `git log` against a local clone on 2026-10-05.
[^lcpp-constants]: llama.cpp `gguf-py/gguf/constants.py` at commit `99b9548` (source id: lcpp-constants), re-fetched 2026-10-05. Lines 6005–6010 enumerate the six decision backends with the readout-mechanism comments quoted above. Converter TODOs for `lev` and `nimble` are in the conversion scripts at the same revision.
[^lcpp-clef-commit]: llama.cpp commit `99b9548`, "model: add support for clef decision model (text-only) (#29831)", author Xuan-Son Nguyen, commit date 2026-10-03 (source id: lcpp-clef-commit). Commit `46ca246`, "model: support nimble decision model (#29844)", same author, commit date 2026-10-02. Both confirmed by `git log` against a local clone on 2026-10-05.
