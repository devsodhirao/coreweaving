import shutil

import pytest

from coreweaving.sandbox import run_python

pytestmark = [
    pytest.mark.sandbox,
    pytest.mark.skipif(not shutil.which("docker"), reason="Docker required"),
]


def test_code_runs_without_host_credentials_or_network(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-secret-must-not-enter-container")
    result = run_python("""import os, socket
print('credential', 'ANTHROPIC_API_KEY' in os.environ)
print('mean', sum([True, False, True]) / 3)
try:
    socket.create_connection(('1.1.1.1', 443), timeout=1)
    print('network available')
except OSError:
    print('network blocked')
""")
    assert result["exit_code"] == 0
    assert "credential False" in result["output"]
    assert "mean 0.6666666666666666" in result["output"]
    assert "network blocked" in result["output"]


def test_infinite_loop_is_stopped():
    assert run_python("while True: pass", timeout=2)["stopped"] == "timeout"


def test_output_is_bounded():
    result = run_python("while True: print('x' * 1000)", max_output=2048)
    assert result["stopped"] == "output_limit"
    assert len(result["output"]) <= 2048
