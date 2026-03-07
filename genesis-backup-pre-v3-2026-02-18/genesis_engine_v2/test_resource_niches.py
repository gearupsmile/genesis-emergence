"""
Test Resource Niche System - Week 3 Phase 1

Validates that resource niches drive agent specialization.

Expected outcomes:
- Agents develop resource preferences based on genome
- Specialization entropy increases over generations
- Different genome sizes prefer different resources
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine


def test_resource_specialization():
    """Test that agents specialize in different resources over 1,000 generations."""
    print("=" * 70)
    print("RESOURCE NICHE SPECIALIZATION TEST")
    print("=" * 70)
    print()
    
    # Create engine with resource system
    engine = GenesisEngine(
        population_size=30,  # Smaller for faster test
        mutation_rate=0.3,
        simulation_steps=5
    )
    
    print(f"Initial population: {len(engine.population)}")
    print(f"Resource system: {engine.resource_system}")
    print()
    
    # Track specialization over time
    specialization_history = []
    
    print("Running 1,000 generations...")
    for gen in range(1000):
        engine.run_cycle()
        
        # Track specialization every 100 gens
        if (gen + 1) % 100 == 0:
            stats = engine.resource_system.get_statistics()
            entropy = stats['specialization_entropy']
            dist = stats['specialization_distribution']
            
            specialization_history.append(entropy)
            
            print(f"  Gen {gen+1}: "
                  f"Entropy={entropy:.3f}, "
                  f"A:{dist['A']}, B:{dist['B']}, C:{dist['C']}, "
                  f"Pop={len(engine.population)}")
    
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    final_stats = engine.resource_system.get_statistics()
    final_entropy = final_stats['specialization_entropy']
    final_dist = final_stats['specialization_distribution']
    
    print(f"\nFinal specialization entropy: {final_entropy:.3f}")
    print(f"Target: > 0.3 (moderate specialization)")
    print()
    
    print(f"Final distribution:")
    print(f"  Resource A (high-risk): {final_dist['A']} agents")
    print(f"  Resource B (balanced): {final_dist['B']} agents")
    print(f"  Resource C (opportunist): {final_dist['C']} agents")
    print()
    
    # Check if specialization emerged
    if final_entropy > 0.3:
        print("[SUCCESS] Agents show resource specialization")
        
        # Check if all resources are used
        resources_used = sum(1 for count in final_dist.values() if count > 0)
        if resources_used >= 2:
            print(f"[SUCCESS] Multiple resources utilized ({resources_used}/3)")
        else:
            print(f"[WARNING] Only {resources_used}/3 resources utilized")
        
        return True
    else:
        print(f"[FAIL] Insufficient specialization (entropy={final_entropy:.3f} < 0.3)")
        print("Population may be too homogeneous")
        return False


if __name__ == '__main__':
    try:
        success = test_resource_specialization()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
