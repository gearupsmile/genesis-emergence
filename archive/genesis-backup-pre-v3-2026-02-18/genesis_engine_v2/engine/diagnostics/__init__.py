"""
Diagnostics module for Genesis Engine v2.

Provides metrics for tracking:
- Genome Architecture Complexity (GAC)
- Normalized Novelty Distance (NND)
- Phenotypic Novelty & Complexity Trajectory (PNCT)
"""

from .pnct_metrics import ComplexityTracker, NoveltyAnalyzer, PNCTLogger

__all__ = ['ComplexityTracker', 'NoveltyAnalyzer', 'PNCTLogger']
