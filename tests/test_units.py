"""
Unit tests for metric definitions and unit conversions.
Covers RECOVERY_ROADMAP.md D10: v1 pbias() returned normalised MAE mislabeled
as PBIAS; v2 must implement true PBIAS = 100*sum(pred-obs)/sum(obs).
Also covers D2 groundwork: BCM <-> cm LWE mass conversion.

Run: uv run python tests/test_units.py
Exit code 0 only if every check passes (fail-closed by design).
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent.parent


def load_module(name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(name, PROJECT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


m03 = load_module('m03_deleak', 'src/03b_xgboost_deleak.py')
mb2 = load_module('mb2_grace', 'src/fix_b2_grace_raw_units.py')

FAILURES = []


def check(label: str, cond: bool):
    status = 'PASS ✓' if cond else 'FAIL ✗'
    print(f"  {status}  {label}")
    if not cond:
        FAILURES.append(label)


print("== NSE ==")
check("perfect prediction -> 1.0",
      abs(m03.nse([1, 2, 3, 4], [1, 2, 3, 4]) - 1.0) < 1e-12)
check("mean prediction -> 0.0",
      abs(m03.nse([1, 2, 3], [2.0, 2.0, 2.0])) < 1e-12)
check("hand-computed case", abs(m03.nse(
    [1.0, 2.0, 3.0, 4.0], [1.5, 2.5, 2.5, 3.5]) - (1 - 1.0 / 5.0)) < 1e-12)

print("== KGE ==")
check("perfect prediction -> 1.0",
      abs(m03.kge([1, 2, 3], [1, 2, 3]) - 1.0) < 1e-12)
# obs=[1,2,3] pred=[2,4,6]: r=1, alpha=2, beta=2 -> 1-sqrt(0+1+1)=0
check("scaled-by-2 -> 0.0", abs(m03.kge([1, 2, 3], [2, 4, 6])) < 1e-12)

print("== PBIAS (TRUE definition) ==")
check("obs=[10,20,30] pred=[9,18,27] -> -10%",
      abs(m03.pbias_true([10, 20, 30], [9, 18, 27]) + 10.0) < 1e-12)
check("over-prediction positive",
      abs(m03.pbias_true([10, 20, 30], [11, 22, 33]) - 10.0) < 1e-12)
check("zero-sum obs guard -> NaN",
      np.isnan(m03.pbias_true([-5, 5, -5, 5], [-4, 4, -6, 6])))
check("v1-style nMAE_std is NOT equal to true PBIAS on asymmetric errors",
      abs(m03.nmae_std([10, 20, 30], [15, 20, 25])
          - m03.pbias_true([10, 20, 30], [15, 20, 25])) > 1e-9)

print("== unit conversions ==")
check("cm_per_bcm(23370) ~ 4.279 cm/BCM",
      abs(mb2.cm_per_bcm(23370.0) - 4.279) < 0.001)
check("cm_per_bcm(19600) ~ 5.102 cm/BCM",
      abs(mb2.cm_per_bcm(19600.0) - 5.102) < 0.001)

print()
if FAILURES:
    print(f"RESULT: {len(FAILURES)} FAILURE(S)")
    sys.exit(1)
print("RESULT: ALL PASS")
sys.exit(0)
