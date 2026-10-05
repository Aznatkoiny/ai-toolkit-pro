---
type: Decision Rule
title: "Tool error text is a tunable part of the agent harness, not a message to the operator"
description: >
  In a 168-scenario tool-failure harness, appending a next step the agent cannot execute to an
  otherwise identical error message cut expired-credential recovery by 0.375 absolute averaged over
  five models, and mechanically filtering that step back out restored recovery exactly to the
  cause-only level. Where the step IS executable, naming the in-tool call is worth up to +0.817.
  A survey of 150 MCP servers finds 477 of 3,001 failure paths carry a next step that depends on
  caller state the agent cannot observe. Rewrite tool error text at the harness boundary.
tags: [agents, tool-use, mcp, error-handling, reliability, harness]
tier: frontier
applies_to:
  - writing or reviewing the error messages a tool, MCP server, or API returns to an agent
  - debugging an agent that fails to recover from authentication, permission, or rate-limit failures
  - wrapping a third-party MCP server or tool whose error text you do not control
  - deciding where to spend effort when agent reliability is below target
status: draft
stale_after: 2027-01-05
generated:
  by: expedition/weekly-2026-10-05
  at: 2026-10-05T00:42:00Z
sources:
  - id: toolerr-readme
    resource: https://github.com/WenJing95/tool-error-text/blob/be2affff3a8855d8b89dc6f951ae842e9d70f1a2/README.md
    title: "tool-error-text — data and code for 'MCP Error Messages Written for Developers Hurt the Most Capable Agents Most'"
    author: "GitHub identity WenJing95 (paper author list is not stated in the repository)"
    last_modified: 2026-09-28
  - id: toolerr-contrasts
    resource: https://github.com/WenJing95/tool-error-text/blob/be2affff3a8855d8b89dc6f951ae842e9d70f1a2/experiment/results/contrasts.csv
    title: "tool-error-text — per-condition contrasts with 95% bootstrap intervals (contrasts.csv)"
    author: "GitHub identity WenJing95"
    last_modified: 2026-09-28
  - id: toolerr-recovery
    resource: https://github.com/WenJing95/tool-error-text/blob/be2affff3a8855d8b89dc6f951ae842e9d70f1a2/experiment/results/recovery.csv
    title: "tool-error-text — per-model, per-condition recovery rates (recovery.csv)"
    author: "GitHub identity WenJing95"
    last_modified: 2026-09-28
  - id: toolerr-survey
    resource: https://github.com/WenJing95/tool-error-text/blob/be2affff3a8855d8b89dc6f951ae842e9d70f1a2/survey/error_messages.csv
    title: "tool-error-text — 3,001 annotated failure paths across 150 MCP servers (error_messages.csv)"
    author: "GitHub identity WenJing95"
    last_modified: 2026-09-28
  - id: toolerr-analyze
    resource: https://github.com/WenJing95/tool-error-text/blob/be2affff3a8855d8b89dc6f951ae842e9d70f1a2/experiment/code/analyze.py
    title: "tool-error-text — analysis script stating the bootstrap and run protocol (analyze.py)"
    author: "GitHub identity WenJing95"
    last_modified: 2026-09-28
---

# Rule

**Treat the text a tool returns on failure as a tunable part of your agent harness, and rewrite it at the boundary before it reaches the model. Two edits carry almost all of the measured effect: strip any next step the agent cannot physically execute, and where a step IS executable, name the in-tool call rather than describing the goal.** The error string is conventionally written for a human operator reading a terminal. When an agent is the reader, a human-oriented next step is not merely unhelpful — it measurably displaces recovery behavior the model would otherwise have produced.

