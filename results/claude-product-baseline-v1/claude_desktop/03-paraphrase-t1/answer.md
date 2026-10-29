Use the `postprocess_inputs` and `postprocess_output` parameters on the `@weave.op` decorator. They change only what Weave logs: your function still receives the real arguments and runs exactly as written.

The two hooks work like this:
- **`postprocess_inputs`** receives a dict mapping argument names to their values and returns the dict that Weave should record.
- **`postprocess_output`** receives whatever your function returned and returns the version that Weave should record.

```python
from dataclasses import dataclass, replace
from typing import Any
import weave

@dataclass
class LoginResult:
    user: str
    session_token: str

def hide_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    # Mask the password (or drop the key entirely)
    return {**inputs, "password": "REDACTED"}

def hide_output(output: LoginResult) -> LoginResult:
    # Build a new object rather than editing the original
    return replace(output, session_token="REDACTED")

@weave.op(postprocess_inputs=hide_inputs, postprocess_output=hide_output)
def login(user: str, password: str) -> LoginResult:
    token = authenticate(user, password)  # uses the real password
    return LoginResult(user=user, session_token=token)

weave.init("your-team/your-project")
login(user="alice", password="hunter2")
```

The trace will show `password: "REDACTED"` and a redacted `session_token`. The function itself still gets the real password.

Two practical notes:
- **Build a new object in `postprocess_output`.** If you modify the returned object in place, you may also change what your calling code gets back. `dataclasses.replace` creates a copy, which is the same approach the docs' example takes.
- **This is Python-only.** The TypeScript SDK doesn't support it yet.

If you want broader, automatic scrubbing of personal data across all traces, rather than per-function control, the docs have a separate guide called "Redact PII from traces."