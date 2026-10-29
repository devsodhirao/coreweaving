# Full operational retry on the frozen presentation build

The first attempt in `../presentation-regression-v1` produced no valid grades:
its first judge call timed out and the spending guard withheld remaining calls.
This retry was frozen before execution in [preflight.json](preflight.json).

Run all 13 cases / 48 assertions once, preserving the runtime, snapshot, dataset,
rubric, seed, writer/checker effort and cache settings. No quality-selected
regeneration, prompt fixes or question changes. Keep all failures and read back
saved records after the run. The $7 returned-usage allowance is additional to the
first attempt's $0.24075 known estimate and one unpriced timed-out request. It is
not an invoice cap. If this retry also fails operationally, report that limit;
do not start another full run automatically.

Review final answers separately from the Opus judge. Reused development questions,
one trial per case and the shared writer/checker/judge model family limit the
claims. Passing does not establish SDK compatibility or the auditor's added value.
