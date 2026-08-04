---
type: Decision Rule
title: "Time-series foundation models for financial forecasting: zero-shot is out-of-domain transfer"
description: >
  Which TSFMs to reach for (Chronos-2 general-purpose, Kronos finance-native), licensing
  traps (Moirai is non-commercial), and why zero-shot financial forecasting must be treated
  as unvalidated out-of-domain transfer.
tags: [time-series, foundation-models, zero-shot, finance, chronos, kronos, licensing]
tier: frontier
applies_to:
  - zero-shot or few-shot forecasting of financial series
  - selecting a pretrained time-series model for a trading or research workflow
default_general_model: amazon/chronos-2
finance_native_model: NeoQuasar/Kronos-base
commercial_license_blocked: [Salesforce/moirai-1.1-R, Salesforce/moirai-2.0-R]
status: draft
stale_after: 2026-12-01
generated:
  by: expedition/qlib-2026-08-03
  at: 2026-08-03T12:00:00Z
sources:
  - id: chronos2
    resource: https://huggingface.co/amazon/chronos-2
    title: "amazon/chronos-2 model card"
    author: Amazon
    last_modified: 2026-06-05
  - id: kronos
    resource: https://huggingface.co/NeoQuasar/Kronos-base
    title: "NeoQuasar/Kronos-base model card"
    author: NeoQuasar
    last_modified: 2025-09-09
  - id: moirai2
    resource: https://huggingface.co/Salesforce/moirai-2.0-R-small
    title: "Salesforce/moirai-2.0-R-small model card"
    author: Salesforce
    last_modified: 2026-01-29
  - id: moirai11
    resource: https://huggingface.co/Salesforce/moirai-1.1-R-large
    title: "Salesforce/moirai-1.1-R-large model card"
    author: Salesforce
    last_modified: 2026-08-03
  - id: timesfm
    resource: https://huggingface.co/google/timesfm-2.5-200m-pytorch
    title: "google/timesfm-2.5-200m-pytorch model card"
    author: Google
    last_modified: 2025-10-02
  - id: timesfm-repo
    resource: https://github.com/google-research/timesfm
    title: "google-research/timesfm README (TimesFM 2.5 context ceiling)"
    author: Google
    last_modified: 2026-08-03
  - id: ttm
    resource: https://huggingface.co/ibm-granite/granite-timeseries-ttm-r2
    title: "ibm-granite/granite-timeseries-ttm-r2 model card"
    author: IBM
    last_modified: 2024-10-01
  - id: chronos-t5
    resource: https://huggingface.co/amazon/chronos-t5-large
    title: "amazon/chronos-t5-large model card"
    author: Amazon
    last_modified: 2025-02-14
  - id: hf-listing
    resource: https://huggingface.co/models?pipeline_tag=time-series-forecasting&sort=downloads
    title: "Hugging Face time-series-forecasting models by downloads"
    author: Hugging Face
    last_modified: 2026-08-03
  - id: hf-finance-datasets
    resource: https://huggingface.co/datasets?search=finance&sort=downloads
    title: "Hugging Face datasets search: finance"
    author: Hugging Face
    last_modified: 2026-08-03
---

# Rule

**Treat zero-shot financial forecasting with general TSFMs as out-of-domain transfer that you must validate yourself.** Of the general TSFMs whose model cards describe their pretraining mix, none lists financial market data (Chronos-T5: public time-series + Gaussian-process synthetic; Chronos-2: Chronos/GIFT-Eval/synthetic; TimesFM: Wikimedia pageviews/Google Trends/synthetic) — the lone exception is IBM Granite TTM, which lists Bitcoin data in its pretraining mix.[^ttm] Moirai's cards describe no pretraining mix at all, so it cannot be cleared either way.[^moirai11] The model cards for Chronos-2, Chronos-T5, TimesFM 2.5, and Granite TTM say nothing at all about financial forecasting suitability — silence, not endorsement.[^chronos2][^chronos-t5][^timesfm][^ttm] "Validate yourself" means the book-canon gate, not eyeballing plots: chronological splits and beating the last-value naive baseline ([recurrent forecasting](../foundations/recurrent-forecasting.md)).

**Default general-purpose pick: Chronos-2.** As of August 2026 it is the download leader of the HF time-series category: 120M-parameter encoder-only, Apache 2.0, 28.4M downloads/month, handling univariate, multivariate, and covariate-informed zero-shot forecasting in one architecture.[^chronos2] Envelope: 8,192-token max context, up to 1,024 prediction steps, quantile forecasts, past-only and known-future covariates, 300+ forecasts/second on an A10G.[^chronos2] Monthly download counts suggest the Chronos/AutoGluon stack is the most common deployment path (chronos-2 28.4M/mo; autogluon mirrors 13.7M/mo and 12M/mo; next non-Amazon entries are far behind; snapshot 2026-08-03).[^hf-listing] Do not anchor new work on Chronos-T5: its own card recommends chronos-2 and notes Chronos-Bolt is up to 250x faster with ~5% lower error.[^chronos-t5]

