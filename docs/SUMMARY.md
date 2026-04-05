# Genesis Engine - Repository Summary

This repository chronicles the iterative development of the Genesis core engine across multiple research phases leading up to the GECCO 2026 paper on constraint-driven evolution.

## Repository Structure

The current codebase is organized to preserve the historical architectures while providing a unified verification and evaluation environment:

### `genesis_engine_v1/`
The foundational proof-of-concept. 
- **Focus**: Initial experiments replacing scalar fitness with raw metabolic constraints.
- **Key Modules**: Contains early CPPN (Compositional Pattern Producing Networks) agent representations and basic local physics engines.

### `genesis_engine_v2/`
The mature baseline system used for generating early empirical bounds.
- **Focus**: Relational pressure, baseline comparisons (MAP-Elites, Novelty Search), and strict complexity penalization.
- **Key Modules**: Implements the Pareto-based multi-objective evaluations and initial Diversity maintenance using explicit novelty metrics. Contains diagnostic suites for tracking Neutral Drift.

### `genesis_engine_v3/`
The advanced evolutionary architecture deployed for the GECCO 2026 paper.
- **Focus**: Fully integrated Artificial Immune System (AIS), Adaptive Regulation (CARP), and environment secretion systems.
- **Key Modules**: The primary testbed for studying the "complexity plateau" and 50k-generation runs without fitness functions. Integrates the robust Lempel-Ziv complexity diagnostics and EPC tracking.

### `experiments/`
Contains the execution scripts to replicate the specific 10k and 50k generation limits, as well as the ablation studies (No CARP, No AIS).

### `tests/`
The consolidated testing directory. Validates constraints, module integrations, physics accuracy, and regression suites to ensure exact reproducibility across platforms.

### `docs/`
All internal design documentation and technical records. See `V2_V3_DIFFERENCES.md` for architectural migration details, and `ZERO_FITNESS_FIX.md` for our rationale surrounding absolute fitness removal.

### `archive/`
Houses legacy data, experimental serialized checkpoints, diagnostic artifacts from active research runs, and scratch notebooks. Stored here offline to keep the root executable core clean for reviewers.

---

## Technical Context

For specific reproducing instructions, run `python tests/run_verification_suite.py` to assert your environment is valid, then consult `README.md` at the project root.
