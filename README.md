# Genesis Engine

**Constraint-Driven Evolution Without Fitness Functions**

Genesis is an artificial life research framework for studying **sustained evolutionary dynamics in the complete absence of fitness functions**.
It was developed to empirically investigate whether evolutionary activity can persist when selection is driven purely by **constraints, relational pressures, and viability regulation**, rather than explicit optimization objectives.

This repository contains the **full experimental system** used in our GECCO 2026 paper:

> **Sustained Evolutionary Activity Without Fitness Functions:
> An Empirical Study of Constraint-Driven Selection**

---

## 🔬 Research Motivation

Most evolutionary algorithms depend on explicit fitness functions that define what “better” means. While effective for optimization, this approach strongly limits long-term innovation and often leads to premature convergence.

Biological evolution, by contrast, exhibits **open-ended creativity without predefined objectives**.

Genesis tests the hypothesis that:

> **Sustained evolutionary activity can emerge from constraint-driven selection alone, without fitness, novelty objectives, or reward shaping.**

Instead of climbing a predefined fitness landscape, Genesis populations must remain viable within a dynamically regulated constraint space.

---

## 🧠 Core Idea: Constraint-Driven Evolution

Genesis removes all external fitness signals and replaces them with:

* **Metabolic cost constraints** penalizing genome complexity
* **Pareto-based relational dominance** instead of scalar fitness
* **Diversity stabilization via an Artificial Immune System (AIS)**
* **Adaptive constraint regulation (CARP)** to maintain a narrow viability corridor

Importantly:

* Nothing optimizes for novelty, complexity, or performance
* Regulation controls *margins*, not *outcomes*

---

## 🧩 System Architecture (High-Level)

Genesis is organized as layered evolutionary machinery:

1. **Genome Representation**

   * Variable-length codon sequences
   * Supports point and structural mutations

2. **Constraint Enforcement**

   * Nonlinear metabolic cost penalizes genome growth
   * Prevents uncontrolled bloat while allowing useful complexity

3. **Relational Selection**

   * Pareto dominance across internal axes
   * No scalar fitness values

4. **Diversity Preservation (AIS)**

   * Maintains an archive of representative genotypes
   * Reinjects diversity when collapse is detected

5. **Adaptive Regulation (CARP)**

   * Dynamically adjusts constraint intensity
   * Maintains evolutionary viability without objectives

6. **Measurement & Diagnostics**

   * PNCT metrics suite:

     * Genetic Activity Coefficient (GAC)
     * Expressed Phenotype Complexity (EPC)
     * Novelty Network Density (NND)

---

## 📦 What This Repository Contains

* **`genesis_engine_v1/`, `v2/`, `v3/`**: Core evolutionary engines preserving all research phases.
* **`experiments/`**: All experiment scripts used for the paper (10k, 50k runs, ablations).
* **`docs/`**: Comprehensive guides, design decisions, and system diagrams (Start with `docs/SUMMARY.md`).
* **`tests/`**: Cross-version verification suite and regression testing.
* **`archive/`**: Offline storage for metrics, checkpoints, and generated artifacts.

Features included in the core:
* Four baseline methods (Random, Fixed, Novelty, MAP-Elites)

  * Random Search
  * Fixed Constraints
  * Novelty Search
  * MAP-Elites
* Ablation study variants
* Parameter sweep tools
* Analysis scripts to regenerate all paper figures
* Fixed random seeds for exact reproducibility

---

## ⚙️ Installation

### Requirements

* Python **3.8+**
* NumPy, SciPy, Matplotlib, Pandas

### Setup

```bash
git clone https://github.com/yourusername/genesis-engine.git
cd genesis-engine
pip install -r requirements.txt
```

---

## 🚀 Quick Start

Run a short diagnostic experiment (1,000 generations):

```bash
python experiments/run_genesis_1k.py --seed 42
```

This verifies installation and shows real-time tracking of:

* Genetic Activity Coefficient (GAC)
* Expressed Phenotype Complexity (EPC)
* Novelty Network Density (NND)

---

## 🔁 Replicating the GECCO 2026 Results

The paper reports **12 independent Genesis runs**, each of **10,000 generations**.

Run a single experiment:

```bash
python experiments/run_genesis_10k.py --seed 12345
```

Run all 12 paper experiments:

```bash
python experiments/run_all_genesis.py
```

Each run takes approximately **30–40 minutes** on a modern desktop CPU.

---

## 📊 Baseline Comparisons

Run individual baselines:

```bash
python experiments/run_baseline_random.py --seed 12345
python experiments/run_baseline_fixed.py --seed 12345
python experiments/run_baseline_novelty.py --seed 12345
python experiments/run_baseline_mapelites.py --seed 12345
```

Run all baselines across all seeds:

```bash
python scripts/run_all_baselines.py
```

Observed failure modes:

* **Metabolic overload** (Random Search)
* **Neutral drift saturation** (Fixed Constraints)
* **Dominance monopolization** (MAP-Elites)

---

## 🧪 Ablation Studies

Disable individual mechanisms:

```bash
python experiments/run_ablation_no_carp.py --seed 12345
python experiments/run_ablation_no_ais.py --seed 12345
python experiments/run_ablation_no_metabolic.py --seed 12345
python experiments/run_ablation_no_pareto.py --seed 12345
```

Results show:

* Removing CARP or AIS raises failure rates from ~42% to **>90%**
* These mechanisms are **necessary, not optional**

---

## 📈 Analysis & Figure Generation

```bash
python analysis/scripts/process_logs.py
python analysis/scripts/generate_paper_figures.py
```

Outputs match Figures 1–4 and Tables from the paper.

---

## 🧠 Key Findings

* Sustained evolutionary activity without fitness is achievable but **structurally bounded**
* ~58% of runs maintain non-zero activity after fitness removal
* Genome complexity consistently plateaus, revealing architectural ceilings
* Constraint regulation enables persistence but does not guarantee open-endedness

This work provides **empirical boundaries**, not aspirational claims.

---

## ♻️ Reproducibility

* All runs use fixed random seeds (Appendix A)
* All hyperparameters are documented (Appendix B)
* Full replication instructions in
  `reproducibility_package/README_REPLICATION.md`

Verification suite:

```bash
python tests/run_verification_suite.py
```

---

## 📚 Citation

```bibtex
@inproceedings{genesis2026,
  title={Sustained Evolutionary Activity Without Fitness Functions: An Empirical Study of Constraint-Driven Selection},
  author={Anonymous Author(s)},
  booktitle={GECCO '26: Genetic and Evolutionary Computation Conference},
  year={2026},
  address={San José, Costa Rica}
}
```

---

## 🔮 Future Directions

* Evolvable genome alphabets
* Adaptive constraint structures
* Coevolutionary and environmental dynamics

Each targets a specific hypothesized cause of complexity plateaus.

---

## 📜 License

MIT License.
Free to use, modify, and distribute with attribution.
