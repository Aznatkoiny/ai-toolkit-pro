---
type: Decision Rule
title: "Late-interaction retrieval buys about one NDCG point for a compressible index"
description: >
  In a controlled ablation at equal parameter count, a multi-vector (ColBERT-style) retriever beat
  its dense twin on 9 of 13 NanoBEIR datasets and by ~1 NDCG@10 point on the mean — but the spread
  runs from +6.8pp to -6.2pp, so the mean is not the number you will get. Uncompressed the index is
  ~42x a small dense index; PLAID plus token pooling brings it into the range of a large dense
  index. Decide on your own corpus, and prefer retrieve-and-rerank to test before committing storage.
tags: [retrieval, embeddings, rag, colbert, late-interaction, sentence-transformers, indexing, evaluation]
tier: frontier
applies_to:
  - choosing between a dense bi-encoder and a multi-vector retriever for search or RAG
  - budgeting index storage for a retrieval system
  - upgrading a Sentence Transformers pipeline to v6.0
status: draft
stale_after: 2027-02-24
generated:
  by: expedition/weekly-2026-08-24
  at: 2026-08-24T00:00:00Z
sources:
  - id: st6-multivector
    resource: https://github.com/huggingface/blog/blob/bc2adee48c9e0b8fdfe6d9aca239bfeed4a69cd3/multi-vector-encoder.md
    title: "Multi-Vector (Late Interaction) Embedding Models with Sentence Transformers (source of huggingface.co/blog/multi-vector-encoder)"
    author: Hugging Face (tomaarsen) and LightOn (NohTow, raphaelsty)
    last_modified: 2026-08-19
---

# Rule

**Late interaction is a modest average gain with a wide per-corpus spread, bought with index
storage. Decide it on your own data, not on the mean.** A dense model compresses a whole text into
one vector, so a rare entity, an exact identifier, and one crucial clause all compete for room in
the same 384 or 768 numbers; a multi-vector model projects each token embedding to a small
dimension (classically 128) and keeps all of them, scoring with MaxSim — for each query token, its
highest similarity against any document token, summed over the query.[^st6-multivector]

**The controlled number.** `lightonai/LateOn` and `lightonai/DenseOn` were trained on the same
data with the same ModernBERT backbone and the same 149M parameters, differing only in whether
they keep one vector per token or pool to one per document — an ablation that isolates late
interaction itself. Over all 13 NanoBEIR datasets, LateOn won 9 and the mean, 0.6868 against
0.6764 NDCG@10: **roughly one NDCG point.** The same pair scores 57.22 against 56.20 on the full
15-dataset BEIR, so the margin is not an artifact of the small benchmark.[^st6-multivector]

**The spread is the actionable part, and it is much wider than the mean.** Within that same table
the gap runs from **+6.8pp on MSMARCO** (0.7194 vs 0.6517) and +4.9pp on HotpotQA down to
**−6.2pp on FiQA2018** (0.5871 vs 0.6491), with three further losses on ArguAna, SciFact, and
SCIDOCS.[^st6-multivector] A one-point mean assembled from a ±6-point spread predicts almost
nothing about your corpus. **Run the evaluator on your own data before you pay for the index** —
`MultiVectorNanoBEIREvaluator` needs no data preparation, and
`MultiVectorInformationRetrievalEvaluator` covers your own dataset.[^st6-multivector]

**Where the gain is expected to come from**, per the source: queries whose relevance hinges on one
specific piece of a document, multi-requirement queries where each requirement can find its own
evidence, and out-of-domain data where a dense model's compression was tuned for a different query
distribution; the effect "grows with document length," since more text must fit the same fixed
vector.[^st6-multivector] That reasoning is the source's, and the table above is the only
quantification of it offered.

**The cost, measured on 4,874 Natural Questions passages encoded with `lightonai/LateOn`:**

| Representation | Vectors | Dim | float32 index |
|---|---:|---:|---:|
| Dense, `all-MiniLM-L6-v2` | 4,874 | 384 | 7.5 MB |
| Dense, `gte-modernbert-base` | 4,874 | 768 | 15.0 MB |
| Multi-vector, `LateOn` | 608,414 | 128 | 311.5 MB |

608,414 token vectors, an average of 124.8 per passage — about 42× the MiniLM index, roughly
62 KiB per passage.[^st6-multivector]

**Two compressions change the verdict, and they compose.** The same 608,414 vectors occupy 92 MB
as a `fast-plaid` index, because PLAID stores a centroid id plus a quantized residual per vector
rather than the vector itself; a 4096-dimensional dense model such as `Qwen3-Embedding-8B` would
need about 80 MB for the same passages.[^st6-multivector] **A compressed multi-vector index
therefore sits in the same territory as a large dense index people already run — the 42× figure
describes uncompressed float32 and is the wrong number to budget from.** Separately,
`HierarchicalTokenPooling` (Ward linkage on cosine distance, each cluster replaced by its mean,
keeping roughly `1 / pool_factor` of the tokens) cuts the vector count first:

| `pool_factor` | Token vectors | Reduction | float32 index |
|:---:|---:|:---:|---:|
| 1 (off) | 608,414 | 1.00× | 311.5 MB |
| 2 | 305,438 | 1.99× | 156.4 MB |
| 3 | 204,407 | 2.98× | 104.7 MB |
| 4 | 153,936 | 3.95× | 78.8 MB |

