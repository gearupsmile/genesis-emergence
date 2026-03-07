"""
Artificial Immune System (AIS) - Stateless Universal Law

This module implements the AIS as a stateless rule applier that enforces
forgetting and purging laws on entities. The AIS does NOT maintain entity
state - each entity owns its own relevance_score and age.

Phase 1.2: Entity Lifecycle Management through Universal Laws
"""

from typing import List, Dict, Tuple


class ArtificialImmuneSystem:
    """
    Stateless universal law that applies forgetting & purging rules.
    
    Architecture Principles:
    - NO internal entity state or registry
    - Pure function design (deterministic, no side effects)
    - Entity sovereignty (entities own their relevance_score and age)
    
    The AIS applies two universal laws:
    1. Forgetting Rule: After expiry_cycle, relevance_score decays by decay_rate
    2. Purging Rule: Entities with relevance_score < viability_threshold are removed
    """
    
    def __init__(self, expiry_cycle: int = 1000, decay_rate: float = 0.001, 
                 viability_threshold: float = 0.1):
        """
        Initialize the AIS with immutable law parameters.
        
        Args:
            expiry_cycle: Number of cycles before decay begins (default: 1000)
            decay_rate: Amount to decay relevance_score per cycle after expiry (default: 0.001)
            viability_threshold: Minimum relevance_score for survival (default: 0.1)
            
        Note:
            These parameters define universal laws. The AIS does NOT store entity state.
        """
        self.expiry_cycle = expiry_cycle
        self.decay_rate = decay_rate
        self.viability_threshold = viability_threshold
    
    def apply_cycle(self, entities: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """
        Apply forgetting & purging rules to entity dictionaries.
        
        This is a PURE FUNCTION - it does not modify input or maintain state.
        
        Args:
            entities: List of entity dictionaries, each with keys:
                - 'id' (str): Unique entity identifier
                - 'relevance_score' (float): Current relevance (0.0 to 1.0)
                - 'age' (int): Number of cycles since entity creation
                
        Returns:
            Tuple of (updated_entities, purged_ids):
                - updated_entities: List of surviving entities with updated state
                - purged_ids: List of IDs for entities that were purged
                
        Rules Applied (in order):
            1. Increment age for all entities
            2. If age >= expiry_cycle: decay relevance_score by decay_rate
            3. Purge entities where relevance_score < viability_threshold
            
        Example:
            >>> ais = ArtificialImmuneSystem(expiry_cycle=1000, decay_rate=0.001, viability_threshold=0.1)
            >>> entities = [{'id': 'e1', 'relevance_score': 1.0, 'age': 0}]
            >>> updated, purged = ais.apply_cycle(entities)
            >>> updated[0]['age']
            1
            >>> updated[0]['relevance_score']
            1.0
            >>> purged
            []
        """
        updated_entities = []
        purged_ids = []
        
        for entity in entities:
            # Create a copy to avoid mutating input (pure function principle)
            updated_entity = entity.copy()
            
            # Rule 1: Increment age
            updated_entity['age'] += 1
            
            # Rule 2: Forgetting - decay relevance after expiry
            if updated_entity['age'] >= self.expiry_cycle:
                updated_entity['relevance_score'] -= self.decay_rate
                # Ensure score doesn't go negative
                updated_entity['relevance_score'] = max(0.0, updated_entity['relevance_score'])
            
            # Rule 3: Purging - remove entities below viability threshold
            if updated_entity['relevance_score'] < self.viability_threshold:
                purged_ids.append(updated_entity['id'])
            else:
                updated_entities.append(updated_entity)
        
        return updated_entities, purged_ids
    
    def get_parameters(self) -> Dict[str, float]:
        """
        Get the immutable law parameters.
        
        Returns:
            Dictionary with expiry_cycle, decay_rate, and viability_threshold
        """
        return {
            'expiry_cycle': self.expiry_cycle,
            'decay_rate': self.decay_rate,
            'viability_threshold': self.viability_threshold
        }
    
    def calculate_lifetime(self) -> int:
        """
        Calculate the expected lifetime of an inert entity (no relevance boosts).
        
        Returns:
            Number of cycles until an inert entity is purged
            
        Formula:
            lifetime = expiry_cycle + (1.0 - viability_threshold) / decay_rate
            
        Example:
            With defaults (expiry=1000, decay=0.001, threshold=0.1):
            lifetime = 1000 + (1.0 - 0.1) / 0.001 = 1000 + 900 = 1900 cycles
        """
        decay_cycles = (1.0 - self.viability_threshold) / self.decay_rate
        return int(self.expiry_cycle + decay_cycles)


if __name__ == '__main__':
    # Demonstration of stateless AIS
    print("=" * 60)
    print("Artificial Immune System - Stateless Universal Law")
    print("=" * 60)
    print()
    
    # Create AIS with default parameters
    ais = ArtificialImmuneSystem()
    
    print("AIS Parameters:")
    params = ais.get_parameters()
    for key, value in params.items():
        print(f"  {key}: {value}")
    print()
    
    print(f"Expected inert entity lifetime: {ais.calculate_lifetime()} cycles")
    print()
    
    # Demonstrate entity lifecycle
    print("Entity Lifecycle Demonstration:")
    print("-" * 60)
    
    # Create a single entity
    entities = [{'id': 'demo_entity', 'relevance_score': 1.0, 'age': 0}]
    
    # Simulate key lifecycle points
    checkpoints = [0, 999, 1000, 1001, 1500, 1900, 1901]
    
    for target_cycle in checkpoints:
        # Fast-forward to target cycle
        while entities and entities[0]['age'] < target_cycle:
            entities, purged = ais.apply_cycle(entities)
        
        if entities:
            entity = entities[0]
            print(f"Cycle {entity['age']:4d}: "
                  f"relevance_score = {entity['relevance_score']:.3f} "
                  f"{'(decay active)' if entity['age'] >= ais.expiry_cycle else '(no decay)'}")
        else:
            print(f"Cycle {target_cycle:4d}: PURGED")
            break
    
    print()
    print("=" * 60)
    print("Stateless Design Verified:")
    print("  - AIS stores only immutable parameters")
    print("  - Entities own their relevance_score and age")
    print("  - apply_cycle is a pure function")
    print("=" * 60)
