# Genesis Project: Paper Replication Guide

This package contains the code, data, and instructions necessary to fully replicate the experiments, analysis, and figures presented in our paper.

## 1. System Requirements
- Python 3.8+
- Memory: Minimum 16GB RAM recommended for full co-evolution runs.
- Libraries: `numpy`, `pandas`, `matplotlib`, `scipy`

## 2. Installation
To install the required dependencies:
```bash
pip install -r requirements.txt
```

## 3. Running Baseline Experiments (Phase 1)
To regenerate the data for all baseline conditions (Fixed Constraints, Random Search, MAP-Elites, and Novelty Search) across the 3 seeds used in the paper:
```bash
python scripts/run_all_baselines.py
```
*Note: This will execute 12 independent simulations of 10,000 generations each. Data will be saved to `results/baselines/`.*

## 4. Analysis and Figure Generation (Phase 2)
Once the baseline experiments are complete (and assuming the Full Genesis logs are present in `v5/results/`), you can generate the paper figures.

**Step A: Process Logs**
```bash
python analysis/scripts/process_logs.py
```
This script aggregates the timeseries data, calculates percentiles, and maps the internal metrics (Nodes, LZ) to the paper's theoretical constructs (GAC, EPC, NND).

**Step B: Generate Figures**
```bash
python analysis/scripts/generate_paper_figures.py
```
This generates `figure1.pdf`, `figure2.pdf`, `figure3.pdf`, and `figure4.pdf` directly into the `analysis/figures/` directory.

## 5. Hyperparameter Details
All scraped hyperparameters can be found in `APPENDIX_PARAMETERS.md` within this folder.

## 6. Pre-Submission Validation
Run the validation suite to ensure all outputs are perfectly formatted for submission:
```bash
python scripts/validate_submission.py
```
