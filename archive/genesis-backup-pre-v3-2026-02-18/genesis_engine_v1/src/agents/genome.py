"""
Evolvable genome with genes as multipliers to world physics.

Genes modify how agents interact with fixed world physics (World_98),
enabling evolution through mutation and natural selection.
"""

import numpy as np
from typing import Dict


class Genome:
    """Agent genome with genes as multipliers/modifiers to world physics."""
    
    # Baseline values (neutral multipliers)
    BASELINES = {
        'metabolism_multiplier': 1.0,      # 1.0 = world baseline
        'consumption_multiplier': 1.0,     # 1.5 = 50% better than world
        'reproduction_th_multiplier': 1.0, # 0.8 = 20% lower threshold
        'reproduction_cost_multiplier': 1.0,
        'move_speed': 1.0,                 # Absolute speed (pixels/cycle)
        'sensor_radius': 5.0               # Absolute radius (pixels)
    }
    
    # Viable ranges for each gene
    RANGES = {
        'metabolism_multiplier': (0.5, 2.0),
        'consumption_multiplier': (0.5, 2.0),
        'reproduction_th_multiplier': (0.7, 1.5),
        'reproduction_cost_multiplier': (0.7, 1.5),
        'move_speed': (0.5, 2.0),
        'sensor_radius': (3.0, 10.0)
    }
    
    def __init__(self, genes: Dict[str, float] = None):
        """Initialize genome with genes dict or baselines.
        
        Args:
            genes: Dictionary of gene values, or None for baselines
        """
        if genes is None:
            self.genes = self.BASELINES.copy()
        else:
            self.genes = genes.copy()
    
    def mutate(self, mutation_rate: float = 0.1, 
               mutation_strength: float = 0.2) -> 'Genome':
        """Create mutated copy of genome.
        
        Each gene has mutation_rate probability of mutating.
        Mutations are Gaussian noise with std = mutation_strength * value.
        
        Args:
            mutation_rate: Probability each gene mutates (default: 10%)
            mutation_strength: Std dev of Gaussian noise as fraction of value (default: 20%)
        
        Returns:
            New Genome with mutations applied and clamped to viable ranges
        """
        mutated = {}
        
        for gene_name, value in self.genes.items():
            if np.random.random() < mutation_rate:
                # Gaussian noise: ±mutation_strength of current value
                noise = np.random.normal(0, mutation_strength * value)
                mutated[gene_name] = value + noise
            else:
                mutated[gene_name] = value
        
        # Clamp to viable ranges
        clamped = self._clamp_genes(mutated)
        return Genome(clamped)
    
    def copy(self) -> 'Genome':
        """Create exact copy of genome.
        
        Returns:
            New Genome with identical gene values
        """
        return Genome(self.genes)
    
    def _clamp_genes(self, genes: Dict[str, float]) -> Dict[str, float]:
        """Ensure genes stay within viable ranges.
        
        Args:
            genes: Dictionary of gene values
        
        Returns:
            Dictionary with values clamped to RANGES
        """
        clamped = {}
        for name, value in genes.items():
            min_val, max_val = self.RANGES[name]
            clamped[name] = np.clip(value, min_val, max_val)
        return clamped
    
    def __repr__(self):
        """String representation of genome."""
        gene_str = ', '.join(f"{k}={v:.3f}" for k, v in self.genes.items())
        return f"Genome({gene_str})"
    
    def __eq__(self, other):
        """Check equality based on gene values."""
        if not isinstance(other, Genome):
            return False
        return self.genes == other.genes
