"""Run small, offline stdlib examples in a disposable Docker container."""

import os
import selectors
import subprocess
import time
import uuid

IMAGE = "python:3.12-slim@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704"


def run_python(code: str, timeout: float = 8, max_output: int = 12000) -> dict:
    """Run stdlib code offline with fixed container limits and bounded output.

    No host mounts or credentials enter the container. Results describe only this
    execution; the tool cannot validate SDK examples whose packages are absent.
    """
    if len(code.encode()) > 6000:
        return {"error": "Code exceeds the 6 KB limit."}
    name = "coreweaving-" + uuid.uuid4().hex[:12]
    command = [
        "docker",
        "run",
        "--rm",
        "-i",
        "--pull",
        "never",
        "--name",
        name,
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--memory",
        "128m",
        "--cpus",
        "0.5",
        "--pids-limit",
        "32",
        "--user",
        "65534:65534",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=8m",
        IMAGE,
        "python",
        "-I",
        "-B",
        "-",
    ]
    output = bytearray()
    stopped = None
    try:
        process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
    except FileNotFoundError:
        return {"error": "Docker is unavailable. No code was executed."}
    try:
        process.stdin.write(code.encode())
        process.stdin.close()
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            deadline = time.monotonic() + timeout
            while True:
                if time.monotonic() >= deadline:
                    stopped = "timeout"
                    break
                if not selector.select(timeout=0.1):
                    continue
                chunk = os.read(process.stdout.fileno(), 4096)
                if not chunk:
                    break
                output.extend(chunk[: max_output - len(output)])
                if len(output) >= max_output:
                    stopped = "output_limit"
                    break
        if stopped:
            process.kill()
        process.wait(timeout=3)
    finally:
        # Kill the container as well as the CLI, including after cancellation.
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=10)
        if process.poll() is None:
            process.kill()
            process.wait(timeout=3)
        process.stdout.close()
    return {
        "output": output.decode(errors="replace"),
        "exit_code": process.returncode,
        "stopped": stopped,
        "environment": "Python 3.12 standard library; offline container",
        "limitation": "No Weave SDK or remote API calls. This only checks local Python behavior.",
    }