**An unexecutable next step is actively harmful, not neutral.** In a 168-scenario harness (7 failure types × 24 scenarios) the same underlying failure was presented under six error texts differing only in their final sentence. Condition `C` states the cause alone; condition `E2` appends a shell command the agent has no way to run (for scenario `S001`, `"Please run: reddit-mcp-buddy --auth"` against `C`'s `"send_message rejected the call: no authenticated session exists."`).[^toolerr-readme] On expired credentials, `C − E2` averaged over five models is **0.375 absolute** (95% interval 0.286–0.461).[^toolerr-contrasts] That is a third of the achievable recovery rate destroyed by one appended sentence that adds no false information — it is simply addressed to the wrong reader.

**The mechanism is displacement, and filtering is a complete fix.** The same study re-ran the degraded texts after mechanically removing the unexecutable step. Recovery came back to the cause-only level exactly: `E2f − E2` = **+0.375** (0.269–0.478) and `C − E2f` = **0.000** (−0.047 to +0.047).[^toolerr-contrasts] A point estimate of zero with an interval that tight is the useful part of this result: it says the harm is entirely attributable to the presence of the unexecutable instruction, not to anything else about the message. **So you do not need to rewrite your error strings at the source to capture this.** A filter in the harness that drops operator-directed steps from tool output recovers the full difference, which makes this actionable against third-party MCP servers whose text you do not own.

**Where the step is executable, state it as a call — and this is where the largest single effect sits.** Pooled over the three failure classes the study labels *invisible* (the agent cannot infer the remedy from the error alone), adding an executable next step beats cause-only text by `D − C` = **+0.281** (0.247–0.316).[^toolerr-recovery] On rate-limit failures, naming the concrete call beats a bare wait-and-retry instruction by `D2 − D1` = **+0.817** (0.747–0.878).[^toolerr-contrasts] **Check your own cause-only floor before deciding this is optional:** in the released per-model data the cause-only recovery rate on `permission_denied` is **0.0 for all five models**, and on `quota_exhausted` it ranges 0.0–0.111.[^toolerr-recovery] For those classes the cause text alone recovers essentially nothing, so the next step is not a refinement — it is the entire remedy.

**This is a prevalent defect, not a constructed one.** A survey of 150 MCP servers annotated 3,001 reachable failure paths. Only **949** state any next step at all, and of those **477** depend on caller state not observable from the request (458 do not; 14 are marked uncertain).[^toolerr-survey] So roughly half of the servers that do try to help are issuing steps whose applicability the agent cannot determine, and two thirds of all failure paths say nothing actionable whatsoever. Both halves of the rule above have wide surface area in a typical tool stack.

**The penalty varies enormously across models, so do not generalize a single model's robustness.** On expired credentials the `C − E2` penalty ranges from **0.181** (0.042–0.333) to **0.694** (0.514–0.861) across the five models tested, and the gap between the two extremes is itself significant at **0.514** (0.292–0.722).[^toolerr-contrasts][^toolerr-recovery] Measuring this on one model tells you little about another in the same family.

**Do not carry the source's causal story.** The repository is titled "MCP Error Messages Written for Developers Hurt the Most Capable Agents Most",[^toolerr-readme] and the model with the largest penalty is the one whose name implies the most recent generation. **The released data does not support that ordering.** Overall cause-only recovery across all failure types is 0.597–0.647 for the five models — a 5-point spread in which the *highest* value belongs to a model that takes a middling penalty and the *lowest* belongs to another mid-penalty model; the 0.181–0.694 penalty spread does not track it.[^toolerr-recovery] The paper itself is not reachable from this expedition's network, so whatever capability measure it uses to order the models could not be inspected. **Use the robust finding — the penalty is large, real, and model-dependent — and treat "it hurts stronger models more" as the authors' unverified interpretation.**

# Open questions

- Whether the effect holds outside the OpenAI model family is untested; all five models in the study are from one provider, so provider-level prompt-handling conventions are a plausible confound that this design cannot separate from capability.
- The filtering arm was produced by one model acting as the filter (`filter-gpt-6-luna.jsonl`),[^toolerr-readme] so the measured restoration includes that filter's accuracy. A production harness filter may do better or worse, and the study does not bound the error rate of the filtering step itself.
- Recovery is judged by comparing final environment state against a gold snapshot on the BFCL runtime,[^toolerr-readme] which rewards reaching the right end state. It does not score cost, latency, or the number of tool calls spent getting there, so the rule above is silent on whether better error text also makes recovery cheaper.
- The 0.375 figure is specific to expired credentials. Per-failure-type contrasts for the other six classes are in the released CSVs but were not all inspected here; treat the headline number as a per-class effect, not a harness-wide average.

# Related

- Error-text quality is a harness property, so a measured agent score is partly a measurement of the harness around the model — see [published-result reproducibility](published-result-reproducibility.md) for how much weight an unreproduced published number may carry.

[^toolerr-readme]: `WenJing95/tool-error-text` README at commit `be2affff` (source id: toolerr-readme), repository's single commit dated 2026-09-28. Supplies the title, the directory contents (150 servers, 3,001 annotated failure paths, 168 scenarios with six error texts each, the 949-message filtering test), the BFCL-runtime recovery check, and the identity of the filtering model. The paper's author list is not stated in the repository and the paper itself was not reachable.
[^toolerr-contrasts]: `experiment/results/contrasts.csv` at commit `be2affff` (source id: toolerr-contrasts), re-fetched and read directly on 2026-10-05. Rows quoted verbatim: `expired_auth,C-E2,mean of five models,0.375,0.28611111111111115,0.4611111111111111,24`; `expired_auth,E2f-E2,mean of five models,0.37500000000000006,0.2694444444444445,0.4777777777777778,24`; `expired_auth,C-E2f,mean of five models,0.0,-0.04722222222222222,0.04722222222222223,24`; `quota_exhausted,D2-D1,mean of five models,0.8166666666666668,0.7472222222222222,0.8777777777777778,24`; per-model `expired_auth,C-E2` values 0.181 / 0.347 / 0.389 / 0.694 / 0.264.
[^toolerr-recovery]: `experiment/results/recovery.csv` at commit `be2affff` (source id: toolerr-recovery), re-fetched and read directly on 2026-10-05. Supplies `mean of five models,invisible,,D-C,3240,0.2810185185185185,0.24675925925925923,0.3162037037037037,72`; the cross-model gap row `gpt-6-astra minus gpt-5.5,expired_auth,,C-E2,288,0.5138888888888888,0.2916666666666667,0.7222222222222223,24`; the cause-only (`condition = C`) rates per failure type, including `permission_denied` = 0.0 for all five models and `quota_exhausted` = 0.0–0.111; and the `all` cause-only rates 0.6131 / 0.6230 / 0.5972 / 0.6151 / 0.6468 on which the capability-ordering correction above rests.
[^toolerr-survey]: `survey/error_messages.csv` and `survey/servers.csv` at commit `be2affff` (source id: toolerr-survey). Counts recomputed from the shipped CSVs on 2026-10-05: 150 server rows; 3,001 failure-path rows; `has_next_step` yes 949 / no 2,052; among the 949, `depends_on_caller_state` yes 477 / no 458 / uncertain 14.
[^toolerr-analyze]: `experiment/code/analyze.py` at commit `be2affff` (source id: toolerr-analyze). States the protocol: "The unit of analysis is the scenario (mean of its three runs); intervals are 95% percentile intervals from a scenario bootstrap stratified by failure type, with the same resampled scenarios used for every condition and contrast of a model." Constants give five models, `REPEATS = 3`, seven failure types, `DRAWS = 10000`, `SEED = 20260925`.
