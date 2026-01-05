# Genesis Engine: A Framework for Constraint-Driven Open-Ended Evolution

## Abstract

The **Genesis Engine** is an artificial life research platform engineered for **Open-Ended Evolution (OEE)**. This project documents a paradigm shift from **objective-driven, guided evolution** (v1.0) to **constraint-driven evolution** (v2.0), where system dynamics emerge from agent-environment interactions governed by immutable, physics-like laws.

The core innovation is the **Metabolic Cost Model**—a tunable constraint (`cost = 0.005 × genes^1.5`) that penalizes genomic bloat without prescribing goals. Following an expert critique distinguishing sustained activity from unbounded novelty, the project developed a **three-phase diagnostic framework** (Phases 6-8) and a **three-layer architectural hardening** process. A verified 5,000-generation test confirms genome stability (22.8 ± 2 genes) and performance (40.1 gen/sec), enabling the definitive **200,000-generation "Deep Probe" experiment** to quantitatively test for open-ended trajectories using Phenotypic Novelty & Complexity Trajectory (PNCT) metrics.

**Status:** Phase 6 hardening **COMPLETE**. System verified and ready for the final OEE diagnostic experiment.

## Table of Contents
1.  [Introduction & Vision](#introduction--vision)
2.  [Installation & Quick Start](#installation--quick-start)
3.  [Architectural Overview](#architectural-overview)
4.  [Research Phases: A Narrative of Progression](#research-phases-a-narrative-of-progression)
5.  [Core Technical Implementation](#core-technical-implementation)
6.  [Key Results & Verification](#key-results--verification)
7.  [Running Experiments](#running-experiments)
8.  [Project Structure](#project-structure)
9.  [Future Work & Planned Phases](#future-work--planned-phases)
10. [Contributing & Citation](#contributing--citation)

---

## 1. Introduction & Vision

**Core Research Question:** Can an artificial system, stripped of designer-specified objectives and governed solely by self-enforcing environmental constraints, exhibit genuine, unbounded evolutionary innovation?

This project is built on the thesis that **Open-Ended Evolution (OEE)** requires a shift from **optimizing fitness functions** to **navigating constraint-defined viability landscapes**. The Genesis Engine implements this as **Constraint-Driven Evolution (CDE)**, where complexity must "earn its keep" against relentless pressure.

## 2. Installation & Quick Start

### Prerequisites
- Python 3.9+
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/genesis-engine.git
cd genesis-engine

# Install core dependencies
pip install numpy scipy matplotlib
```

### First Verification (5,000 generations)
```bash
# Run the core verification test to confirm system integrity
python verify_fix.py

# Expected output includes:
# ✅ Pre-flight checks: PASSED
# ✅ Genome control: 22.8 genes (target: 15-25)
# ✅ Performance: 40.1 gen/s
# ✅ Verification Test PASSED - System ready for 200k Deep Probe
```

## 3. Architectural Overview

The Genesis Engine is built as a layered architecture where higher-level functions emerge from lower-level, immutable rules.

```
┌─────────────────────────────────────────────┐
│            EXPERIMENT LAYER                 │
│  (Deep Probe, Ablation Studies, Coevolution)│
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│         DIAGNOSTIC & VERIFICATION LAYER     │
│  (PNCT Metrics, ConstraintChecker, Profilers)│
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│         EVOLUTIONARY CORE LAYER             │
│  (Selection, Mutation, Pareto Co-Evolution) │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│         CONSTRAINED GENETICS LAYER          │
│  (EvolvableGenome, Linkage, Metabolic Cost) │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│         IMMUTABLE KERNEL LAYER              │
│  (Codon Genetics, AIS, Phenotype Development)│
└─────────────────────────────────────────────┘
```

## 4. Research Phases: A Narrative of Progression

The project follows an 8-phase research program, each building on and responding to the limitations of the previous.

### Phase 1-4: Foundation & Pivot to Endogenous Dynamics
| Phase | Guiding Principle | Core Achievement | Status |
|-------|-------------------|------------------|---------|
| **1. Immutable Kernel** | "Design the ground, not the path." | Codon-based genetics, Artificial Immune System (AIS), minimal phenotype development. | ✅ **Complete** |
| **2. Evolvable Scaffolding** | "Survival decides what 'better' means." | `EvolvableGenome` with metabolic cost, Linkage Learning (LLGA). | ✅ **Complete** |
| **3. Guided Bootstrapping** | "Guidance is allowed, control is not." | Temporary fitness function to seed initial diversity. | ✅ **Complete** |
| **4. Endogenous Genesis** | "If I can predict it, the system failed." | Pareto Co-Evolution Engine; removal of all external fitness. | ✅ **Complete** |

### Phase 5: Extended Exploration & The Expert Critique
A 50,000-generation run demonstrated self-sustaining activity but exposed **genome bloat** as a systemic risk. External reviewers issued a critical challenge:
> **"A population not collapsing does not constitute evidence of an unbounded evolutionary trajectory."**

This forced a shift from observation to measurement, motivating the diagnostic Phases 6-8.

### Phase 6: Phenotypic Novelty & Complexity Trajectory (PNCT) - **CURRENT**
*   **Objective**: Answer the expert critique with quantitative, longitudinal metrics.
*   **Implementation**:
    *   **PNCT Metrics Suite**: Genome Architecture Complexity (GAC), Expressed Phenotype Complexity (EPC), Normalized Novelty Distance (NND).
    *   **The Genome Bloat Crisis & Hardening**: A failed 200k-run revealed catastrophic bloat (693 genes). Investigation showed the metabolic cost law (`0.005 × genes^1.5`) was implemented but **not integrated** into selection. This led to the **Three-Layer Hardening**:
        1.  **Law Enforcement**: Mandatory pre-flight `ConstraintChecker`.
        2.  **Diagnosis**: `MutationProfiler` micro-phase (found GAC grew 40x faster than EPC).
        3.  **Meta-Optimization**: Framework to tune the constraint for maximum functional complexity.
*   **Status**: ✅ **Hardening Complete**. System verified stable (22.8 genes, 40.1 gen/s). Ready for the final **200,000-generation Deep Probe**.

### Phase 7-8: The Diagnostic Trilogy (Planned)
| Phase | Diagnostic Question | Method |
|-------|---------------------|---------|
| **7. Ablation Studies (AECF)** | Are core mechanisms *necessary* for complexity? | Controlled ablation of AIS, Linkage Learning. |
| **8. Coevolutionary Arms Race (CARP)** | Can the system sustain accelerating innovation? | Introduce internal adversarial pressure. |

## 5. Core Technical Implementation

### The Metabolic Cost Model
The foundational constraint that enforces a cost on complexity:
```python
# In evolvable_genome.py
metabolic_cost = 0.005 * (gene_count ** 1.5)  # Quadratic penalty

# Applied during selection in bootstrap_evaluator.py
penalized_fitness = raw_fitness * (1.0 - metabolic_cost)
```

### PNCT Metrics
*   **GAC**: Raw count of active genes in the `EvolvableGenome`.
*   **EPC**: Functional complexity measured via **Lempel-Ziv compression** of agent action sequences. A rising EPC indicates new, compressible behavioral patterns.
*   **NND**: Mean behavioral distance between agents in a population, ensuring diversity.

### Automated Verification
The `ConstraintChecker` performs pre-flight validation, ensuring:
1. Metabolic cost is correctly applied during selection.
2. AIS pruning is active.
3. Linkage structures are properly inherited.
4. No fundamental laws are disconnected.

## 6. Key Results & Verification

### Genesis Engine v1.0 (Guided Evolution Baseline)
*   **Result**: Successfully evolved chaos-seeking dynamics in a Gray-Scott physics substrate.
*   **Fitness**: Increased from 1.0 to 3.0 over 10 generations.
*   **Limitation**: Explicitly bounded by the designer's objective function.

### Phase 6 Hardening Verification
**Test:** `verify_fix.py` (5,000 generations)
| Metric | Result | Target | Verdict |
|--------|--------|---------|---------|
| **Final GAC** | 22.8 genes | 15-25 | ✅ **PASS** |
| **Performance** | 40.1 gen/sec | >30 gen/sec | ✅ **PASS** |
| **Bloat Trend** | +0.0010 genes/gen | Minimal | ✅ **PASS** |
| **Circuit Breaker** | Not triggered (GAC < 50) | - | ✅ **PASS** |

**Conclusion:** The genome bloat crisis is resolved. The system is stable and ready for long-term observation.

## 7. Running Experiments

### A. Verification & Diagnostics
```bash
# Run the comprehensive verification test
python verify_fix.py

# Run a 10,000-generation diagnostic profile
python scripts/run_diagnostic_10k.py

# Profile mutation operator efficiency
python -m engine.diagnostics.mutation_profiler
```

### B. The 200,000-Generation Deep Probe
This is the definitive experiment for Phase 6.
```bash
# Launch with conservative, verified settings (Population: 50)
python scripts/launch_final_overnight.py

# Expected runtime: ~6-8 hours
# Output: Checkpoints every 25k gens, PNCT data, final pivot decision.
```

**Monitoring**: The experiment includes real-time tracking of GAC, EPC, NND, and performance. Safety cutoffs halt execution if GAC > 150 or performance degrades significantly.

## 8. Project Structure
```
genesis-engine/
├── engine/
│   ├── kernel/                    # Phase 1: Immutable base
│   │   ├── codon_table.py         # Degenerate genetic code
│   │   └── artificial_immune_system.py
│   ├── genetics/                  # Phase 2: Evolvable structures
│   │   ├── evolvable_genome.py    # Genome with metabolic cost
│   │   └── linkage_structure.py   # Linkage Learning (LLGA)
│   ├── evolution/                 # Evolutionary core
│   │   ├── bootstrap_evaluator.py # Selection with cost penalty
│   │   ├── pareto_engine.py       # Phase 4: Co-evolution
│   │   └── genesis_engine.py      # Main orchestration loop
│   └── diagnostics/               # Phase 6: Hardening tools
│       ├── constraint_checker.py  # Pre-flight verification
│       ├── mutation_profiler.py
│       └── resource_profiler.py
├── scripts/                       # Experiment runners
│   ├── launch_final_overnight.py  # 200k Deep Probe
│   ├── verify_fix.py              # Main verification test
│   └── run_diagnostic_10k.py
├── configs/                       # Experiment configurations
├── tests/                         # Unit and integration tests
└── docs/
    └── walkthrough.md             # Phase-by-phase technical narrative
```

## 9. Future Work & Planned Phases

The immediate next step is the **200k Deep Probe**. Its PNCT data will trigger one of two paths:

| Decision | Next Action |
|----------|-------------|
| **`PROCEED_TO_PHASE_7`** | Implement the **Ablation Framework** to test necessity of core mechanisms. |
| **`REDESIGN_ARCHITECTURE`** | Conduct a deep analysis of PNCT failure modes to inform a targeted redesign. |

**Long-Term Vision**: To evolve the constraints themselves, creating a meta-evolutionary system where the "laws of physics" can adapt to facilitate exploration.

## 10. Contributing & Citation

This is an active research project. For collaboration inquiries, please contact the principal investigator.

If you build upon this work, please cite:
```
Sharma, A. Genesis Engine: A Framework for Constraint-Driven Open-Ended Evolution. 2024.
```

**License:** MIT

---
**The system is verified, stable, and waiting. The final experiment to distinguish a universe of endless discovery from a complex sandpile begins with:**
```bash
python scripts/launch_final_overnight.py
```
