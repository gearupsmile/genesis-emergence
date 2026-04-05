# Quick Verification Log

## V1 Execution
```
Command: python genesis_engine_v1/simulator.py --cycles 100 --with-agents --no-snapshots
[2026-04-06 01:17:35] Initialized with pattern: random
[2026-04-06 01:17:35] Grid size: (256, 256)
[2026-04-06 01:17:35] Parameters: F=0.0367, k=0.0649, Du=0.16, Dv=0.08
[2026-04-06 01:17:35] Agent system enabled: spawned 50 agents (max: 1000)
[2026-04-06 01:17:35] Starting simulation for 100 cycles
[2026-04-06 01:17:43] Cycle 100/100 | V: [0.000, 0.405] mean=0.022 | Mass error: 0.114868 | 12.4 cycles/sec | Agents: 998 (births: 1868, deaths: 781) Energy: 25.7
[2026-04-06 01:17:43] Checkpoint saved: checkpoint_000100.npz
[2026-04-06 01:17:43] Simulation completed successfully in 8.2 seconds
[2026-04-06 01:17:43] Average: 12.3 cycles/second

============================================================
FINAL STATISTICS
============================================================
cycle: 100
U_min: 0.0
U_max: 0.9999257322855504
U_mean: 0.8854458508377838
U_std: 0.14810402040454343
V_min: 0.0
V_max: 0.4045721100101864
V_mean: 0.0218515620542045
V_std: 0.05337258150899667
total_mass: 59460.643251289344
mass_conservation_error: 0.11486843676493635
stability_warnings: 0
total_elapsed_seconds: 8.162253379821777
average_cycles_per_second: 12.251518710165733
agent_population: 998
agent_total_births: 1868
agent_total_deaths: 781
agent_avg_energy: 25.70991785018601
agent_avg_age: 60.95390781563126
============================================================

```

**STATUS: PASS**

## V2 Execution
```
Command: python -m pytest genesis_engine_v2/test_minimal_smoke.py
============================= test session starts =============================
platform win32 -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: E:\Anushka\Projects\genesis-emergence
collected 1 item

genesis_engine_v2\test_minimal_smoke.py .                                [100%]

============================== warnings summary ===============================
genesis_engine_v2/test_minimal_smoke.py::test_minimal_smoke
  C:\Users\Lenovo\miniforge3\Lib\site-packages\_pytest\python.py:170: PytestReturnNotNoneWarning: Test functions should return None, but genesis_engine_v2/test_minimal_smoke.py::test_minimal_smoke returned <class 'bool'>.
  Did you mean to use `assert` instead of `return`?
  See https://docs.pytest.org/en/stable/how-to/assert.html#return-not-none for more information.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 1 passed, 1 warning in 1.57s =========================

```

**STATUS: PASS**

## V3 Execution
```
Command: python -m pytest genesis_engine_v3/tests/validate_stage1.py
============================= test session starts =============================
platform win32 -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: E:\Anushka\Projects\genesis-emergence
collected 1 item

genesis_engine_v3\tests\validate_stage1.py .                             [100%]

============================== 1 passed in 4.65s ==============================

```

**STATUS: PASS**

## V4 Execution
```
Command: python -m pytest genesis_engine_v3/tests/test_cppn.py
============================= test session starts =============================
platform win32 -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: E:\Anushka\Projects\genesis-emergence
collected 1 item

genesis_engine_v3\tests\test_cppn.py .                                   [100%]

============================== 1 passed in 2.61s ==============================

```

**STATUS: PASS**

