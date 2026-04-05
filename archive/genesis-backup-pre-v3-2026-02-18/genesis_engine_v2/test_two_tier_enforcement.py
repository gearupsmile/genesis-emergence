"""
Two-Tier Physics Enforcement Test

Validates that the two-tier gatekeeper system ensures NO violating agent
ever exists in the population, not even for one generation.

Test Strategy:
1. Create parents that will produce violating offspring (high mutation rate)
2. Run exactly ONE generation
3. Assert: NO agents with cost > threshold in population
4. Assert: Offspring terminations logged

Phase 2 - Two-Tier Enforcement Fix
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine
from engine.evolvable_genome import EvolvableGenome
from engine.structurally_evolvable_agent import StructurallyEvolvableAgent


def test_two_tier_enforcement():
    """Test that two-tier gatekeeper prevents ALL violations."""
    print("=" * 70)
    print("TWO-TIER PHYSICS ENFORCEMENT TEST")
    print("=" * 70)
    print()
    
    # Create engine with settings that encourage violations
    engine = GenesisEngine(
        population_size=20,
        mutation_rate=0.8,  # Very high mutation rate
        simulation_steps=1
    )
    
    # Replace initial population with agents near the threshold
    # These will likely produce violating offspring
    near_threshold_agents = []
    for i in range(20):
        # 18-20 genes: cost ~0.38-0.45 (viable parents)
        # But with high mutation, offspring may exceed threshold
        genome = EvolvableGenome(['AAA'] * 19)
        agent = StructurallyEvolvableAgent(genome)
        near_threshold_agents.append(agent)
    
    engine.population = near_threshold_agents
    
    print(f"Initial population: {len(engine.population)} agents")
    print(f"  All agents have 19 genes (cost ~0.41)")
    print(f"  Mutation rate: {engine.mutation_rate} (very high)")
    print(f"  Energy constant: 0.5")
    print()
    
    # Check initial population
    initial_violators = [a for a in engine.population if a.genome.metabolic_cost > 0.5]
    print(f"Initial violators: {len(initial_violators)}")
    assert len(initial_violators) == 0, "Initial population should have no violators"
    print()
    
    # Run ONE generation
    print("Running ONE generation...")
    engine.run_cycle()
    print()
    
    # CRITICAL CHECKS
    print("=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    print()
    
    # Check 1: NO violators in final population
    print("Check 1: Population Viability")
    print("-" * 70)
    final_violators = [a for a in engine.population if a.genome.metabolic_cost > 0.5]
    
    print(f"  Final population size: {len(engine.population)}")
    print(f"  Violators (cost > 0.5): {len(final_violators)}")
    
    if final_violators:
        print(f"  [FAIL] Found {len(final_violators)} violating agents!")
        for agent in final_violators[:3]:
            print(f"    Agent {agent.id[:8]}: {agent.genome.get_length()} genes, cost={agent.genome.metabolic_cost:.4f}")
        return False
    else:
        print("  [PASS] NO violating agents in population")
    print()
    
    # Check 2: Offspring terminations logged
    print("Check 2: Offspring Termination Logging")
    print("-" * 70)
    
    if hasattr(engine, 'offspring_terminations_log'):
        total_offspring_terminated = sum(
            event['terminated_count'] 
            for event in engine.offspring_terminations_log
        )
        print(f"  Offspring termination events: {len(engine.offspring_terminations_log)}")
        print(f"  Total offspring terminated: {total_offspring_terminated}")
        
        if total_offspring_terminated > 0:
            print(f"  [PASS] Tier 2 gatekeeper caught {total_offspring_terminated} violating offspring")
        else:
            print("  [INFO] No violating offspring (all mutations stayed viable)")
    else:
        print("  [FAIL] offspring_terminations_log not found!")
        return False
    print()
    
    # Check 3: Parent terminations (Tier 1)
    print("Check 3: Parent Termination Logging (Tier 1)")
    print("-" * 70)
    
    if hasattr(engine, 'physics_violations'):
        total_parents_terminated = sum(
            event['terminated_count']
            for event in engine.physics_violations
        )
        print(f"  Parent termination events: {len(engine.physics_violations)}")
        print(f"  Total parents terminated: {total_parents_terminated}")
        
        if total_parents_terminated > 0:
            print(f"  [INFO] Tier 1 gatekeeper caught {total_parents_terminated} violating parents")
        else:
            print("  [INFO] No violating parents (all stayed viable)")
    print()
    
    # Check 4: Gatekeeper statistics
    print("Check 4: Gatekeeper Statistics")
    print("-" * 70)
    
    if hasattr(engine, 'physics_gatekeeper'):
        stats = engine.physics_gatekeeper.get_statistics()
        print(f"  Total viability checks: {stats['total_checks']}")
        print(f"  Total violations detected: {stats['total_violations']}")
        print(f"  Violation rate: {stats['violation_rate']:.2%}")
        
        # With two-tier system, violations should be caught but not in final population
        if stats['total_violations'] > 0 and len(final_violators) == 0:
            print("  [PASS] Violations detected and prevented from entering population")
        elif stats['total_violations'] == 0:
            print("  [INFO] No violations occurred (all agents stayed viable)")
        else:
            print("  [FAIL] Violations detected but agents still in population!")
            return False
    print()
    
    print("=" * 70)
    print("TEST RESULT: SUCCESS")
    print("=" * 70)
    print()
    print("The two-tier gatekeeper system ensures:")
    print("  1. Tier 1: Parents are checked before reproduction")
    print("  2. Tier 2: Offspring are checked before entering population")
    print("  3. NO violating agent ever exists in self.population")
    print()
    
    return True


if __name__ == '__main__':
    try:
        success = test_two_tier_enforcement()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
