"""
Genesis Engine v3 - Core Engine Package (Experimental)

__version__ = "3.0.0-dev"

This package contains the experimental genetic architecture for the Genesis Engine V3.
"""

from .codon_translator import CodonTranslator
from .ais import ArtificialImmuneSystem
from .kernel_agent import KernelAgent
from .kernel_world import KernelWorld
from .evolvable_genome import EvolvableGenome
from .linkage_structure import LinkageStructure
from .structurally_evolvable_agent import StructurallyEvolvableAgent
from .bootstrap_evaluator import calculate_fitness, tournament_selection
from .genesis_engine import GenesisEngine
from .pareto_evaluator import ParetoCoevolutionEvaluator

__all__ = ['CodonTranslator', 'ArtificialImmuneSystem', 'KernelAgent', 'KernelWorld', 
           'EvolvableGenome', 'LinkageStructure', 'StructurallyEvolvableAgent',
           'calculate_fitness', 'tournament_selection', 'GenesisEngine',
           'ParetoCoevolutionEvaluator']
