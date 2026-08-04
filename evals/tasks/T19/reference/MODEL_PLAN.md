# Model Plan — LoRA fine-tuning of Llama-3-8B (out of scope)
Status: OUT-OF-SCOPE — not covered by Deep Learning with Python, 2nd Edition (2021)

## Problem framing
Request: parameter-efficient fine-tuning (LoRA) of a pretrained large language model on 50,000 transcripts.

## Scope notes
The book (2021) predates this technique family; nothing in its 14 chapters covers it.
Recommending a 2021-era recipe as if it solved this request would be misleading.

## Adjacent best-effort (NOT equivalent to what you asked for)
The book covers training Transformer language models from scratch (ch11-12), which shares vocabulary but is NOT the requested technique: it predates LLM fine-tuning, LoRA, and instruction tuning entirely. Consult current PEFT/LoRA literature instead.
