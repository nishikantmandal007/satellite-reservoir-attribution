"""
D12 tripwire — critical_checks.py must fail closed and stay read-only.
ACCEPT (playbook R5): with data/raw absent -> nonzero exit + FAIL-CLOSED
banner; data/processed byte-identical before/after.

Run: uv run python tests/test_failclosed.py
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent


def snapshot_processed() -> dict[str, str]:
    state = {}
    d = PROJECT / 'data' / 'processed'
    for p in sorted(d.glob('*')):
        if p.is_file():
            state[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return state


def main() -> int:
    failures: list[str] = []
    raw_present = (PROJECT / 'data' / 'raw').exists()

    before = snapshot_processed()
    proc = subprocess.run(
        ['uv', 'run', 'python', 'src/critical_checks.py'],
        cwd=PROJECT, capture_output=True, text=True,
        env={**os.environ, 'TERM': 'dumb'})
    after = snapshot_processed()
    output = proc.stdout + proc.stderr

    if raw_present:
        if proc.returncode not in (0, 2):
            failures.append(f'unexpected exit {proc.returncode} with inputs present')
        else:
            print('PASS ✓  inputs present -> checks executed (exit '
                  f'{proc.returncode})')
    else:
        if proc.returncode == 0:
            failures.append('fail-OPEN detected: exit 0 despite data/raw absent')
        elif 'FAIL-CLOSED' not in output:
            failures.append('nonzero exit but no FAIL-CLOSED banner')
        else:
            print('PASS ✓  data/raw absent -> nonzero exit + FAIL-CLOSED listing')

    if before != after:
        changed = [k for k in set(before) | set(after)
                   if before.get(k) != after.get(k)]
        failures.append(f'data/processed modified: {changed} — must be read-only')
    else:
        print(f'PASS ✓  read-only ({len(before)} processed files untouched)')

    if failures:
        for f in failures:
            print(f'FAIL ✗  {f}')
        print('RESULT: FAILURE')
        return 1
    print('RESULT: ALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
