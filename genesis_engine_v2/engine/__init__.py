"""
Genesis Engine v2 - Core Engine Package

This package contains the foundational genetic architecture for the Genesis Engine.
"""

from .codon_translator import CodonTranslator
from .ais import ArtificialImmuneSystem
from .kernel_agent import KernelAgent
from .kernel_world import KernelWorld
from .evolvable_genome import EvolvableGenome
from .linkage_structure import LinkageStructure

__all__ = ['CodonTranslator', 'ArtificialImmuneSystem', 'KernelAgent', 'KernelWorld', 
           'EvolvableGenome', 'LinkageStructure']
