"""
Test Spatial Heterogeneity - Week 3 Phase 2

Validates that spatial regions drive regional specialization.

Expected outcomes:
- Non-uniform distribution across regions
- Regional adaptation (agents cluster in suitable regions)
- Behavioral variance increase due to spatial differentiation
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine


def test_spatial_specialization():
    """Test that agents specialize across regions over 2,000 generations."""
    print("=" * 70)
    print("SPATIAL HETEROGENEITY SPECIALIZATION TEST")
    print("=" * 70)
    print()
    
    # Create engine with spatial system
    engine = GenesisEngine(
        population_size=100,
        mutation_rate=0.3,
        simulation_steps=5
    )
    
    print(f"Initial population: {len(engine.population)}")
    print(f"Spatial environment: {engine.spatial_env}")
    print(f"Resource system: {engine.resource_system}")
    print()
    
    # Track metrics over time
    distribution_history = []
    variance_history = []
    
    print("Running 2,000 generations...")
    for gen in range(2000):
        engine.run_cycle()
        
        # Track metrics every 200 gens
        if (gen + 1) % 200 == 0:
            spatial_stats = engine.spatial_env.get_statistics()
            resource_stats = engine.resource_system.get_statistics()
            
            dist = spatial_stats['distribution']
            uniformity = spatial_stats['uniformity']
            migrations = spatial_stats['migration_count']
            
            distribution_history.append(dist.copy())
            
            print(f"  Gen {gen+1}: "
                  f"Harsh:{dist['Harsh']}, Moderate:{dist['Moderate']}, Permissive:{dist['Permissive']}, "
                  f"Uniformity={uniformity:.3f}, Migrations={migrations}")
    
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    final_spatial = engine.spatial_env.get_statistics()
    final_resource = engine.resource_system.get_statistics()
    
    final_dist = final_spatial['distribution']
    final_uniformity = final_spatial['uniformity']
    final_migrations = final_spatial['migration_count']
    
    print(f"\nFinal spatial distribution:")
    print(f"  Harsh region: {final_dist['Harsh']} agents")
    print(f"  Moderate region: {final_dist['Moderate']} agents")
    print(f"  Permissive region: {final_dist['Permissive']} agents")
    print()
    
    print(f"Uniformity: {final_uniformity:.3f}")
    print(f"Total migrations: {final_migrations}")
    print()
    
    # Check success criteria
    print("SUCCESS CRITERIA:")
    print("-" * 70)
    
    # C2.1: Non-uniform distribution (no region >60%)
    max_region_pct = max(final_dist.values()) / sum(final_dist.values())
    c21_pass = max_region_pct < 0.6
    print(f"C2.1: Non-uniform distribution (max region: {max_region_pct:.1%})")
    print(f"      Target: <60%")
    print(f"      Result: {'PASS' if c21_pass else 'FAIL'}")
    print()
    
    # C2.2: Resource specialization entropy
    resource_entropy = final_resource['specialization_entropy']
    c22_pass = resource_entropy > 0.4
    print(f"C2.2: Resource specialization (entropy: {resource_entropy:.3f})")
    print(f"      Target: >0.4")
    print(f"      Result: {'PASS' if c22_pass else 'FAIL'}")
    print()
    
    # C2.3: Migration occurred
    c23_pass = final_migrations > 0
    print(f"C2.3: Migration mechanics (migrations: {final_migrations})")
    print(f"      Target: >0")
    print(f"      Result: {'PASS' if c23_pass else 'FAIL'}")
    print()
    
    # Overall success
    all_pass = c21_pass and c22_pass and c23_pass
    print("=" * 70)
    if all_pass:
        print("[SUCCESS] Spatial heterogeneity drives regional specialization")
    else:
        print("[PARTIAL] Some criteria not met - may need parameter adjustment")
    
    return all_pass


if __name__ == '__main__':
    try:
        success = test_spatial_specialization()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
