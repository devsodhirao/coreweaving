# Publication checks and progress-display repair

October 30, 2026. Follow-up to the owner's Claude-in-Chrome review. This pass
checks public access and trace interpretation, and repairs the misleading
completion icon during research. It makes no new model requests.

## Progress display

The app used a Streamlit status context manager inside a polling fragment. Ending
each render automatically marked the status complete, even though the background
job was still running. The existing pending-work test reproduced this:
`complete != running`.

The app now writes into the status container without ending a status context.
The indicator stays running during research and verification, then disappears
when the answer arrives. All **430 tests**, Ruff and whitespace checks pass.
A deliberately pending local job was rendered through the actual app on desktop
1440×1000 and mobile 390×844, with no model requests or trace writes.
[Test receipt](local-checks.json) · [Browser receipt](progress-display.json) ·
[Desktop](pending-1440.png) · [Mobile](pending-390.png)

This changes the full source hash to `a6eb10c56bcd`. Agent modules, prompts,
retrieval, dependencies, corpus and evaluation inputs are unchanged from
`a07e5da`. The **12/13 cases and 47/48 assertions** remain measurements of that
build. No new full model regression was run for this display-only change.
[Exact change boundary](change-boundary.json)

## Live generation, caching and trace labels

- The two overlapping walkthroughs produced **35 distinct provider response IDs**.
  All stored model spans lasted **1.631–13.848 seconds**. Our 18 local call receipts
  agree with their remote durations within **0.015 seconds**.
- The public conversation view does display millisecond badges beside some cards
  containing tool calls and a model label. Those badges do not match the model
  request durations. The underlying model timestamps are sound; the precise
  conversation-card calculation has not been established here. Use the individual
  model spans when discussing request latency.
- Anthropic prompt caching is enabled. Our two live turns reported 197,560 cached
  input tokens read across the 18 requests. Each request still generated a fresh
  response. The app retains loaded docs and conversation history; it has no
  saved-answer lookup or preset-answer replay.
- The provider's `user` message role contains both human input and application
  budget/repair instructions. The trace preserves the role actually sent to the
  provider. The turn root identifies the human question; a chat span's User-message
  count is not a count of messages typed by the human. More explicit origin
  metadata is a possible future improvement, not an implemented feature.
- Source passages intentionally show the exact stored Markdown as text. The
  document title is linked separately. Rendering those passages as plain text
  also avoids fetching embedded images automatically.

[Timestamp comparison](trace-audit.json) · [94-span bounded readback](recent-span-timings.json)

## Public access

A fresh isolated Chrome context began with **zero cookies** and no login. The
public project, the 13-case evaluation with its scores, and the exact two-turn
conversation all loaded with substantive content. The old wandb.ai conversation
link redirects to the matching Forge conversation ID.
[Readback](public-access.json) · [Project](project.png) ·
[Evaluation](evaluation.png) · [Conversation](conversation.png)

GitHub publication and the two previously broken email links are checked
separately after pushing the reviewed commits. The earlier 404 evidence remains
in [the pre-publication packet](../email-contract-v1/publication-check.json).

## Scope and remaining limits

The overview can take about a minute, even though the recorded regression's
median agent execution time is 31.46 seconds. These are different measurements.
The model-family, judge-calibration and single-run limits remain unchanged.
The reset-only expired-download console error remains documented in the
[walkthrough packet](../email-contract-v1/README.md#remaining-browser-issue).

New API spend for this follow-up is **$0**. The preceding Codex walkthrough cost
$0.973135; the owner reports about $0.92 for the separate Claude walkthrough.
No human labels were inferred or added, and no prior results or tags were changed.