Pooling all 608k vectors took about 6 seconds, and applies to documents only by default since
queries are short and are the side you cannot afford to distort.[^st6-multivector] Start at
`pool_factor=2`: the retention figures the source quotes — 100.6% of unpooled retrieval
performance at 2 and 99.0% at 3, on BEIR — come from the original token-pooling paper
(arXiv:2409.14683v1), not from this post, which says the cost "is corpus-specific though, so
measure it with an evaluator before you settle on a factor."[^st6-multivector]

**If the index is the problem, you may not need one.** Retrieve-and-rerank uses a fast dense
bi-encoder for the first stage and rescores only the top candidates with MaxSim, avoiding a
multi-vector index entirely — the source demonstrates retrieving the top 50 and
rescoring.[^st6-multivector] Given the spread above, this is the cheapest way to find out whether
late interaction helps *your* queries before committing storage.

**Serving knob worth taking.** On GPU, fp16 with Flash Attention measured 2.44× the throughput of
fp32 with no measurable retrieval quality loss; the source attributes the outsized gain to
unpadding, since multi-vector documents are truncated but never padded to a shared length, so
batches carry widely varying sequence lengths.[^st6-multivector]

**Migration gate.** `MultiVectorEncoder` arrives in Sentence Transformers v6.0, which **requires
`transformers` v5.x, `torch` 2.2+, and `huggingface-hub` v1.x** — plan that upgrade before
planning the retriever.[^st6-multivector] Checkpoints carry over rather than needing retraining:
any PyLate checkpoint and any Stanford-NLP ColBERT checkpoint load directly (the latter detected
via an `HF_ColBERT` architecture marker), and `colpali-engine` models for visual document
retrieval work through the same API.[^st6-multivector]

**Scope note.** This concept covers *selection and index budgeting* for retrieval. Training or
fine-tuning a multi-vector model is not covered here and remains outside the catalog, consistent
with the stable [scope boundary](../foundations/scope-boundary.md)'s exclusion of
foundation-model fine-tuning methodology. Retrieval is not on that boundary's uncovered list, so
this concept opens a new area rather than crossing an existing exclusion.

# Open questions

- Both models in the head-to-head are LightOn's, and two LightOn authors co-wrote the post; LightOn
  also builds PyLate, `fast-plaid`, and the pooling regularizer mentioned below. The ablation is
  genuinely controlled (same data, backbone, parameter count), but it is an interested party
  evaluating its own pair, and no independent reproduction exists. Tier is `frontier`
  accordingly; see [published-result reproducibility](published-result-reproducibility.md).
- NanoBEIR subsamples 50 queries per dataset. The post itself warns that "its scores aren't a
  substitute for evaluating on your own data."[^st6-multivector] The 15-dataset BEIR figures
  (57.22 / 56.20) are reported as bare numbers with no per-dataset breakdown, so the spread on the
  full benchmark cannot be checked.
- Whether the ~1-point mean holds at other parameter counts, other backbones, or non-English
  corpora is not established. The comparison is one pair at 149M parameters.
- All storage figures come from one corpus (4,874 Natural Questions passages, 124.8 vectors per
  passage). Longer documents scale the token count, and the index, differently — 62 KiB per
  passage is not a constant.
- The BEIR retention figures at `pool_factor` 2 and 3 are quoted at second hand and were not
  re-derived here (arXiv was outside this session's network perimeter). A retention *above* 100% at
  `pool_factor=2` is reported without explanation; flagged, unresolved.
- The separate claim of 99.4% retention at 5× compression for
  `lightonai/LateOn-hpool-regularized` is a LightOn self-report the post links but does not verify,
  and the regularizer is not in Sentence Transformers.[^st6-multivector] Do not plan around it.
- No index-build or query-latency numbers accompany the storage table, so the *serving* cost of
  late interaction — as distinct from its storage cost — is unquantified by this source.

[^st6-multivector]: Hugging Face blog, "Multi-Vector (Late Interaction) Embedding Models with Sentence Transformers" (source id: st6-multivector), read at repo commit bc2adee, post last modified 2026-08-19 (originally published 2026-08-18). The MaxSim definition, the LateOn/DenseOn training-parity statement and full 13-row NanoBEIR table, the 9-of-13 and BEIR-15 (57.22 vs 56.20) figures, the storage and token-pooling tables, the 124.8-vectors-per-passage average, the 42× and 62 KiB figures, the 92 MB fast-plaid and ~80 MB Qwen3-Embedding-8B comparisons, the ~6 s pooling time, the quoted BEIR retention figures and their attribution to arXiv:2409.14683v1, the documents-only pooling default, the retrieve-and-rerank pattern, the 2.44× fp16+Flash-Attention result, the NanoBEIR caveat, the v6.0 dependency requirements, and the PyLate / Stanford-NLP ColBERT / colpali-engine checkpoint compatibility are all stated there. Per-dataset deltas (+6.8pp MSMARCO, +4.9pp HotpotQA, −6.2pp FiQA2018) are computed from that table.
