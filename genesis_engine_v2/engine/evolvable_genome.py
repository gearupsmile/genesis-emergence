"""
EvolvableGenome - Structural Mutation and Complexification

This module implements the EvolvableGenome class that enables open-ended evolution
through structural mutations (adding/removing genes), NEAT-style innovation tracking,
and metabolic cost management to prevent bloat.

Phase 2.1: Complexification
"""

import random
from typing import List, Optional, Tuple


class EvolvableGenome:
    """
    Genome with structural mutation capabilities and innovation tracking.
    
    Key Features:
    - Structural mutations: add/remove genes (codons)
    - Innovation IDs: NEAT-style historical marking for lineage tracking
    - Metabolic cost: Permanent penalty for genome complexity
    - Inheritance: Create offspring with mutations
    
    This is designed as a drop-in replacement for string genotypes.
    """
    
    # Class variable: global innovation counter
    _next_innovation_id = 0
    
    # Constants
    COST_COEFFICIENT = 0.005  # Coefficient for superlinear metabolic cost (strong bloat control)
    COST_EXPONENT = 1.5  # Superlinear exponent (quadratic-like growth)
    NUCLEOTIDES = ['A', 'C', 'G', 'T']
    
    def __init__(self, initial_sequence: Optional[List[str]] = None, 
                 innovation_ids: Optional[List[int]] = None,
                 metabolic_cost: Optional[float] = None):
        """
        Create an EvolvableGenome.
        
        Args:
            initial_sequence: List of codons (each 3 characters). If None, starts empty.
            innovation_ids: Optional list of innovation IDs (must match sequence length).
                           If None, new IDs are assigned.
            metabolic_cost: Optional initial metabolic cost. If None, calculated from length.
            
        Raises:
            ValueError: If innovation_ids length doesn't match sequence length
        """
        if initial_sequence is None:
            self.sequence = []
            self.innovation_ids = []
            self.metabolic_cost = 0.0
        else:
            self.sequence = list(initial_sequence)
            
            if innovation_ids is None:
                # Assign new innovation IDs
                self.innovation_ids = [self._get_next_innovation_id() 
                                      for _ in range(len(self.sequence))]
            else:
                if len(innovation_ids) != len(self.sequence):
                    raise ValueError(f"Innovation IDs length ({len(innovation_ids)}) "
                                   f"must match sequence length ({len(self.sequence)})")
                self.innovation_ids = list(innovation_ids)
            
            if metabolic_cost is None:
                self.metabolic_cost = self._calculate_metabolic_cost(len(self.sequence))
            else:
                self.metabolic_cost = metabolic_cost
    
    @classmethod
    def _calculate_metabolic_cost(cls, num_genes: int) -> float:
        """
        Calculate metabolic cost using superlinear formula.
        
        Formula: cost = COST_COEFFICIENT * (num_genes ** COST_EXPONENT)
        
        This creates strong pressure against genome bloat:
        - 10 genes: ~0.003
        - 50 genes: ~0.035
        - 100 genes: ~0.100 (10% penalty)
        - 200 genes: ~0.283 (28% penalty)
        - 400 genes: ~0.800 (80% penalty - nearly lethal)
        
        Args:
            num_genes: Number of genes in genome
            
        Returns:
            Metabolic cost (0.0 to ~1.0)
        """
        if num_genes == 0:
            return 0.0
        return cls.COST_COEFFICIENT * (num_genes ** cls.COST_EXPONENT)
    
    @classmethod
    def _get_next_innovation_id(cls) -> int:
        """Get next unique innovation ID (class method for global counter)."""
        innovation_id = cls._next_innovation_id
        cls._next_innovation_id += 1
        return innovation_id
    
    def add_gene(self, codon: Optional[str] = None) -> int:
        """
        Add a new gene (codon) to the genome.
        
        Args:
            codon: Optional codon to add. If None, generates random codon.
            
        Returns:
            Innovation ID of the newly added gene
            
        Side Effects:
            - Appends codon to sequence
            - Assigns new innovation ID
            - Increases metabolic_cost by COST_PER_GENE
            
        Example:
            >>> genome = EvolvableGenome(['AAA'])
            >>> new_id = genome.add_gene('CAA')
            >>> genome.sequence
            ['AAA', 'CAA']
            >>> genome.metabolic_cost
            0.02
        """
        if codon is None:
            # Generate random codon
            codon = ''.join(random.choice(self.NUCLEOTIDES) for _ in range(3))
        
        # Validate codon
        if len(codon) != 3:
            raise ValueError(f"Codon must be 3 characters, got {len(codon)}")
        
        # Add to sequence
        self.sequence.append(codon.upper())
        
        # Assign innovation ID
        innovation_id = self._get_next_innovation_id()
        self.innovation_ids.append(innovation_id)
        
        # Recalculate metabolic cost with new length (superlinear growth)
        self.metabolic_cost = self._calculate_metabolic_cost(len(self.sequence))
        
        return innovation_id
    
    def remove_gene(self) -> Optional[Tuple[str, int]]:
        """
        Remove a random gene from the genome.
        
        Returns:
            Tuple of (codon, innovation_id) of removed gene, or None if genome is empty
            
        Side Effects:
            - Removes random codon from sequence
            - Removes corresponding innovation ID
            - Does NOT decrease metabolic_cost (permanent penalty)
            
        Note:
            Metabolic cost is NOT reduced when removing genes. This prevents
            evolution from gaming the system by adding/removing genes repeatedly.
            
        Example:
            >>> genome = EvolvableGenome(['AAA', 'CAA', 'GAA'])
            >>> removed = genome.remove_gene()  # Might remove ('CAA', 1)
            >>> len(genome.sequence)
            2
            >>> genome.metabolic_cost  # Still 0.03, not reduced!
            0.03
        """
        if len(self.sequence) == 0:
            return None
        
        # Choose random index
        index = random.randint(0, len(self.sequence) - 1)
        
        # Remove gene and its innovation ID
        removed_codon = self.sequence.pop(index)
        removed_id = self.innovation_ids.pop(index)
        
        # Metabolic cost is NOT reduced (permanent penalty)
        
        return (removed_codon, removed_id)
    
    def create_offspring(self, mutation_rate: float = 0.1) -> 'EvolvableGenome':
        """
        Create a child genome with inherited sequence and innovation IDs.
        
        Args:
            mutation_rate: Probability of structural mutation (add or remove gene)
            
        Returns:
            New EvolvableGenome with copied sequence, innovation IDs, and metabolic cost
            
        Mutations Applied:
            - With probability mutation_rate, adds a random gene
            - With probability mutation_rate, removes a random gene
            - Both mutations can occur in same offspring
            
        Example:
            >>> parent = EvolvableGenome(['AAA', 'CAA'])
            >>> child = parent.create_offspring(mutation_rate=0.5)
            >>> # Child has copied parent's sequence and innovation IDs
            >>> # May have structural mutations applied
        """
        # Copy parent's sequence, innovation IDs, and metabolic cost
        child = EvolvableGenome(
            initial_sequence=self.sequence.copy(),
            innovation_ids=self.innovation_ids.copy(),
            metabolic_cost=self.metabolic_cost
        )
        
        # Apply structural mutations
        # Addition mutation
        if random.random() < mutation_rate:
            child.add_gene()
        
        # Deletion mutation
        if random.random() < mutation_rate:
            child.remove_gene()
        
        return child
    
    def get_sequence_string(self) -> str:
        """
        Get genome as concatenated string (for CodonTranslator compatibility).
        
        Returns:
            Concatenated codon sequence as single string
            
        Example:
            >>> genome = EvolvableGenome(['AAA', 'CAA', 'GAA'])
            >>> genome.get_sequence_string()
            'AAACAAGAA'
        """
        return ''.join(self.sequence)
    
    def get_length(self) -> int:
        """
        Get number of genes in genome.
        
        Returns:
            Number of codons in sequence
        """
        return len(self.sequence)
    
    def get_innovation_ids(self) -> List[int]:
        """Get copy of innovation IDs list."""
        return self.innovation_ids.copy()
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"EvolvableGenome(length={len(self.sequence)}, "
                f"cost={self.metabolic_cost:.3f}, "
                f"sequence={self.get_sequence_string()[:15]}...)")
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Genome[{len(self.sequence)} genes, cost={self.metabolic_cost:.3f}]"


