---
type: Decision Rule
title: "Lift the document-length cap before comparing retrievers"
description: >
  Retrieval checkpoints ship with document-length caps of 180-512 tokens inherited from their
  training data. Evaluated as-served on longer passages they are scored on a truncated fraction of
  each document, and in one measured comparison that truncation cost up to 0.24 NDCG@10 — more, at
  its worst, than any difference between model architectures. Lift the cap first; a comparison run
  before that is partly measuring tokenizer settings.
tags: [retrieval, embeddings, evaluation, benchmarking, sentence-transformers]
tier: frontier
applies_to:
  - comparing retrieval or reranker checkpoints on your own corpus
  - reading a retrieval leaderboard or a published NDCG/recall comparison
  - standing up the evaluation for a RAG system over long documents
  - deciding whether to fine-tune a retriever or switch to a bigger general-purpose one
status: draft
stale_after: 2026-12-07
generated:
  by: expedition/weekly-2026-09-07
  at: 2026-09-07T00:00:00Z
sources:
  - id: st-multivector
    resource: https://github.com/huggingface/blog/blob/6da89bdcceba308dca53ecee843fe9a90b921f1e/train-multi-vector-encoder.md
    title: "Training and Finetuning Multi-Vector Embedding Models with Sentence Transformers (source of huggingface.co/blog/train-multi-vector-encoder)"
    author: Tom Aarsen (Hugging Face)
    last_modified: 2026-08-26
---

# Rule

**Before you compare retrieval models, check what document length each one will actually read, and
lift it. A comparison run on as-served caps is a measurement of truncation, not of the models.**
Most released retrieval checkpoints were configured for short passages: "The classic ColBERT
checkpoints truncate documents at 180 or 300 tokens, and many popular dense models at 256 or 512,
because their MS MARCO-style training data rarely goes beyond that. If your documents are long,
these models silently discard most of every document before scoring it."[^st-multivector]

The measured size of the effect, on a medical retrieval evaluation whose passages average 941
tokens: **"I measured that this truncation costs up to 0.24 NDCG@10, considerably more than any
difference between model architectures."**[^st-multivector] In the same evaluation, lifting the cap
"was worth +0.08 to +0.24 NDCG@10 over the as-served row" for *every* multi-vector model, and +0.03
even for a dense model.[^st-multivector]

**The decision this changes:** a leaderboard ordering built on as-served caps does not tell you
which architecture to adopt for long documents — it partly ranks which checkpoints happened to be
configured for longer inputs. Re-run the comparison with caps lifted before concluding that a
family, an architecture, or a parameter count is what separates two models.

**Where the cap lives is a configuration detail, not a model property.** With per-task caps unset,
"truncation falls back to the tokenizer's `model_max_length`", which is why the source sets that
limit at load time.[^st-multivector] So the fix is usually a load-time setting rather than a
different checkpoint.

**Include a lexical baseline, and discount it correctly.** In this evaluation BM25 beat "every
sparse model, every truncation-capped multi-vector model, and all but three dense models" — but the
source immediately supplies the reason not to generalize that: the dataset's questions are generated
from the passages, so query-passage lexical overlap is unusually high, "and BM25's unlimited context
length lets it use every one of those overlapping words while most neural checkpoints
truncate."[^st-multivector] The transferable half is the practice ("A BM25 baseline is cheap and
always worth running"); the margin is not transferable.[^st-multivector]

**Domain fine-tuning is within reach of one consumer GPU, which changes the buy-versus-tune
calculus.** The source's own multi-vector model was "trained in 14.5 hours on a single RTX 3090"
alongside the post and reports outperforming every general-purpose retrieval model the author could
find on that medical evaluation — dense, sparse, lexical and multi-vector alike.[^st-multivector]
Treat that as an existence proof for the cost scale, not as a benchmark result you can expect to
match.

# Open questions

- **Single source, single evaluation, single domain.** One author's medical retrieval evaluation on
  a corpus with 941-token average passages. The mechanism (truncation discards text before scoring)
  is general; the magnitude is not. Tier is `frontier` accordingly, and `stale_after` is set at
  three months because the load-bearing claim is a benchmark number.
- **The evaluation is by the maintainer of the library whose new model type the post introduces, and
  the correction it advocates is not self-neutral.** Lifting the cap raises the author's own
  architecture family by +0.08 to +0.24 against +0.03 for a dense competitor, and it is what moves
  the truncation-capped multi-vector models back above the BM25 baseline that otherwise beat
  them.[^st-multivector] That is a reason for care, not for dismissal: the mechanism is cheap to
  check on your own corpus, which is the right basis for acting on it. No independent party has
  reproduced the measurement.
- "Up to 0.24 NDCG@10" is an upper bound over a set of models, quoted as such here. The per-model
  range for multi-vector models is given as +0.08 to +0.24, and a dense model gained
  +0.03.[^st-multivector] Do not cite 0.24 as a typical effect.
- Lifting a document cap beyond what a checkpoint was trained on is not free in general — cost and
  quality both change with length. The source configures higher caps at load time and reports the
  gain, but does not report the latency or memory price of doing so.
- Retrieval and embedding models are a **new area for this catalog**: no stable concept covers
  retrieval. Nothing here should be read as covering RAG system design more broadly.

# Conflict with a stable concept

No stable concept covers retrieval, but this draft does touch the stable
[scope boundary](../foundations/scope-boundary.md)'s exclusion of "LLM / foundation-model
fine-tuning (LoRA, PEFT, instruction tuning)": its `applies_to` includes the decision of whether to
fine-tune a retriever, and it cites a domain fine-tune as an existence proof for the cost scale.
**The boundary still governs:** fine-tuning *methodology* remains an OUT-OF-SCOPE response. What
this draft covers is the evaluation-configuration decision — lift the cap before you compare — plus
the observation that a domain fine-tune of a retriever fits on one consumer GPU. Recorded here
rather than resolved, following the precedent set for
[open-weight model-selection signals](open-weight-model-selection-signals.md).

# Related

- [Published-result reproducibility](published-result-reproducibility.md) — a benchmark comparison
  whose confound is a tokenizer setting is a concrete instance of why a published ordering is a
  hypothesis until reproduced on your data.

[^st-multivector]: Hugging Face blog, "Training and Finetuning Multi-Vector Embedding Models with Sentence Transformers", by Tom Aarsen, read from the `huggingface/blog` repository at commit `6da89bd` (source id: st-multivector). The truncation quotes are from the post's motivation section, the per-model lift range from the evaluation table's footnote, the BM25 discussion and the 14.5-hour single-RTX-3090 training claim from the evaluation and introduction sections. The post also introduces Sentence Transformers v6.0's `MultiVectorEncoder` model type. Verified by fetching the file at that SHA on 2026-09-07.
