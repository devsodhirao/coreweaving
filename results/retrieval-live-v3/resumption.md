# Resume after a judge-format failure

The original run stopped after five delivered answers and four valid grades.
Readback of the fifth judge response shows `stop_reason=end_turn` and prose,
with no `record_grade` tool call. It used 605 output tokens; this was neither
truncation nor a provider-credit failure. The parser correctly rejected it.
The original answer, invalid score and incomplete summary remain unchanged.

Under the owner's instruction to finish the experiments, retry **only the grade
of that stored answer**, with the identical question, references, rubric, judge
model and schema. Do not regenerate it or parse the prose as a valid grade.
Then continue the unrun suffix of the original order. Keep the same total $20
allowance including the original $1.6703862. This is a disclosed operational
resumption, not a fresh uninterrupted comparison.

If a later judge produces the same delivery error, allow one unchanged grading
retry for that saved answer and preserve both attempts. Two failed grades for
one answer stop the run. Provider errors, unknown usage, runtime drift and budget
exhaustion still stop immediately. A valid failing quality grade is never retried.
`completion.json` combines valid grades without overwriting `summary.json`.

This changes experiment recovery, not the app, its release checker, the judge's
acceptance rules or any quality criterion. The grade retry may have warm provider
state; its added cost is counted and judge time is excluded from agent latency.