**Finance-native pick: Kronos.** On the HF time-series-forecasting listing (snapshot 2026-08-03), the NeoQuasar Kronos family is the only finance-native TSFM with visible traction: pre-trained on 12B+ K-line (OHLCV) records from 45 global exchanges, MIT license, specialized OHLCV tokenizer, 102.3M params (base), intended for price/volatility forecasting and synthetic financial data, zero-shot or fine-tuned.[^kronos] Its tokenizer shows 2.57M downloads/month, base 1.41M/mo, small 1.08M/mo — top ~15 of the whole category.[^hf-listing] Caveats: max context is only 512 for Kronos-small/base and the predictor silently truncates longer lookbacks, and despite being finance-native the card ships no investment-advice or trading disclaimer.[^kronos]

**Licensing gate before anything else.** Chronos-2 and TimesFM are Apache 2.0, but Salesforce Moirai (both the 1.1-R and 2.0-R families) is CC-BY-NC-4.0 and explicitly "for research purposes only" — a trading desk cannot deploy Moirai commercially without separate licensing.[^moirai2][^moirai11] Among the six model cards surveyed here, Moirai's are the only ones carrying an explicit high-stakes warning (evaluate accuracy/safety/fairness concerns before deploying, particularly in high-risk scenarios).[^moirai11] TimesFM 2.5 (Apache 2.0, 200M, decoder-only, context configurable up to 16K points — the card's quickstart ships at 1,024) states it "is not an officially supported Google product."[^timesfm][^timesfm-repo]

**Granite TTM fine print for daily-bar equity work:** r2 supports only minutely-to-hourly resolutions (daily/weekly added only in r2.1), every channel must be externally standard-scaled before inference, and padding/upsampling to fake longer context degrades performance.[^ttm]

**Benchmark scarcity:** financial evaluation sets on HF are mostly NLP/QA-oriented (financebench-style); forecasting-specific financial benchmarks remain scarce, so vendor-neutral zero-shot evidence on financial series is thin.[^hf-finance-datasets]

**Scope note:** quantitative-finance ML is listed as uncovered in the catalog's [scope boundary](../foundations/scope-boundary.md) ("expedition #1, in progress"); this draft begins carving out that area, and the boundary concept must be revisited when this concept is verified and promoted.

# Open questions

- No scout-gathered evidence compares zero-shot TSFMs against qlib-style supervised baselines on cross-sectional IC/RankIC; whether any TSFM produces a tradable alpha signal (as opposed to plausible point forecasts) is unestablished in the sourced material.
- Kronos's published traction is download-based; independent benchmark results for its zero-shot forecasting quality were not found by scouts.

[^chronos2]: amazon/chronos-2 model card (source: chronos2). Parameter count, license, context/prediction envelope, covariate support, "over 300 time series forecasts per second on a single A10G GPU", and pretraining mix. Download figure is HF's 30-day rolling count, read 2026-08-03.
[^chronos-t5]: amazon/chronos-t5-large model card (source: chronos-t5). Recommends amazon/chronos-2; Chronos-Bolt "up to 250 times faster" with "5% lower error"; pretraining = public time-series corpora + Gaussian-process synthetic.
[^kronos]: NeoQuasar/Kronos-base model card (source: kronos). 12B+ K-line records from 45 exchanges, MIT, 102.3M params, max_context 512 with automatic truncation of longer lookbacks; no financial-risk disclaimer present on the card.
[^moirai2]: Salesforce/moirai-2.0-R-small model card (source: moirai2). cc-by-nc-4.0; "This release is for research purposes only."
[^moirai11]: Salesforce/moirai-1.1-R-large model card (source: moirai11). cc-by-nc-4.0; "evaluate and address potential concerns related to accuracy, safety, and fairness before deploying this model", "particularly for high-risk scenarios"; card does not describe the pretraining corpus.
[^timesfm]: google/timesfm-2.5-200m-pytorch model card (source: timesfm). 0.2B decoder-only, Apache 2.0, pretraining = GiftEvalPretrain + Wikimedia Pageviews + Google Trends + synthetic; "This checkpoint is not an officially supported Google product."
[^timesfm-repo]: google-research/timesfm README (source: timesfm-repo): TimesFM 2.5 "supports up to 16k context length, up from 2048"; the HF card's max_context=1024 is a quickstart configuration value, not the model ceiling.
[^ttm]: ibm-granite/granite-timeseries-ttm-r2 model card (source: ttm). Bitcoin (Zenodo) in the r2 pretraining list; r2 = minutely/hourly resolutions with daily/weekly added in r2.1; per-channel external standard scaling required; upsampling/zero-prepending "not recommended and will impact the model performance".
[^hf-listing]: HF time-series-forecasting models sorted by downloads (source: hf-listing), snapshot 2026-08-03. All download figures are HF 30-day rolling counts.
[^hf-finance-datasets]: HF dataset search "finance" sorted by downloads (source: hf-finance-datasets), snapshot 2026-08-03.
