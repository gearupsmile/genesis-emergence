# Genesis Engine v3

**Phase 3.3: Extended Agency & Secretion Physics**

Genesis Engine v3 extends the v2 architecture with active environmental modification (niche construction), historical complexity tracking, and experimental controls.

## New Features

### 1. Secretion Physics (Niche Construction)
Agents can now actively modify their local environment by secreting a chemical substance `S`.
- **Mechanism**: Agents pay metabolic cost to deposit `S` into the substrate.
- **Physics**: The `Substrate` class handles diffusion and decay of `S` over time.
- **Goal**: Enable *active inference* where agents change the world to fit their internal models (or simply mark territory).

### 2. AIS Archive (Historical & Environmental Memory)
The Artificial Immune System (AIS) is enhanced with an evolutionary archive.
- **Function**: Successfully reproducing agents (parents) archive their **Genome** and a **Local Environment Snapshot**.
- **Utility**: Allows analysis of the *coupled* evolution of agent traits and environmental states.
- **Novelty**: Prevents cycling by tracking historical states.

### 3. LZ Complexity on Action Traces (Behavioral Complexity)
A new metric to quantify the complexity of agent behaviors.
- **Trace**: Agent actions ('M', 'S', 'I') are recorded over their lifetime.
- **Metric**: **Lempel-Ziv (LZ76) Complexity** is calculated on the action string.
- **Interpretation**:
    - Low LZ: Repetitive, simple behavior (looping).
    - High LZ: Random or complex, adaptive behavior.
    - Captures the *emergence* of structured behavior.

### 4. Sham Control Mode (Experimental Rigor)
A built-in experimental control to isolate the effects of environmental modification.
- **Global Flag**: `enable_secretion=True/False`.
- **Mechanism**:
    - **Real Mode**: Agents secrete, pay cost, and `S` accumulates/diffuses.
    - **Sham Mode**: Agents "secrete" and **pay the same metabolic cost**, but **No `S` is deposited**.
- **Purpose**: proves that any fitness advantage in Real mode is due to the *environmental effect* of secretion, not just the metabolic burden or behavioral pattern.

## Usage

### Running an Experiment (Real vs Sham)
```bash
# Run Real Condition (Secretion Enabled)
python experiments/v3_experiments/run_sham_comparison.py --mode real --generations 2000

# Run Sham Condition (Secretion Disabled)
python experiments/v3_experiments/run_sham_comparison.py --mode sham --generations 2000
```

### Analyzing Results
```bash
# Compare Logs
python analysis/compare_runs.py --real logs/test_real/ --sham logs/test_sham/ --output comparison.png
```

## Architecture Updates
- **`engine/substrate.py`**: Manages chemical fields.
- **`engine/structurally_evolvable_agent.py`**: Added `secrete()` action and `step()` trace return.
- **`engine/behavior/behavioral_tracker.py`**: Calculates LZ complexity.
- **`engine/ais.py`**: Added `AISArchive`.

---
*Built upon Genesis v2 core (CodonTranslator, KernelAgent, AIS).*
