"""
PhysicalInvariantGatekeeper - External Enforcer of Immutable Physical Laws

This class operates OUTSIDE the evolvable agent logic to ensure agents
cannot evolve around constraints. It is the final authority on agent viability.

The key insight from the 200k failure: metabolic cost was a FACTOR in fitness
calculation, not a CONDITION of existence. Agents evolved to game the fitness
function while violating the intended physical constraints.

The Gatekeeper enforces constraints as PHYSICAL INVARIANTS:
- If metabolic_cost > PHYSICAL_ENERGY_CONSTANT: agent is TERMINATED
- This is not negotiable, not evolvable, not a fitness penalty
- It is a law of physics in this universe

Phase 2 - Pillar 2: Physical Invariant Architecture
"""

from typing import List, Tuple, Dict, Optional
import time


class PhysicalInvariantGatekeeper:
    """
    External enforcer of immutable physical laws.
    
    This class operates as the "physics engine" of the simulation,
    enforcing constraints that agents cannot evolve around.
    
    Design Principles:
    1. EXTERNAL: Operates outside agent logic (agents can't bypass)
    2. BINARY: Makes life/death decisions, not fitness adjustments
    3. IMMUTABLE: Uses raw values, no transformations agents could exploit
    4. TRANSPARENT: Logs all violations for analysis
    """
    
    # Physical constants (immutable laws of this universe)
    PHYSICAL_ENERGY_CONSTANT = 0.5  # Maximum allowed metabolic cost
    
    def __init__(self, energy_constant: Optional[float] = None, log_violations: bool = True):
        """
        Initialize the Physics Gatekeeper.
        
        Args:
            energy_constant: Override default PHYSICAL_ENERGY_CONSTANT (for testing)
            log_violations: Whether to log violations (default: True)
        """
        if energy_constant is not None:
            self.energy_constant = energy_constant
        else:
            self.energy_constant = self.PHYSICAL_ENERGY_CONSTANT
        
        self.log_violations = log_violations
        
        # Statistics tracking
        self.total_checks = 0
        self.total_violations = 0
        self.violation_log = []
    
    def check_viability(self, agent) -> bool:
        """
        Binary life/death decision based on physical law.
        
        This is the core enforcement mechanism. An agent either meets
        the physical constraints (alive) or violates them (terminated).
        
        Args:
            agent: StructurallyEvolvableAgent instance
            
        Returns:
            True if agent meets physical constraints (viable)
            False if agent violates constraints (non-viable, will be terminated)
        """
        self.total_checks += 1
        
        # IMMUTABLE LAW: metabolic cost must not exceed energy constant
        metabolic_cost = agent.genome.metabolic_cost
        
        if metabolic_cost > self.energy_constant:
            # VIOLATION: Agent exceeds physical energy limit
            self.total_violations += 1
            
            if self.log_violations:
                self._log_violation(agent, metabolic_cost)
            
            return False  # Non-viable (will be terminated)
        
        return True  # Viable (meets physical constraints)
    
    def enforce_population_constraints(self, population: List) -> Tuple[List, List]:
        """
        Apply physical laws to entire population.
        
        This method processes all agents and separates them into:
        - Survivors: agents that meet physical constraints
        - Terminated: agents that violate physical constraints
        
        Args:
            population: List of StructurallyEvolvableAgent instances
            
        Returns:
            Tuple of (surviving_agents, terminated_agent_ids)
        """
        survivors = []
        terminated_ids = []
        
        for agent in population:
            if self.check_viability(agent):
                survivors.append(agent)
            else:
                terminated_ids.append(agent.id)
        
        return survivors, terminated_ids
    
    def _log_violation(self, agent, metabolic_cost: float):
        """
        Log a violation for analysis.
        
        Args:
            agent: Agent that violated constraints
            metabolic_cost: The violating metabolic cost value
        """
        violation_record = {
            'timestamp': time.time(),
            'agent_id': agent.id,
            'metabolic_cost': metabolic_cost,
            'energy_constant': self.energy_constant,
            'excess': metabolic_cost - self.energy_constant,
            'genome_length': agent.genome.get_length(),
            'age': agent.age
        }
        
        self.violation_log.append(violation_record)
    
    def get_statistics(self) -> Dict:
        """
        Get enforcement statistics.
        
        Returns:
            Dictionary with enforcement metrics
        """
        violation_rate = (self.total_violations / self.total_checks) if self.total_checks > 0 else 0.0
        
        return {
            'total_checks': self.total_checks,
            'total_violations': self.total_violations,
            'violation_rate': violation_rate,
            'energy_constant': self.energy_constant,
            'violations_logged': len(self.violation_log)
        }
    
    def get_violation_log(self) -> List[Dict]:
        """
        Get the complete violation log.
        
        Returns:
            List of violation records
        """
        return self.violation_log.copy()
    
    def reset_statistics(self):
        """Reset all statistics and logs."""
        self.total_checks = 0
        self.total_violations = 0
        self.violation_log = []
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        stats = self.get_statistics()
        return (f"PhysicalInvariantGatekeeper("
                f"energy_constant={self.energy_constant:.3f}, "
                f"checks={stats['total_checks']}, "
                f"violations={stats['total_violations']}, "
                f"rate={stats['violation_rate']:.2%})")


