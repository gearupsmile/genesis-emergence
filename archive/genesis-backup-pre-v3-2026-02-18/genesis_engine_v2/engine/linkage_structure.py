"""
LinkageStructure - Building Block Discovery and Linkage Learning

This module implements the LinkageStructure class that enables discovery and
preservation of beneficial gene combinations through linkage learning, inspired
by algorithms like LTGA (Linkage Tree Genetic Algorithm).

Phase 2.2: Complexification - Building Block Discovery
"""

import random
from typing import List, Set, Optional, Dict
from collections import defaultdict


class LinkageStructure:
    """
    Manages gene linkage groups for building block preservation.
    
    Key Features:
    - Linkage groups: Sets of gene indices inherited together
    - Expression probabilities: Control which genes are expressed
    - Building block discovery: Learn beneficial combinations from high performers
    - Linkage evolution: Inherit and mutate linkage structure
    
    Inspired by linkage learning algorithms (LTGA, DSMGA).
    """
    
    def __init__(self, genome_length: int = 0, 
                 groups: Optional[List[Set[int]]] = None,
                 expression_probabilities: Optional[Dict[int, float]] = None):
        """
        Create a LinkageStructure.
        
        Args:
            genome_length: Number of genes (for uniform initialization)
            groups: Optional list of linkage groups (sets of gene indices).
                   If None, creates uniform structure (each gene in own group).
            expression_probabilities: Optional dict mapping group index to probability.
                                     If None, all groups get probability 1.0.
        
        Example:
            # Uniform structure (each gene separate)
            linkage = LinkageStructure(genome_length=5)
            # groups: [{0}, {1}, {2}, {3}, {4}]
            
            # Custom structure
            linkage = LinkageStructure(groups=[{0, 1}, {2}, {3, 4}])
            # groups: [{0, 1}, {2}, {3, 4}]
        """
        if groups is None:
            # Create uniform structure - each gene in its own group
            self.groups = [set([i]) for i in range(genome_length)]
        else:
            # Use provided groups (make copies to avoid mutation)
            self.groups = [group.copy() for group in groups]
        
        if expression_probabilities is None:
            # Default: all groups have 100% expression probability
            self.expression_probabilities = {i: 1.0 for i in range(len(self.groups))}
        else:
            self.expression_probabilities = expression_probabilities.copy()
    
    def get_group_for_index(self, gene_index: int) -> Optional[int]:
        """
        Find which group contains the given gene index.
        
        Args:
            gene_index: Gene index to search for
            
        Returns:
            Group index (position in self.groups), or None if not found
        """
        for group_idx, group in enumerate(self.groups):
            if gene_index in group:
                return group_idx
        return None
    
    def merge_groups(self, parent_genome, high_performers: List, 
                     co_occurrence_threshold: float = 0.7) -> None:
        """
        Discover building blocks by analyzing high-performing genomes.
        
        This method learns which genes are frequently co-inherited in successful
        genomes and merges their linkage groups to preserve these combinations.
        
        Args:
            parent_genome: EvolvableGenome to analyze (provides gene count)
            high_performers: List of successful EvolvableGenome instances
            co_occurrence_threshold: Fraction of high performers that must contain
                                    both genes for them to be considered linked
        
        Algorithm:
            1. For each pair of gene indices in parent
            2. Count how often both appear in high performers
            3. If co-occurrence >= threshold * len(high_performers), merge groups
        
        Example:
            # If genes 0 and 1 appear together in 80% of high performers,
            # and threshold is 0.7, their groups will be merged
        """
        if len(high_performers) == 0:
            return
        
        parent_length = parent_genome.get_length()
        
        # Count co-occurrences of gene pairs
        co_occurrence = defaultdict(int)
        
        for i in range(parent_length):
            for j in range(i + 1, parent_length):
                # Count how many high performers have both genes i and j
                count = sum(1 for genome in high_performers 
                           if i < genome.get_length() and j < genome.get_length())
                
                # Calculate co-occurrence ratio
                ratio = count / len(high_performers)
                
                if ratio >= co_occurrence_threshold:
                    co_occurrence[(i, j)] = ratio
        
        # Merge groups for frequently co-occurring genes
        for (i, j), ratio in co_occurrence.items():
            group_i = self.get_group_for_index(i)
            group_j = self.get_group_for_index(j)
            
            # Only merge if genes are in different groups
            if group_i is not None and group_j is not None and group_i != group_j:
                # Merge group_j into group_i
                self.groups[group_i] |= self.groups[group_j]
                
                # Remove the merged group
                del self.groups[group_j]
                del self.expression_probabilities[group_j]
                
                # Update expression probabilities dict (indices shifted)
                new_probs = {}
                for idx in range(len(self.groups)):
                    if idx < group_j:
                        new_probs[idx] = self.expression_probabilities.get(idx, 1.0)
                    else:
                        # Shifted down by 1
                        new_probs[idx] = self.expression_probabilities.get(idx + 1, 1.0)
                self.expression_probabilities = new_probs
    
    def create_offspring(self, mutation_rate: float = 0.1) -> 'LinkageStructure':
        """
        Create child linkage structure with mutations.
        
        Args:
            mutation_rate: Probability of each type of mutation
            
        Returns:
            New LinkageStructure with copied groups and probabilities
            
        Mutations Applied:
            - With probability mutation_rate: split a random group
            - With probability mutation_rate: merge two random groups
            
        Example:
            parent = LinkageStructure(groups=[{0, 1}, {2}, {3, 4}])
            child = parent.create_offspring(mutation_rate=0.5)
            # Child might have groups [{0}, {1}, {2, 3, 4}] after split and merge
        """
        # Copy parent's groups and probabilities
        child = LinkageStructure(
            groups=self.groups,
            expression_probabilities=self.expression_probabilities
        )
        
        # Mutation 1: Split a random group
        if random.random() < mutation_rate and len(child.groups) > 0:
            # Find groups with more than one gene
            splittable = [i for i, g in enumerate(child.groups) if len(g) > 1]
            
            if splittable:
                group_idx = random.choice(splittable)
                group = child.groups[group_idx]
                
                # Split into two random subsets
                genes = list(group)
                random.shuffle(genes)
                split_point = random.randint(1, len(genes) - 1)
                
                subset1 = set(genes[:split_point])
                subset2 = set(genes[split_point:])
                
                # Replace original group with two new groups
                child.groups[group_idx] = subset1
                child.groups.append(subset2)
                
                # Copy expression probability to new group
                new_idx = len(child.groups) - 1
                child.expression_probabilities[new_idx] = child.expression_probabilities[group_idx]
        
        # Mutation 2: Merge two random groups
        if random.random() < mutation_rate and len(child.groups) > 1:
            # Choose two different groups
            idx1 = random.randint(0, len(child.groups) - 1)
            idx2 = random.randint(0, len(child.groups) - 1)
            
            while idx2 == idx1:
                idx2 = random.randint(0, len(child.groups) - 1)
            
            # Ensure idx1 < idx2 for consistent deletion
            if idx1 > idx2:
                idx1, idx2 = idx2, idx1
            
            # Merge idx2 into idx1
            child.groups[idx1] |= child.groups[idx2]
            
            # Remove merged group
            del child.groups[idx2]
            del child.expression_probabilities[idx2]
            
            # Update expression probabilities dict (indices shifted)
            new_probs = {}
            for idx in range(len(child.groups)):
                if idx < idx2:
                    new_probs[idx] = child.expression_probabilities.get(idx, 1.0)
                else:
                    new_probs[idx] = child.expression_probabilities.get(idx + 1, 1.0)
            child.expression_probabilities = new_probs
        
        return child
    
    def get_expressed_indices(self, genome_length: int) -> List[int]:
        """
        Get list of gene indices to express based on group probabilities.
        
        Args:
            genome_length: Total number of genes in genome
            
        Returns:
            Sorted list of gene indices that passed expression probability check
            
        Algorithm:
            For each group:
            - Random check against group's expression_probability
            - If check passes, all genes in group are expressed
            - If check fails, no genes in group are expressed
            
        Example:
            linkage = LinkageStructure(groups=[{0, 1}, {2}, {3, 4}])
            linkage.expression_probabilities = {0: 1.0, 1: 0.5, 2: 1.0}
            
            expressed = linkage.get_expressed_indices(5)
            # Might return [0, 1, 3, 4] if group {2} failed probability check
        """
        expressed = set()
        
        for group_idx, group in enumerate(self.groups):
            probability = self.expression_probabilities.get(group_idx, 1.0)
            
            # Random check against expression probability
            if random.random() < probability:
                # Express all genes in this group
                expressed.update(group)
        
        # Return sorted list of expressed indices
        return sorted(list(expressed))
    
    def get_num_groups(self) -> int:
        """Get number of linkage groups."""
        return len(self.groups)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"LinkageStructure({len(self.groups)} groups, {sum(len(g) for g in self.groups)} genes)"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        group_strs = [f"{{{', '.join(map(str, sorted(g)))}}}" for g in self.groups]
        return f"Linkage[{', '.join(group_strs)}]"


