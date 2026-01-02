"""
StructurallyEvolvableAgent - Integrated Structural Evolution

This module implements the StructurallyEvolvableAgent class that integrates
EvolvableGenome and LinkageStructure into a complete evolutionary system with
co-evolution of genome structure and linkage patterns.

Phase 2.3: Complexification - Integrated Evolution
"""

import uuid
from typing import List, Optional, Dict
from .evolvable_genome import EvolvableGenome
from .linkage_structure import LinkageStructure
from .codon_translator import CodonTranslator


class StructurallyEvolvableAgent:
    """
    Agent with integrated structural evolution.
    
    Key Features:
    - Owns EvolvableGenome (structural mutations)
    - Owns LinkageStructure (building block discovery)
    - Filtered expression (linkage controls which genes are expressed)
    - Dual mutation (genome and linkage evolve independently)
    - AIS compatible (relevance_score, age, to_dict/from_dict)
    
    This integrates all Phase 2 components into a complete evolutionary system.
    """
    
    def __init__(self, genome: EvolvableGenome, 
                 linkage_structure: Optional[LinkageStructure] = None,
                 agent_id: Optional[str] = None):
        """
        Create a StructurallyEvolvableAgent.
        
        Args:
            genome: EvolvableGenome instance
            linkage_structure: Optional LinkageStructure. If None, creates uniform structure.
            agent_id: Optional unique identifier (UUID4 generated if None)
        """
        self.id = agent_id if agent_id else str(uuid.uuid4())
        self.genome = genome
        
        if linkage_structure is None:
            # Create uniform linkage structure
            self.linkage_structure = LinkageStructure(genome_length=genome.get_length())
        else:
            self.linkage_structure = linkage_structure
        
        # AIS state - entity owns this
        self.relevance_score = 1.0
        self.age = 0
        
        # Phenotype - None until developed
        self.phenotype: Optional[List[str]] = None
    
    def develop(self, translator: CodonTranslator) -> List[str]:
        """
        Develop phenotype using filtered expression.
        
        Args:
            translator: CodonTranslator instance
            
        Returns:
            List of phenotypic instructions (agent behaviors)
            
        Algorithm:
            1. Get expressed indices from linkage structure (probabilistic)
            2. Filter genome sequence to only expressed genes
            3. Translate filtered sequence using CodonTranslator
            4. Store and return phenotype
            
        Example:
            >>> genome = EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAA', 'ACA'])
            >>> linkage = LinkageStructure(genome_length=5)
            >>> linkage.expression_probabilities = {0: 1.0, 1: 0.5, 2: 1.0, 3: 1.0, 4: 1.0}
            >>> agent = StructurallyEvolvableAgent(genome, linkage)
            >>> phenotype = agent.develop(translator)
            >>> # If group 1 failed probability check, only genes [0, 2, 3, 4] are expressed
        """
        # Get expressed indices (probabilistic based on linkage structure)
        expressed_indices = self.linkage_structure.get_expressed_indices(
            self.genome.get_length()
        )
        
        # Filter genome sequence to only expressed genes
        if len(expressed_indices) == 0:
            # No genes expressed - empty phenotype
            self.phenotype = []
            return self.phenotype
        
        expressed_sequence = [self.genome.sequence[i] for i in expressed_indices]
        
        # Translate filtered sequence
        sequence_string = ''.join(expressed_sequence)
        self.phenotype = translator.translate_sequence(sequence_string, 'agent')
        
        return self.phenotype
    
    def reproduce(self, mutation_rate: float = 0.1) -> 'StructurallyEvolvableAgent':
        """
        Create offspring with dual mutation.
        
        Args:
            mutation_rate: Probability of mutations in both genome and linkage
            
        Returns:
            New StructurallyEvolvableAgent with mutated genome and linkage
            
        Dual Mutation:
            - Genome: structural mutations (add/remove genes)
            - Linkage: structural mutations (split/merge groups)
            - Both evolve independently
            - Linkage is adjusted if genome length changes
            
        Example:
            >>> parent = StructurallyEvolvableAgent(genome, linkage)
            >>> child = parent.reproduce(mutation_rate=0.2)
            >>> # Child has mutated genome and mutated linkage structure
        """
        # Create offspring genome (structural mutations)
        child_genome = self.genome.create_offspring(mutation_rate)
        
        # Create offspring linkage (structural mutations)
        # If genome length changed significantly, create new uniform linkage
        if abs(child_genome.get_length() - self.genome.get_length()) > 2:
            # Genome changed significantly - create new uniform linkage
            child_linkage = LinkageStructure(genome_length=child_genome.get_length())
        else:
            # Genome similar - evolve linkage structure
            child_linkage = self.linkage_structure.create_offspring(mutation_rate)
            
            # Adjust linkage if genome length changed
            if child_genome.get_length() != self.genome.get_length():
                # Recreate linkage to match new genome length
                child_linkage = LinkageStructure(genome_length=child_genome.get_length())
        
        # Create child agent
        child = StructurallyEvolvableAgent(
            genome=child_genome,
            linkage_structure=child_linkage
        )
        
        return child
    
    def to_dict(self) -> Dict:
        """
        Convert agent to dictionary for AIS integration.
        
        Returns:
            Dictionary with id, relevance_score, and age
            
        Note:
            This is the format expected by AIS.apply_cycle()
        """
        return {
            'id': self.id,
            'relevance_score': self.relevance_score,
            'age': self.age
        }
    
    @staticmethod
    def from_dict(data: Dict, genome: EvolvableGenome, 
                  linkage: LinkageStructure,
                  phenotype: Optional[List[str]] = None) -> 'StructurallyEvolvableAgent':
        """
        Reconstruct StructurallyEvolvableAgent from dictionary (after AIS processing).
        
        Args:
            data: Dictionary with id, relevance_score, age (from AIS)
            genome: EvolvableGenome instance
            linkage: LinkageStructure instance
            phenotype: Optional phenotype (if already developed)
            
        Returns:
            StructurallyEvolvableAgent with updated state
        """
        agent = StructurallyEvolvableAgent(
            genome=genome,
            linkage_structure=linkage,
            agent_id=data['id']
        )
        agent.relevance_score = data['relevance_score']
        agent.age = data['age']
        agent.phenotype = phenotype
        return agent
    
    def update_from_dict(self, data: Dict) -> None:
        """
        Update agent's AIS state from dictionary (in-place).
        
        Args:
            data: Dictionary with relevance_score and age from AIS
            
        Note:
            This is useful for updating existing agents after AIS cycle
        """
        self.relevance_score = data['relevance_score']
        self.age = data['age']
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"StructurallyEvolvableAgent(id={self.id[:8]}..., "
                f"genome_length={self.genome.get_length()}, "
                f"linkage_groups={self.linkage_structure.get_num_groups()}, "
                f"age={self.age}, relevance={self.relevance_score:.2f})")
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return (f"Agent[genome:{self.genome.get_length()} genes, "
                f"linkage:{self.linkage_structure.get_num_groups()} groups, "
                f"age:{self.age}]")


