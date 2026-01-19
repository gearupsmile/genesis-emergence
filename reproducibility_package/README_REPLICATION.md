# Replication Guide: Genesis Emergence (GECCO Submission)

This package contains the artifacts necessary to replicate the experiments and analysis presented in *"Open-Ended Evolution via Metabolic Limits and Co-Evolutionary Arms Races"*.

## 1. System Requirements

- **OS**: Windows, Linux, or macOS (Tested on Windows 11)
- **Python**: 3.8+
- **Memory**: 16GB+ RAM recommended (Simulations are memory-intensive)
- **Disk**: 5GB+ for logs and results

## 2. Installation

1. Clone the repository (if applicable) or unzip the archive.
2. Install dependencies:
   ```bash
   pip install numpy scipy matplotlib pandas seaborn
   ```
   *(See `requirements.txt` for exact versions)*

## 3. Running Experiments

We provide a master runner script to execute all baseline comparisons sequentially.

### Baselines (Table 4 & Figure 2)
The following command runs 4 experimental conditions:
1. **Novelty Search**: Fitness replaced by behavioral novelty (GAC, EPC, NND).
2. **MAP-Elites**: Quality-Diversity search in 2D space (GAC vs. EPC).
3. **Random Search**: Pure genetic drift (no selection).
4. **Fixed Constraints**: Standard evolution with static physical constraints (No CARP).

**Execution:**
```bash
# Run all baselines (3 seeds each, 10,000 generations)
python scripts/run_all_baselines.py
```
*Runtime: Approximately 4-6 hours on a modern CPU.*

### Main Genesis Experiment (Deep Probe)
The main results (Figures 1, 3, 4) form the "Full Genesis" condition. These runs are computationally expensive (200,000 generations).
To replicate a single run:
```bash
python experiments/launch_final_overnight.py
```

## 4. Analysis & Figure Generation

Once experiments are complete, results are stored in `results/baselines/`.
To generate the paper figures (PDF format):

```bash
# 1. Process logs and calculate statistics
python analysis/scripts/process_logs.py

# 2. Generate Figures 1-4
python analysis/scripts/generate_paper_figures.py
```

Outputs will be saved to `analysis/figures/`.

## 5. Directory Structure

- `genesis_engine_v2/`: Core simulation engine.
- `experiments/baselines/`: Script definitions for comparison benchmarks.
- `scripts/`: Utility scripts (running, scraping, validating).
- `analysis/`: Data processing and plotting code.
- `reproducibility_package/`: Documentation and parameter appendices.

## 6. Parameters

See `APPENDIX_PARAMETERS.md` for a complete list of hyperparameters used in this study.