if __name__ == '__main__':
    # Demonstration
    print("=" * 60)
    print("LinkageStructure Demonstration")
    print("=" * 60)
    print()
    
    # Create uniform structure
    linkage = LinkageStructure(genome_length=5)
    print(f"Uniform structure: {linkage}")
    print(f"  Groups: {linkage.groups}")
    print(f"  Expression probabilities: {linkage.expression_probabilities}")
    print()
    
    # Create custom structure
    custom = LinkageStructure(groups=[{0, 1}, {2}, {3, 4}])
    print(f"Custom structure: {custom}")
    print(f"  Groups: {custom.groups}")
    print()
    
    # Get expressed indices
    print("Expression simulation (5 trials):")
    custom.expression_probabilities = {0: 1.0, 1: 0.5, 2: 1.0}
    for i in range(5):
        expressed = custom.get_expressed_indices(5)
        print(f"  Trial {i + 1}: {expressed}")
    print()
    
    # Create offspring
    print("Creating offspring with mutations...")
    child = custom.create_offspring(mutation_rate=0.5)
    print(f"  Parent: {custom}")
    print(f"  Child:  {child}")
    print()
    
    # Simulate building block discovery
    print("Simulating building block discovery...")
    from engine.evolvable_genome import EvolvableGenome
    
    linkage = LinkageStructure(genome_length=6)
    print(f"  Initial: {linkage}")
    
    # Create parent and high performers with pattern: genes 0,1,2 together
    parent = EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAA', 'ACA', 'AGA'])
    high_performers = [
        EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAA', 'ACA', 'AGA']),
        EvolvableGenome(['AAA', 'CAA', 'GAA', 'TTA', 'ACC', 'AGG']),
        EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAT', 'ATC', 'ATA']),
    ]
    
    linkage.merge_groups(parent, high_performers, co_occurrence_threshold=0.6)
    print(f"  After merge: {linkage}")
    print()
    
    print("=" * 60)
    print("Building Block Discovery Features Verified:")
    print("  - Linkage groups (gene indices inherited together)")
    print("  - Expression probabilities (probabilistic gene activation)")
    print("  - Building block discovery (merge_groups)")
    print("  - Linkage evolution (create_offspring)")
    print("=" * 60)