if __name__ == '__main__':
    # Demonstration
    print("=" * 70)
    print("PhysicalInvariantGatekeeper Demonstration")
    print("=" * 70)
    print()
    
    # Import dependencies for demo
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from evolvable_genome import EvolvableGenome
    from structurally_evolvable_agent import StructurallyEvolvableAgent
    
    # Create gatekeeper
    gatekeeper = PhysicalInvariantGatekeeper(energy_constant=0.5)
    print(f"Gatekeeper initialized: {gatekeeper}")
    print(f"  Energy constant: {gatekeeper.energy_constant}")
    print()
    
    # Test Case 1: Viable agent (low cost)
    print("Test Case 1: Viable Agent (Low Cost)")
    genome1 = EvolvableGenome(['AAA', 'CAA', 'GAA'])  # 3 genes
    agent1 = StructurallyEvolvableAgent(genome1)
    print(f"  Genome length: {genome1.get_length()} genes")
    print(f"  Metabolic cost: {genome1.metabolic_cost:.3f}")
    print(f"  Viable: {gatekeeper.check_viability(agent1)}")
    print()
    
    # Test Case 2: Non-viable agent (high cost)
    print("Test Case 2: Non-Viable Agent (High Cost)")
    # Create agent with many genes to exceed threshold
    genome2 = EvolvableGenome(['AAA'] * 50)  # 50 genes
    agent2 = StructurallyEvolvableAgent(genome2)
    print(f"  Genome length: {genome2.get_length()} genes")
    print(f"  Metabolic cost: {genome2.metabolic_cost:.3f}")
    print(f"  Viable: {gatekeeper.check_viability(agent2)}")
    print()
    
    # Test Case 3: Edge case (exactly at threshold)
    print("Test Case 3: Edge Case (At Threshold)")
    # Calculate genome length that gives cost ≈ 0.5
    # cost = 0.005 * (length ^ 1.5)
    # 0.5 = 0.005 * (length ^ 1.5)
    # length = (0.5 / 0.005) ^ (1/1.5) ≈ 46.4
    genome3 = EvolvableGenome(['AAA'] * 46)
    agent3 = StructurallyEvolvableAgent(genome3)
    print(f"  Genome length: {genome3.get_length()} genes")
    print(f"  Metabolic cost: {genome3.metabolic_cost:.3f}")
    print(f"  Viable: {gatekeeper.check_viability(agent3)}")
    print()
    
    # Test Case 4: Population enforcement
    print("Test Case 4: Population Enforcement")
    population = [agent1, agent2, agent3]
    print(f"  Initial population: {len(population)} agents")
    
    survivors, terminated = gatekeeper.enforce_population_constraints(population)
    print(f"  Survivors: {len(survivors)} agents")
    print(f"  Terminated: {len(terminated)} agents")
    print()
    
    # Statistics
    print("Gatekeeper Statistics:")
    stats = gatekeeper.get_statistics()
    print(f"  Total checks: {stats['total_checks']}")
    print(f"  Total violations: {stats['total_violations']}")
    print(f"  Violation rate: {stats['violation_rate']:.2%}")
    print()
    
    # Violation log
    if stats['violations_logged'] > 0:
        print("Violation Log:")
        for i, violation in enumerate(gatekeeper.get_violation_log(), 1):
            print(f"  Violation {i}:")
            print(f"    Agent ID: {violation['agent_id']}")
            print(f"    Metabolic cost: {violation['metabolic_cost']:.3f}")
            print(f"    Excess: {violation['excess']:.3f}")
            print(f"    Genome length: {violation['genome_length']} genes")
    
    print()
    print("=" * 70)
    print("PhysicalInvariantGatekeeper Features Verified:")
    print("  - Binary viability checking (alive/dead)")
    print("  - Population-wide constraint enforcement")
    print("  - Violation logging and statistics")
    print("  - Immutable physical constants")
    print("=" * 70)
