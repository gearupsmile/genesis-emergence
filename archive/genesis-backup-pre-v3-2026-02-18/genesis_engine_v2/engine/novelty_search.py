"""
Novelty Search Implementation

Implements a Novelty Search algorithm using a behavioral descriptor based on
the three PNCT metrics:
1. GAC (Genome Architecture Complexity)
2. EPC (Expressed Phenotype Complexity)
3. NND (Normalized Novelty Distance - per agent)
"""

import random
import math
import statistics
import heapq
from typing import List, Dict, Tuple, Optional
import numpy as np

from .structurally_evolvable_agent import StructurallyEvolvableAgent
from .diagnostics.pnct_metrics import ComplexityTracker, extract_expressed_phenotype
from .codon_translator import CodonTranslator

class NoveltySearch:
    """
    Novelty Search algorithm using PNCT metrics as behavioral descriptor.
    
    Behavioral Descriptor (3D):
    [GAC (normalized), EPC (0-1), NND (normalized distance to prev gen)]
    """
    
    def __init__(self, 
                 k_neighbors: int = 15, 
                 archive_threshold: float = 0.5, 
                 max_archive_size: int = 1000,
                 nnd_reference_size: int = 20):
        """
        Initialize Novelty Search.
        
        Args:
            k_neighbors: Number of neighbors for novelty score calculation
            archive_threshold: Minimum novelty score to add to archive
            max_archive_size: Maximum size of the novelty archive
            nnd_reference_size: Number of agents from prev gen to use for NND calc
        """
        self.k_neighbors = k_neighbors
        self.archive_threshold = archive_threshold
        self.max_archive_size = max_archive_size
        self.nnd_reference_size = nnd_reference_size
        
        # Archive of novel behaviors (list of 3D points)
        self.archive: List[List[float]] = []
        
        # Tools
        self.tracker = ComplexityTracker()
        self.translator = CodonTranslator()
        
        # History for NND calculation
        self.previous_phenotypes: List[str] = []
        
        # Statistics
        self.generation_stats = {}

    def get_behavioral_descriptor(self, agent: StructurallyEvolvableAgent) -> List[float]:
        """
        Compute the 3D behavioral descriptor for an agent.
        
        Dimensions:
        1. GAC: Genome Length (Log-normalized to 0-1 range approx)
        2. EPC: Lempel-Ziv Complexity (0-1)
        3. NND: Min normalized Hamming distance to previous generation
        """
        # 1. GAC Component
        length = agent.genome.get_length()
        # Normalize: assumes length roughly 0-100. Log scale handles bloat better.
        # log(1) = 0, log(100) ~ 4.6. Divide by 5.0 to get approx 0-1.
        gac_val = min(1.0, math.log(max(1, length)) / 5.0)
        
        # 2. EPC Component
        # We need to re-implement/access lz_complexity since tracker.compute_epc does it internally
        # But compute_epc returns a dict, we can use that.
        epc_metrics = self.tracker.compute_epc(agent, self.translator)
        epc_val = epc_metrics['lz_complexity']
        
        # 3. NND Component
        # Distance to previous generation's reference population
        nnd_val = 0.0
        current_phenotype = self._extract_codon_string(agent)
        
        if self.previous_phenotypes:
            # Calculate min distance to any agent in previous reference set
            distances = [self._hamming_distance(current_phenotype, prev) 
                         for prev in self.previous_phenotypes]
            min_dist = min(distances) if distances else 0
            
            # Normalize by length (approx 0-1)
            max_len = max(len(current_phenotype), 1)
            nnd_val = min(1.0, min_dist / max_len)
        else:
            # First gen, high novelty bias? Or zero?
            # Let's say 1.0 to encourage initial spread, or 0.0. 
            # 0.0 makes more sense as "no history to be novel against".
            nnd_val = 0.0
            
        return [gac_val, epc_val, nnd_val]

    def _extract_codon_string(self, agent) -> str:
        """Extract expressed codon string."""
        genome_length = agent.genome.get_length()
        expressed_indices = agent.linkage_structure.get_expressed_indices(genome_length)
        codons = agent.genome.sequence
        expressed = [codons[i] for i in expressed_indices if i < len(codons)]
        return ''.join(expressed)

    def _hamming_distance(self, s1: str, s2: str) -> int:
        """Calculate Hamming distance."""
        # Pad
        l1, l2 = len(s1), len(s2)
        max_l = max(l1, l2)
        s1 = s1.ljust(max_l, 'X')
        s2 = s2.ljust(max_l, 'X')
        return sum(c1 != c2 for c1, c2 in zip(s1, s2))

    def _euclidean_distance(self, p1: List[float], p2: List[float]) -> float:
        """Calculate Euclidean distance between two 3D points."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

    def calculate_novelty_scores(self, population: List[StructurallyEvolvableAgent]) -> Dict[str, float]:
        """
        Calculate novelty score for each agent.
        
        Score = Average distance to k-nearest neighbors (in population + archive).
        """
        # 1. Compute descriptors
        descriptors = {agent.id: self.get_behavioral_descriptor(agent) for agent in population}
        
        # 2. Collect all points (Population + Archive)
        pop_points = list(descriptors.values())
        all_points = pop_points + self.archive
        
        scores = {}
        
        for agent in population:
            point = descriptors[agent.id]
            
            # Calculate distances to all other points
            # (Optimization: could use KD-Tree for large pops, but O(N^2) fine for N<2000)
            dists = [self._euclidean_distance(point, other) for other in all_points]
            
            # Sort and take k nearest (excluding self, which is dist 0)
            dists.sort()
            # First dist is 0 (self), so take 1..k+1
            k_nearest = dists[1 : self.k_neighbors + 1]
            
            if k_nearest:
                score = sum(k_nearest) / len(k_nearest)
            else:
                score = 0.0
                
            scores[agent.id] = score
            
        return scores, descriptors

    def update_archive(self, population: List[StructurallyEvolvableAgent], 
                      scores: Dict[str, float], 
                      descriptors: Dict[str, List[float]]):
        """
        Add highly novel agents to archive and update randomness.
        """
        # 1. Add candidates > threshold
        added_count = 0
        for agent in population:
            score = scores[agent.id]
            if score > self.archive_threshold:
                self.archive.append(descriptors[agent.id])
                added_count += 1
                
        # 2. Random probabilistic addition (to ensure some drift)
        if added_count == 0 and random.random() < 0.01:
             rand_agent = random.choice(population)
             self.archive.append(descriptors[rand_agent.id])
             
        # 3. Prune archive if too large (remove oldest or random?)
        # Standard: remove random to keep distribution uniform-ish or just cap
        while len(self.archive) > self.max_archive_size:
            self.archive.pop(random.randint(0, len(self.archive) - 1))
            
        # 4. Update Reference for NND (for NEXT gen)
        # Store phenotypes of top N most novel agents
        sorted_agents = sorted(population, key=lambda a: scores[a.id], reverse=True)
        top_n = sorted_agents[:self.nnd_reference_size]
        self.previous_phenotypes = [self._extract_codon_string(a) for a in top_n]

    def select_parents(self, population: List[StructurallyEvolvableAgent], 
                      num_parents: int) -> List[StructurallyEvolvableAgent]:
        """
        Select parents based on novelty scores.
        """
        scores, descriptors = self.calculate_novelty_scores(population)
        self.update_archive(population, scores, descriptors)
        
        # Selection: Tournament
        parents = []
        for _ in range(num_parents):
            # Tournament size 3
            candidates = random.sample(population, 3)
            winner = max(candidates, key=lambda a: scores[a.id])
            parents.append(winner)
            
        return parents

    def get_stats(self):
        """Return current stats."""
        return {
            'archive_size': len(self.archive)
        }
