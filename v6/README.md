# Genesis V6 – Experimental Suite & Structural-Behavioral Lag Investigation

Genesis V6 is an experimental research framework designed to investigate the **structural-behavioral lag hypothesis** identified in expert critiques of Genesis V5.

---

## 🔬 Core Hypothesis

In Genesis V5, populations exhibit a delayed onset of behavioral innovations relative to structural genome expansions. Rather than treating this lag as an inefficiency or bug, **Genesis V6 tests whether structural expansion is a necessary complexification phase**:
> *Agents must build internal structural capacity (scaffolding) before they can express novel behavioral dynamics in open-ended environments.*

---

## 🧪 Experiments

### Phase 1: Constrained Ceiling Ablation Study (`run_constrained_ceiling.py`)
This study tests whether agents can continue to complexify behaviorally when structural node growth is artificially capped.

- **Control Condition**: Standard V5 evolution (unconstrained CPPN node additions).
- **Constrained Condition**: Capped at `max_nodes = 52` (the fixed-environment baseline ceiling).
- **Evaluated Metrics**:
  - `Action Entropy`: Shannon entropy of action sequences ($H = -\sum p_i \log_2 p_i$).
  - `GAC` (Genetic Activity Coefficient): Proportion of genome innovations persisting $>500$ generations.
  - `Species Count`: Dynamic NEAT compatibility-distance speciation.
  - `ANNEX`: Accumulated Novel Environments Explored counter.

### Phase 2: Transfer Shock (Future)
- `run_transfer_shock.py`: Evaluates agent resilience and behavioral adaptation when abruptly transferred between disparate Gray-Scott reaction-diffusion environments.

### Phase 3: Active Environment Co-Evolution & PATA-EC (Future)
- `run_active_environment.py`: POET-driven active environment generation coupled with continuous PATA-EC fitness profiling.

---

## 🚀 How to Run

### 1. Run Quick Verification Test (100 Generations)
```bash
python v6/quicktest_v6.py
```
or
```bash
python genesis_engine_v6/quicktest_v6.py
```

### 2. Run Full Constrained Ceiling Study (10,000 Generations)
```bash
python genesis_engine_v6/experiments/run_constrained_ceiling.py
```

---

## 📂 File Structure

```
genesis_engine_v6/
├── configs/
│   └── v6_default_config.yaml      # Default hyper-parameter definitions
├── experiments/
│   ├── run_constrained_ceiling.py  # Main ablation experiment runner
│   ├── run_transfer_shock.py       # (Future phase)
│   └── run_active_environment.py   # (Future phase)
├── src/
│   ├── v6_agent.py                 # V6Agent with node cap logic
│   ├── v6_substrate.py             # Gray-Scott substrate with secretion physics
│   ├── v6_speciation.py            # NEAT species assignment
│   ├── v6_metrics.py               # Action entropy, GAC, and ANNEX metrics
│   └── v6_pata_ec.py               # (Future phase)
├── results/
│   └── constrained_ceiling.csv     # Logged metrics across conditions
└── quicktest_v6.py                 # Fast 100-generation verification
```

---

## 📊 Results Logging

Output metrics are appended to `v6/results/constrained_ceiling.csv` with the following fields:
`Generation, Condition, AvgNodes, ActionEntropy, GAC, SpeciesCount, ANNEX, AvgEdges`
