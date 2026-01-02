"""
KernelAgent - Foundational Agent Entity

This module implements the KernelAgent class, a simple container that owns
its own state and integrates with the CodonTranslator for phenotype development
and the AIS for lifecycle management.

Phase 1.3: Foundational Entity Classes
"""

import uuid
from typing import List, Dict, Optional
from .codon_translator import CodonTranslator


class KernelAgent:
    """
    Foundational agent entity with state sovereignty.
    
    Architecture Principles:
    - Owns its own state (id, genotype, relevance_score, age)
    - Simple container, not a complex simulation object
    - Integrates with CodonTranslator for phenotype development
    - Compatible with AIS through dictionary conversion
    """
    
    def __init__(self, genotype: str, agent_id: Optional[str] = None):
        """
        Create a KernelAgent with genetic code and AIS state.
        
        Args:
            genotype: Codon sequence (must be multiple of 3)
            agent_id: Optional unique identifier (UUID4 generated if None)
            
        Raises:
            ValueError: If genotype length is not a multiple of 3
        """
        if len(genotype) % 3 != 0:
            raise ValueError(f"Genotype length must be multiple of 3, got {len(genotype)}")
        
        self.id = agent_id if agent_id else str(uuid.uuid4())
        self.genotype = genotype.upper()
        
        # AIS state - entity owns this
        self.relevance_score = 1.0
        self.age = 0
        
        # Phenotype - None until developed
        self.phenotype: Optional[List[str]] = None
    
    def develop(self, translator: CodonTranslator) -> List[str]:
        """
        Translate genotype to phenotype using CodonTranslator.
        
        Args:
            translator: CodonTranslator instance
            
        Returns:
            List of phenotypic instructions (agent behaviors)
            
        Example:
            >>> agent = KernelAgent('AAAAATACA')
            >>> translator = CodonTranslator()
            >>> phenotype = agent.develop(translator)
            >>> phenotype
            ['move_forward', 'move_forward', 'turn_left']
        """
        self.phenotype = translator.translate_sequence(self.genotype, 'agent')
        return self.phenotype
    
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
    def from_dict(data: Dict, genotype: str, phenotype: Optional[List[str]] = None) -> 'KernelAgent':
        """
        Reconstruct KernelAgent from dictionary (after AIS processing).
        
        Args:
            data: Dictionary with id, relevance_score, age (from AIS)
            genotype: Original genotype string
            phenotype: Optional phenotype (if already developed)
            
        Returns:
            KernelAgent with updated state
            
        Example:
            >>> # After AIS cycle
            >>> updated_dict = {'id': 'abc', 'relevance_score': 0.95, 'age': 5}
            >>> agent = KernelAgent.from_dict(updated_dict, 'AAAAATACA')
            >>> agent.age
            5
        """
        agent = KernelAgent(genotype, agent_id=data['id'])
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
        return (f"KernelAgent(id={self.id[:8]}..., genotype={self.genotype[:12]}..., "
                f"age={self.age}, relevance={self.relevance_score:.2f}, "
                f"phenotype={'developed' if self.phenotype else 'undeveloped'})")


if __name__ == '__main__':
    # Demonstration
    print("=" * 60)
    print("KernelAgent Demonstration")
    print("=" * 60)
    print()
    
    # Create agent
    agent = KernelAgent('AAAAATACA')
    print(f"Created: {agent}")
    print(f"  ID: {agent.id}")
    print(f"  Genotype: {agent.genotype}")
    print(f"  Relevance Score: {agent.relevance_score}")
    print(f"  Age: {agent.age}")
    print()
    
    # Develop phenotype
    from .codon_translator import CodonTranslator
    translator = CodonTranslator()
    phenotype = agent.develop(translator)
    print(f"Developed phenotype: {phenotype}")
    print(f"  Agent: {agent}")
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
    print("State Sovereignty Verified:")
    print("  - Agent owns its id, genotype, relevance_score, age")
    print("  - Phenotype developed using CodonTranslator")
    print("  - Dictionary conversion enables AIS integration")
    print("=" * 60)
