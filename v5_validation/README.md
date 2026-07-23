# Genesis V5 Validation Suite

This directory contains the high-priority validation tests for Genesis V5. These tests assess the **structure-function decoupling** claim and validate the historical necessity of co-evolutionary structural complexity growth.

## Directory Structure

```
v5_validation/
├── README.md               # This file
├── 01_pata_ec/             # Functional environment divergence (PATA-EC)
│   ├── run_pata_ec.py      # Test execution script
│   ├── results.json        # Spearman rank correlations and statistics
│   └── correlation_histogram.png
├── 02_behavioral_metrics/  # Quantitative behavioral metrics
│   ├── run_behavioral_metrics.py
│   ├── results.json        # DTW, action entropy, energy efficiency metrics
│   └── metrics_plots.png   # Comparative boxplots
├── 03_pruning_gac/         # Adaptive pruning and GAC tracking
│   ├── run_pruning_gac.py
│   ├── results.json        # Pruning thresholds, survival, collapse point
│   └── gac_vs_pruning.png  # Line plot showing structural collapse
├── 04_robustness/          # Resilience to perturbations
│   ├── run_robustness.py
│   ├── results.json        # Survival degradation and ANOVA results
│   └── robustness_plot.png # Robustness comparison plot
├── 05_constrained_training/ # Constrained co-evolution
│   ├── run_constrained_training.py
│   ├── progress.log        # Generation log
│   └── final_summary.json  # Stagnation evidence (when complete)
└── summary_report.txt      # Final verdict and summary of findings
```

## Validation Tests and Rationale

### 1. PATA-EC (Functional Environment Divergence)
- **What it does**: Evaluates fixed-environment baseline (~52 nodes) and co-evolved (~467 nodes) agents across all co-evolved environment substrates, computing Spearman rank correlations of performance.
- **Why it matters**: A low rank correlation indicates that the environments demand distinct behavioral strategies. If the correlation were high, the environments would simply be scaled versions of each other, disconfirming the claim that co-evolution explores functionally diverse niches.

### 2. Quantitative Behavioral Metrics
- **What it does**: Runs agents in a fixed environment for 100 episodes each and measures:
  - Trajectory DTW (Dynamic Time Warping) distance to a reference path.
  - Action entropy (Shannon entropy of movement and secretion actions).
  - Energy efficiency (metabolic returns).
- **Why it matters**: Validates that structural growth translates to richer, more complex behaviors (high action entropy) and distinct movement characteristics (DTW differences), rather than just silent neutral mutations.

### 3. Adaptive Pruning with GAC Tracking
- **What it does**: Prunes the weakest connections of a 467-node co-evolved agent and tracks the survival rate and GAC (Genome Addition Persistence) over 30 generations.
- **Why it matters**: Identifies the "collapse point" where performance degrades. If the agent collapses only at high pruning levels, it shows that the large structure is functional and contingency-rich.

### 4. Robustness to Perturbations
- **What it does**: Applies Gaussian noise to CPPN weights ($\sigma \in \{0.1, 0.2, 0.3\}$) and sensory gradients ($\sigma \in \{0.05, 0.1\}$), measuring survival times.
- **Why it matters**: Demonstrates whether the co-evolved structures are more resilient to perturbations compared to simple fixed-environment agents, a hallmark of structure-function decoupling.

### 5. Constrained Training
- **What it does**: Restarts co-evolution from scratch but limits CPPN size to $\le 52$ nodes.
- **Why it matters**: Tests if the co-evolutionary curriculum stagnates when agents are prevented from growing structurally, providing evidence of historical necessity (contingency).
