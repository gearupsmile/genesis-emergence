# Genesis V5: Co-evolutionary Dynamics

Genesis V5 implements the next evolutionary step following V4's foundational structural complexity bounds. This phase integrates **Paired Open-Ended Trailblazer (POET)** style co-evolution.

## Key Features

- **Co-evolution Orchestrator**: Mutates environments and automatically transfers agents between them if a goal-switching threshold is met (`src/coevolution.py`).
- **Expressive CPPN Environments**: Environments are continuous and mapped using Compositional Pattern Producing Networks instead of flat grids (`src/cppn_environment.py`).
- **Advanced Novelty Metrics**: 
  - `PATA-EC` (Performance of All Transferred Agents - Enhanced Criterion) to calculate divergence in task competence.
  - `ANNEX` bounds.

## How to Run

Test the framework:
```bash
python v5/experiments/quicktest_v5.py
```

Run the massive simulation:
```bash
python v5/experiments/run_v5.py
```
