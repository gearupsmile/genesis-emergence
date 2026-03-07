"""
KernelWorld - Foundational World/Environment Entity

This module implements the KernelWorld class, a simple container that owns
its own state and integrates with the CodonTranslator for physics development
and the AIS for lifecycle management.

Phase 1.3: Foundational Entity Classes
"""

import uuid
from typing import List, Dict, Optional
from .codon_translator import CodonTranslator


class KernelWorld:
    """
    Foundational world/environment entity with state sovereignty.
    
    Architecture Principles:
    - Owns its own state (id, genotype, relevance_score, age)
    - Simple container, not a complex simulation object
    - Integrates with CodonTranslator for physics development
    - Compatible with AIS through dictionary conversion
    """
    
    def __init__(self, genotype: str, world_id: Optional[str] = None):
        """
        Create a KernelWorld with genetic code and AIS state.
        
        Args:
            genotype: Codon sequence (must be multiple of 3)
            world_id: Optional unique identifier (UUID4 generated if None)
            
        Raises:
            ValueError: If genotype length is not a multiple of 3
        """
        if len(genotype) % 3 != 0:
            raise ValueError(f"Genotype length must be multiple of 3, got {len(genotype)}")
        
        self.id = world_id if world_id else str(uuid.uuid4())
        self.genotype = genotype.upper()
        
        # AIS state - entity owns this
        self.relevance_score = 1.0
        self.age = 0
        
        # Physics rules - None until developed
        self.physics_rules: Optional[List[str]] = None
    
    def develop_physics(self, translator: CodonTranslator) -> List[str]:
        """
        Translate genotype to physics_rules using CodonTranslator.
        
        Args:
            translator: CodonTranslator instance
            
        Returns:
            List of physics parameter instructions
            
        Example:
            >>> world = KernelWorld('GAAGCTGGA')
            >>> translator = CodonTranslator()
            >>> physics = world.develop_physics(translator)
            >>> physics
            ['increase_resources', 'decrease_resources', 'raise_temperature']
        """
        self.physics_rules = translator.translate_sequence(self.genotype, 'world')
        return self.physics_rules
    
    def to_dict(self) -> Dict:
        """
        Convert world to dictionary for AIS integration.
        
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
    def from_dict(data: Dict, genotype: str, physics_rules: Optional[List[str]] = None) -> 'KernelWorld':
        """
        Reconstruct KernelWorld from dictionary (after AIS processing).
        
        Args:
            data: Dictionary with id, relevance_score, age (from AIS)
            genotype: Original genotype string
            physics_rules: Optional physics rules (if already developed)
            
        Returns:
            KernelWorld with updated state
            
        Example:
            >>> # After AIS cycle
            >>> updated_dict = {'id': 'xyz', 'relevance_score': 0.95, 'age': 5}
            >>> world = KernelWorld.from_dict(updated_dict, 'GAAGCTGGA')
            >>> world.age
            5
        """
        world = KernelWorld(genotype, world_id=data['id'])
        world.relevance_score = data['relevance_score']
        world.age = data['age']
        world.physics_rules = physics_rules
        return world
    
    def update_from_dict(self, data: Dict) -> None:
        """
        Update world's AIS state from dictionary (in-place).
        
        Args:
            data: Dictionary with relevance_score and age from AIS
            
        Note:
            This is useful for updating existing worlds after AIS cycle
        """
        self.relevance_score = data['relevance_score']
        self.age = data['age']
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"KernelWorld(id={self.id[:8]}..., genotype={self.genotype[:12]}..., "
                f"age={self.age}, relevance={self.relevance_score:.2f}, "
                f"physics={'developed' if self.physics_rules else 'undeveloped'})")


if __name__ == '__main__':
    # Demonstration
    print("=" * 60)
    print("KernelWorld Demonstration")
    print("=" * 60)
    print()
    
    # Create world
    world = KernelWorld('GAAGCTGGA')
    print(f"Created: {world}")
    print(f"  ID: {world.id}")
    print(f"  Genotype: {world.genotype}")
    print(f"  Relevance Score: {world.relevance_score}")
    print(f"  Age: {world.age}")
    print()
    
    # Develop physics
    from .codon_translator import CodonTranslator
    translator = CodonTranslator()
    physics = world.develop_physics(translator)
    print(f"Developed physics: {physics}")
    print(f"  World: {world}")
    print()
    
    # AIS integration
    print("AIS Integration:")
    world_dict = world.to_dict()
    print(f"  to_dict(): {world_dict}")
    
    # Simulate AIS update
    world_dict['age'] = 10
    world_dict['relevance_score'] = 0.8
    world.update_from_dict(world_dict)
    print(f"  After AIS update: {world}")
    print()
    
    print("=" * 60)
    print("State Sovereignty Verified:")
    print("  - World owns its id, genotype, relevance_score, age")
    print("  - Physics developed using CodonTranslator")
    print("  - Dictionary conversion enables AIS integration")
    print("=" * 60)
