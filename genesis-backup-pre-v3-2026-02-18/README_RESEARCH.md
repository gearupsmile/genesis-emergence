# Genesis Engine: Constraint-Driven Open-Ended Evolution

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Abstract

The **Genesis Engine** achieves sustained open-ended evolution through constraint-driven dynamics rather than fitness optimization. By eliminating external fitness signals and enforcing immutable physical constraints (metabolic cost, immune pruning, codon protection), the system demonstrates 58.3% sustained runs beyond 50,000 generations with non-saturating complexity growth.

**Key Results:**
- 58.3% sustained evolution (7/12 runs) over 50k generations
- Non-saturating GAC growth (20 → 250 genes)
- 287 distinct phenotypic types via PNCT metrics
- 100% endogenous fitness (zero external objectives)

## Installation

### Prerequisites
- Python 3.9 or higher
- Git

### Quick Start
```bash
# Clone the repository
git clone https://github.com/[username]/genesis-emergence.git
cd genesis-emergence

# Install dependencies
pip install -r requirements.txt

# Verify installation
python verify_fix.py
```

## Running Experiments

### 1. Baseline Comparisons

Run all baseline experiments (Random Search, Fixed Constraints, Novelty Search, MAP-Elites):
```bash
python run_all_baselines.py
```

Individual baselines:
```bash
# Random search baseline
python run_baseline_random.py

# Fixed constraints (no CARP)
python run_baseline_fixed.py

# Novelty search
python run_baseline_novelty.py

# MAP-Elites (quality-diversity)
python run_baseline_mapelites.py
```

**Expected runtime:** ~30-45 minutes for all baselines (3 seeds × 10k generations each)

### 2. Full Genesis System

Run a single 50k-generation experiment:
```bash
python scripts/launch_final_overnight.py --config baseline
```

Run complete ablation study (72 runs):
```bash
python scripts/run_ablation_study.py --full
```

**Expected runtime:** 
- Single 50k run: ~6-8 hours
- Full ablation: ~48 hours

### 3. Generate Figures

Generate all paper figures:
```bash
# Phase transition plot (Figure 2)
python generate_figure_2.py

# Comparison plot (Figure 3)
python generate_figure_3_comparison.py

# Distribution box plots (Figure 3 alternative)
python generate_figure_3_distributions.py

# Failure timeline (Figure 4)
python generate_figure_4_timeline.py
```

All figures saved as PDF and PNG in the artifacts directory.

## Data and Figure Generation

### Output Structure
```
results/
├── baselines/
│   ├── random_search_seed_42.csv
│   ├── novelty_seed_42.csv
│   ├── mapelites_seed_42.csv
│   └── ...
└── full_system/
    ├── run_seed_42/
    │   ├── metrics.json
    │   └── checkpoints/
    └── ...

C:/Users/Lenovo/.gemini/antigravity/brain/.../
├── figure_2_phase_transition.pdf
├── figure_3_comparison.pdf
├── figure_3_final_distributions.pdf
└── figure_4_failure_timeline.pdf
```

### Analyzing Results
```python
import pandas as pd
import json

# Load baseline results
df = pd.read_csv('results/baselines/random_search_seed_42.csv')
print(df.describe())

# Load full system metrics
with open('results/full_system/run_seed_42/metrics.json') as f:
    metrics = json.load(f)
```

## Project Structure

```
genesis-emergence/
├── genesis_engine_v2/          # Core engine
│   └── engine/
│       ├── evolvable_genome.py
│       ├── genesis_engine.py
│       ├── ais.py
│       ├── pareto_evaluator.py
│       └── carp/
├── scripts/                    # Experiment runners
│   ├── launch_final_overnight.py
│   └── run_ablation_study.py
├── run_baseline_*.py          # Baseline experiments
├── generate_figure_*.py       # Figure generation
├── requirements.txt           # Pinned dependencies
└── README.md                  # This file
```

## Key Components

### 1. Metabolic Cost Model
```python
cost = 0.005 × (gene_count)^1.5
penalized_score = raw_score × (1 - cost)
```

### 2. PNCT Metrics
- **GAC**: Genome Architecture Complexity (gene count)
- **EPC**: Expressed Phenotype Complexity (Lempel-Ziv)
- **NND**: Normalized Novelty Distance (diversity)

### 3. CARP Protocol
Adaptive constraint regulation that adjusts mutation rate and metabolic cost based on population variance.

## Reproducibility

### Docker Environment
```bash
docker pull genesis-engine/jair-2024:v1.0
docker run -it genesis-engine/jair-2024:v1.0
```

### Random Seeds
All experiments use controlled seeds for reproducibility:
- Baseline runs: `[42, 123, 456]`
- Full system: `[42, 123, 456, 789, 1011, 1213, 1415, 1617, 1819, 2021, 2223, 2425]`

### Hardware Specifications
- CPU: Intel Core i7-10700K @ 3.80GHz (8 cores)
- RAM: 32 GB DDR4-3200
- Storage: NVMe SSD

## Citation

If you use this code in your research, please cite:

```bibtex
@article{sharma2024genesis,
  title={Genesis Engine: Constraint-Driven Open-Ended Evolution Without External Fitness},
  author={Sharma, Anushka},
  journal={Journal of Artificial Intelligence Research},
  year={2024}
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Contact

For questions or collaboration inquiries:
- Email: [your-email@example.com]
- GitHub Issues: [github.com/[username]/genesis-emergence/issues]

## Acknowledgments

This work builds on foundational research in artificial life, including Tierra (Ray, 1991), Avida (Ofria et al., 2004), and POET (Wang et al., 2019).

---

**Status:** Research code - actively maintained  
**Last Updated:** January 2026
