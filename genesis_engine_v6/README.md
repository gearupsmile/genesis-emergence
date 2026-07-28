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

**Key Finding**: Constrained agents did NOT stagnate. They rewired densely (815 edges in 52 nodes) and achieved **65× higher action entropy** (0.1114 vs 0.0017) and **5 species** (vs 4 in control).

---

### Phase 2: Transfer Shock Experiment (`run_transfer_shock.py`)
Tests whether dense internal rewiring (52 nodes, 815 edges) acts as an **evolvability reserve**, allowing constrained agents to adapt faster to radical reaction-diffusion environmental shifts than large unconstrained structures (V5: 467 nodes), static structures (V4: 123 nodes), or naive agents (12 nodes).

- **Conditions**:
  - `Condition A`: V5 (467 nodes)
  - `Condition B`: V6 Constrained (52 nodes, 815 edges)
  - `Condition C`: V4 (123 nodes)
  - `Condition D`: Naive (12 nodes)
- **Shock Environments**:
  - `Shock A`: High diffusion ($D_u=0.32, D_v=0.16$), low feed ($F=0.02, k=0.065$)
  - `Shock B`: Low diffusion ($D_u=0.04, D_v=0.02$), high kill ($F=0.035, k=0.12$)
  - `Shock C`: Chaotic regime ($D_u=0.12, D_v=0.06$), temporal variation ($F=0.018, k=0.050$)
- **Evaluated Metrics**:
  - `Adaptation Speed`: Generations to reach 80% of peak performance.
  - `Survival Rate`: Proportion of population surviving per interval.
  - `Action Entropy`: Behavioral exploration under shock.
  - `Energy Efficiency`: Energy gained vs energy expended ratio.
  - `ANNEX`: Open-ended innovation discovery accumulator.

---

## 🚀 How to Run

### 1. Run Quick Verification Test (100 Generations)
```bash
python genesis_engine_v6/experiments/quicktest_transfer_shock.py
```

### 2. Run Full Transfer Shock Experiment (5,000 Generations)
```bash
python genesis_engine_v6/experiments/run_transfer_shock.py
```

### 3. Generate Analysis & Plot Summaries
```bash
python genesis_engine_v6/analysis/analyze_transfer_shock.py
```

---

## 📂 File Structure

```
genesis_engine_v6/
├── analysis/
│   └── analyze_transfer_shock.py   # Analysis & summary plot generator
├── configs/
│   └── v6_default_config.yaml      # Default hyper-parameter definitions
├── experiments/
│   ├── run_constrained_ceiling.py  # Phase 1 ablation experiment runner
│   ├── run_constrained_only.py     # Standalone constrained condition runner
│   ├── merge_and_plot.py           # Phase 1 plot merger
│   ├── run_transfer_shock.py       # Phase 2 transfer shock experiment runner
│   └── quicktest_transfer_shock.py # Fast 100-generation quicktest runner
├── src/
│   ├── v6_agent.py                 # V6Agent with node cap & checkpoint loading
│   ├── v6_substrate.py             # Gray-Scott substrate with secretion physics
│   ├── v6_transfer_shock_envs.py   # Transfer shock environment generators
│   ├── v6_transfer_metrics.py      # Adaptation speed & transfer metrics
│   ├── v6_speciation.py            # NEAT species assignment
│   └── v6_metrics.py               # Action entropy, GAC, and ANNEX metrics
└── results/
    ├── constrained_ceiling.csv     # Phase 1 CSV dataset
    ├── constrained_ceiling_summary.png # Phase 1 summary plot
    ├── transfer_shock.csv          # Phase 2 CSV dataset
    └── transfer_shock_summary.png  # Phase 2 summary plot
```
