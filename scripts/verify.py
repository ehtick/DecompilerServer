#!/usr/bin/env python3
"""Run the repository's format and Release test gates with quiet output."""
import os
from pathlib import Path
import signal
import subprocess
import sys
from datetime import datetime

root = Path(__file__).resolve().parent.parent
log_dir = root / "artifacts" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_path = log_dir / f"verify-{datetime.now():%Y%m%d-%H%M%S}.log"
child = None


def cancel(signum, _frame):
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
    print(f"Cancelled; full log: {log_path}", file=sys.stderr)
    sys.exit(128 + signum)


signal.signal(signal.SIGINT, cancel)
signal.signal(signal.SIGTERM, cancel)
with log_path.open("w") as log:
    for step, command in [
        ("format", ["dotnet", "format", "DecompilerServer.sln"]),
        ("Release tests", ["dotnet", "test", "-c", "Release"]),
        ("diff check", ["git", "diff", "--check"]),
    ]:
        log.write(f"\n{step}\n")
        log.flush()
        try:
            child = subprocess.Popen(command, cwd=root, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            result = child.wait()
        except OSError as error:
            log.write(f"{error}\n")
            result = 1
        if result:
            log.flush()
            print(f"Failed: {step}\nFull log: {log_path}", file=sys.stderr)
            print("\n".join(log_path.read_text().splitlines()[-20:]), file=sys.stderr)
            sys.exit(1)
print("ok")
