<!-- CDQAI file version: 2.3.6 -->
# Analyst breadcrumbs and severity-aware review priority

The deterministic finding engine remains step 6. Step 7 now adds recorded triggers,
fields worth checking, a priority explanation, and optional local Llama review drafts.
Original evidence and deterministic explanations remain visible and exported.

## What a breadcrumb can establish

Rule evidence identifies the rule, supporting field names, and available coded values.
Structured-model evidence includes up to three observed values outside the cohort's
1st-99th percentile range when available. These comparisons describe unusual values;
they do not establish which field caused an Isolation Forest score. Some unusual
combinations have no individually extreme field, and the dashboard says so.
Narrative scores do not establish that a particular word caused an anomaly.

Each review fact has an E-number. Llama can suggest checks and refer to these facts.
It cannot change a finding, score, rank, or deterministic explanation. A draft is
unverified: valid references and structured output do not prove its prose is correct.
Analysts must compare it with the recorded evidence.

Version 2.3.6 asks Llama for short conversational explanations:
what stood out, what the evidence cannot establish, and a useful next check. Related
base signals are combined rather than repeating one percentile per paragraph.
Derived ensemble summaries are omitted from the prompt when base facts exist, while
remaining visible in the deterministic evidence panel. Recorded sentence-sensitivity
excerpts (up to two, 240 characters each) can supply local context; they remain
protected and are sent only to the verified local Ollama service. They do not prove
a cause or a contradiction. Model outputs are not described as source crash fields.
This change does not implement uncoded-human-factor discovery.

## Local Ollama setup

This feature is off by default. An authorized user configures it privately; an AI
assistant must not run the feature on protected records or inspect the resulting drafts.

1. Have IT disable Ollama cloud features using `OLLAMA_NO_CLOUD=1` in the Ollama
   server environment, or `disable_ollama_cloud: true` in its server configuration,
   and restart Ollama. Verify this locally. Follow the approved network isolation
   policy; CDQAI cannot verify server-side egress controls from the client.
2. Select an already installed local Llama model. Arrange any model download
   separately through approved procedures before processing protected inputs.
3. In the ignored local configuration, set `analyst_guidance.enabled: true`,
   `model` to the exact installed tag, and `local_only_confirmed: true` after the
   local-only server setup is verified. Keep `port: 11434` unless intentionally changed.
4. Run CDQAI yourself locally and inspect the dashboard's Local Llama review draft.

The adapter connects directly to 127.0.0.1, bypasses environment proxies, rejects
redirects, cloud model names, and remote model metadata, and requires a local GGUF
Llama model. Before sending evidence it requires `/api/status` to report cloud
features disabled. Older servers without that endpoint leave guidance unavailable.
This verifies reported status, not firewall controls. It never downloads a model
or falls back to a cloud API. The prompt
contains bounded evidence facts, not the MFN or complete crash narrative. Facts and
drafts are still protected. No prompt/response content is written to application logs.

The default limit is the top 20 actionable findings (configurable from 1 to 100),
with a 60-second default request timeout (the setup helper selects 180 seconds).
A service failure stops optional generation while retaining deterministic reports;
a rejected draft skips that finding and continues. Fixed failure codes are shown
without recording prompts, responses, or exception contents. Disabled/unavailable/not-selected
statuses are visible. Model identity, digest, and generation counts are in run metadata.
This is generation during the local run, not a browser request when expanding a row.

API references: [Ollama chat](https://docs.ollama.com/api/chat),
[installed models](https://docs.ollama.com/api/tags), and
[local-only setup](https://docs.ollama.com/faq#how-do-i-disable-ollama-cloud-features).

## Priority policy

Blank narratives are excluded from semantic model fitting and percentile ranking.
The ensemble renormalizes available model weights. A single available model does
not create additional ensemble or multi-model evidence. Derived summaries do not
inflate agreement/confidence when base evidence is available. Missing/sparse narrative
rules remain unchanged; they remain visible as completeness evidence.

Configure `review_priority.severity_field` to the actual crash-level maximum-severity
column. The default name is `KABCO`, with K/A/B/C/O code meanings supplied by the
project owner. If that field/code is unavailable, severity is unknown; it is not
assumed to be property-damage-only. Numeric codes require a separately reviewed mapping.

| Crash code | Narrative-model priority multiplier | Missing/sparse narrative bonus |
|---|---:|---:|
| K | 1.0 | +1.5 |
| A | 1.0 | +1.0 |
| B or C | 0.75 | +0.25 |
| O | 0.5 | +0.0 |
| Unknown | 1.0 | +0.0 |

These are provisional, editable review-policy choices, not empirically calibrated
weights. The multiplier affects the narrative model's severity/confidence contribution
to finding priority, not the raw anomaly percentile. Structured and deterministic
substantive evidence remain eligible regardless of crash severity. Completeness adds
only the bounded bonus once; it cannot independently add a model-agreement bonus or
raise confidence. Completeness-only findings remain outside the actionable queue.

Review the displayed rationale and compare representative findings privately before
adopting these weights. A severe crash is not automatically a data-quality error.

## Verification scope

Tests use fabricated records and mocked Ollama responses. They cover missing narrative
handling, severity mappings, priority, independent signal counting, draft separation,
cloud/remote rejection, malformed references, and HTML escaping. Real Llama output
quality and production-record ranking require the user's authorized local evaluation.