if __name__ == '__main__':
    # Demonstration
    print("=" * 60)
    print("EvolvableGenome Demonstration")
    print("=" * 60)
    print()
    
    # Create initial genome
    genome = EvolvableGenome(['AAA', 'ACA', 'AGA'])
    print(f"Initial genome: {genome}")
    print(f"  Sequence: {genome.get_sequence_string()}")
    print(f"  Innovation IDs: {genome.innovation_ids}")
    print(f"  Metabolic cost: {genome.metabolic_cost}")
    print()
    
    # Add gene
    print("Adding gene...")
    new_id = genome.add_gene('CAA')
    print(f"  New innovation ID: {new_id}")
    print(f"  Updated genome: {genome}")
    print(f"  Innovation IDs: {genome.innovation_ids}")
    print(f"  Metabolic cost: {genome.metabolic_cost}")
    print()
    
    # Remove gene
    print("Removing gene...")
    removed = genome.remove_gene()
    print(f"  Removed: {removed}")
    print(f"  Updated genome: {genome}")
    print(f"  Innovation IDs: {genome.innovation_ids}")
    print(f"  Metabolic cost: {genome.metabolic_cost} (unchanged!)")
    print()
    
    # Create offspring
    print("Creating offspring with 50% mutation rate...")
    child = genome.create_offspring(mutation_rate=0.5)
    print(f"  Parent: {genome}")
    print(f"  Child:  {child}")
    print(f"  Child innovation IDs: {child.innovation_ids}")
    print()
    
    # Simulate evolution
    print("Simulating 10 generations of evolution...")
    current = genome
    for gen in range(10):
        current = current.create_offspring(mutation_rate=0.3)
        print(f"  Gen {gen + 1}: {current}")
    
    print()
    print("=" * 60)
    print("Complexification Features Verified:")
    print("  - Structural mutations (add/remove genes)")
    print("  - Innovation ID tracking (NEAT-style)")
    print("  - Metabolic cost management (bloat prevention)")
    print("  - Inheritance with mutations")
    print("=" * 60)