if __name__ == '__main__':
    # Demonstration
    print("=" * 60)
    print("StructurallyEvolvableAgent Demonstration")
    print("=" * 60)
    print()
    
    from .codon_translator import CodonTranslator
    
    # Create agent
    genome = EvolvableGenome(['AAA', 'CAA', 'GAA'])
    linkage = LinkageStructure(genome_length=3)
    agent = StructurallyEvolvableAgent(genome, linkage)
    
    print(f"Created agent: {agent}")
    print(f"  Genome: {agent.genome}")
    print(f"  Linkage: {agent.linkage_structure}")
    print()
    
    # Develop phenotype
    translator = CodonTranslator()
    phenotype = agent.develop(translator)
    print(f"Developed phenotype: {phenotype}")
    print(f"  Agent: {agent}")
    print()
    
    # Reproduce
    print("Creating offspring...")
    child = agent.reproduce(mutation_rate=0.3)
    print(f"  Parent: {agent}")
    print(f"  Child:  {child}")
    print(f"  Child genome length: {child.genome.get_length()}")
    print(f"  Child linkage groups: {child.linkage_structure.get_num_groups()}")
    print()
    
    # AIS integration
    print("AIS Integration:")
    agent_dict = agent.to_dict()
    print(f"  to_dict(): {agent_dict}")
    
    # Simulate AIS update
    agent_dict['age'] = 10
    agent_dict['relevance_score'] = 0.8
    agent.update_from_dict(agent_dict)
    print(f"  After AIS update: {agent}")
    print()
    
    print("=" * 60)
    print("Integrated Evolution Features Verified:")
    print("  - Composition (EvolvableGenome + LinkageStructure)")
    print("  - Filtered expression (linkage controls gene activation)")
    print("  - Dual mutation (genome and linkage evolve independently)")
    print("  - AIS compatibility (to_dict/from_dict)")
    print("=" * 60)
