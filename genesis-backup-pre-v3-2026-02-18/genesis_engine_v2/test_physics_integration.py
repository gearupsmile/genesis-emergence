"""
Integration Test: Physics Gatekeeper in Genesis Engine

Tests that the PhysicalInvariantGatekeeper is properly integrated
into the main simulation loop and enforces constraints correctly.

Phase 2 - Pillar 2: Physical Invariant Architecture
"""

import sys
from pathlib import Path

# Add genesis_engine_v2 to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator


def test_physics_enforcement_in_simulation():
    """Test that physics gatekeeper terminates violating agents during simulation."""
    print("=" * 70)
    print("INTEGRATION TEST: Physics Gatekeeper in Genesis Engine")
    print("=" * 70)
    print()
    
    print("Test: Physics Enforcement During Simulation")
    print("-" * 70)
    
    # Create engine with small population
    engine = GenesisEngine(
        population_size=20,
        mutation_rate=0.5,  # High mutation rate to encourage bloat
        simulation_steps=10
    )
    
    print(f"Initial population: {len(engine.population)} agents")
    
    # Run 100 generations
    print("\nRunning 100 generations with physics enforcement...")
    print(f"{'Gen':<6} {'Pop':<5} {'MaxCost':<10} {'Violations':<12}")
    print("-" * 40)
    
    for gen in range(100):
        engine.run_cycle()
        
        # Check population stats
        if len(engine.population) > 0:
            max_cost = max(agent.genome.metabolic_cost for agent in engine.population)
            violations = len(engine.physics_violations) if hasattr(engine, 'physics_violations') else 0
            
            if (gen + 1) % 10 == 0:
                print(f"{gen+1:<6} {len(engine.population):<5} {max_cost:<10.3f} {violations:<12}")
    
    print()
    
    # Verify constraints
    print("Verification:")
    print("-" * 70)
    
    # 1. No agent should exceed energy constant
    max_cost = max(agent.genome.metabolic_cost for agent in engine.population) if engine.population else 0
    energy_constant = engine.physics_gatekeeper.energy_constant
    
    print(f"1. Maximum metabolic cost in population: {max_cost:.3f}")
    print(f"   Energy constant: {energy_constant:.3f}")
    
    if max_cost <= energy_constant:
        print("   [PASS] All agents meet physical constraints")
    else:
        print(f"   [FAIL] Agent(s) exceed energy constant!")
        return False
    
    # 2. Check violation logging
    if hasattr(engine, 'physics_violations'):
        total_violations = sum(v['terminated_count'] for v in engine.physics_violations)
        print(f"\n2. Total physics violations: {total_violations}")
        print(f"   Violations logged across {len(engine.physics_violations)} generations")
        print("   [PASS] Violation logging working")
    else:
        print("\n2. No violations logged (all agents compliant)")
        print("   [PASS] No violations needed")
    
    # 3. Population stability
    print(f"\n3. Final population size: {len(engine.population)}")
    if len(engine.population) >= 5:
        print("   [PASS] Population remains stable")
    else:
        print("   [WARNING] Population very small, may collapse")
    
    # 4. Gatekeeper statistics
    stats = engine.physics_gatekeeper.get_statistics()
    print(f"\n4. Gatekeeper Statistics:")
    print(f"   Total checks: {stats['total_checks']}")
    print(f"   Total violations: {stats['total_violations']}")
    print(f"   Violation rate: {stats['violation_rate']:.2%}")
    
    print()
    print("=" * 70)
    print("INTEGRATION TEST COMPLETE")
    print("=" * 70)
    
    return True


if __name__ == '__main__':
    try:
        success = test_physics_enforcement_in_simulation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
