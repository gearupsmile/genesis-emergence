"""
Multi-Generation Trace - Find the Reproduction Bug

The single-cycle test showed the gatekeeper works correctly.
The bug must be: offspring are created with high cost and survive
until the NEXT generation's gatekeeper check.

This script traces what happens across 3 generations.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine


def trace_multi_generation():
    """Trace violating agents across multiple generations."""
    print("=" * 70)
    print("MULTI-GENERATION TRACE: Reproduction Bug Analysis")
    print("=" * 70)
    print()
    
    # Create engine with normal settings
    engine = GenesisEngine(
        population_size=10,
        mutation_rate=0.5,  # High mutation to encourage bloat
        simulation_steps=1
    )
    
    print(f"Initial population: {len(engine.population)} agents")
    print()
    
    # Run 5 generations with detailed tracking
    for gen in range(5):
        print(f"{'='*70}")
        print(f"GENERATION {gen + 1}")
        print(f"{'='*70}")
        
        # Check population BEFORE cycle
        print(f"\nBEFORE run_cycle():")
        print(f"  Population size: {len(engine.population)}")
        
        violators_before = [a for a in engine.population if a.genome.metabolic_cost > 0.5]
        print(f"  Violators (cost > 0.5): {len(violators_before)}")
        if violators_before:
            for agent in violators_before[:3]:  # Show first 3
                print(f"    Agent {agent.id[:8]}: {agent.genome.get_length()} genes, cost={agent.genome.metabolic_cost:.4f}")
        
        # Run one cycle
        engine.run_cycle()
        
        # Check population AFTER cycle
        print(f"\nAFTER run_cycle():")
        print(f"  Population size: {len(engine.population)}")
        
        violators_after = [a for a in engine.population if a.genome.metabolic_cost > 0.5]
        print(f"  Violators (cost > 0.5): {len(violators_after)}")
        if violators_after:
            for agent in violators_after[:3]:  # Show first 3
                print(f"    Agent {agent.id[:8]}: {agent.genome.get_length()} genes, cost={agent.genome.metabolic_cost:.4f}")
        
        # Check gatekeeper stats
        if hasattr(engine, 'physics_gatekeeper'):
            stats = engine.physics_gatekeeper.get_statistics()
            print(f"\nGatekeeper stats:")
            print(f"  Total checks: {stats['total_checks']}")
            print(f"  Total violations: {stats['total_violations']}")
            print(f"  Violation rate: {stats['violation_rate']:.2%}")
        
        print()
    
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    # Final check
    final_violators = [a for a in engine.population if a.genome.metabolic_cost > 0.5]
    
    if final_violators:
        print(f"\n[BUG CONFIRMED] {len(final_violators)} violating agents survived!")
        print("\nHYPOTHESIS:")
        print("  1. Generation N: Parent with cost < 0.5 is viable")
        print("  2. Reproduction: Offspring created with mutations")
        print("  3. Offspring has cost > 0.5 (due to added genes)")
        print("  4. Population replaced with offspring (including violator)")
        print("  5. Generation N+1: Gatekeeper checks and terminates violator")
        print("  6. BUT: Violator already existed for 1 full generation!")
        print("\nROOT CAUSE: Gatekeeper runs AFTER reproduction, not BEFORE.")
        print("Violating offspring survive for 1 generation before termination.")
        return False
    else:
        print("\n[NO BUG] All agents meet physical constraints")
        return True


if __name__ == '__main__':
    success = trace_multi_generation()
    sys.exit(0 if success else 1)
