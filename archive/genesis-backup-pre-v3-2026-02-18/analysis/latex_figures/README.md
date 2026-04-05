# LaTeX Figure Generation

This directory contains the LaTeX source code for the paper figures using PGFPlots.

## Structure
- `main.tex`: A wrapper document to view all figures.
- `figureX.tex`: Standalone figure files (can be included in your paper or compiled individually).
- `data/`: CSV files containing the data plotted in the figures.

## Data Source
The data is exported from the experimental result logs using `analysis/scripts/export_figure_data.py`.
- **Figure 1 (Genesis)**: Uses `fig1_aggregated.csv`. Derived from successful Genesis runs (or Novelty Search as proxy if Genesis data is missing).
- **Figure 2 (Comparison)**: Uses `fig2_baseline_*.csv` and `fig1_aggregated.csv`.
- **Figure 3 (Diagnostics)**: Uses `fig3_*.csv`. Representative runs for each failure mode.
- **Figure 4 (CARP)**: Uses `fig4_carp.csv`. Shows `lambda` and `viability` dynamics.

## Compiling
You can compile the main document to see all figures:
```bash
pdflatex main.tex
```

Or compile individual figures:
```bash
pdflatex figure1.tex
```

## Requirements
- `pgfplots` package (compat level 1.18)
- `standalone` package
