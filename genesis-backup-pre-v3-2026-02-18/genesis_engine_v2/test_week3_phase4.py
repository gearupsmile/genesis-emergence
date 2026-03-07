"""
Week 3 Phase 4 Validation - FSD with Behavioral Variance Tracking

Comprehensive validation of all Week 3 systems with FSD.
Measures BEHAVIORAL VARIANCE - the PRIMARY Week 3 success metric.

Target: Behavioral variance > 0.08 (16x improvement from 0.005 baseline)
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine
from engine.metrics.behavioral_variance import calculate_behavioral_variance


def run_week3_phase4_validation():
    """
    Run 2,000-generation validation with all Week 3 systems + FSD.
    
    Tracks:
    - Behavioral variance (PRIMARY metric)
    - Innovation count
    - FSD pressure events
    - Resource specialization entropy
    """
    print("=" * 70)
    print("WEEK 3 PHASE 4 VALIDATION - FSD + BEHAVIORAL VARIANCE")
    print("=" * 70)
    print()
    
    # Create engine with ALL Week 3 systems
    engine = GenesisEngine(
        population_size=100,
        mutation_rate=0.3,
        simulation_steps=5
    )
    
    print(f"Systems initialized:")
    print(f"  Population: {len(engine.population)}")
    print(f"  Resource system: {engine.resource_system}")
    print(f"  Spatial environment: {engine.spatial_env}")
    print(f"  Temporal environment: {engine.temporal_env}")
    print(f"  FSD: {engine.fsd}")
    print()
    
    # Track metrics
    variance_history = []
    innovation_history = []
    pressure_history = []
    entropy_history = []
    
    print("Running 2,000 generations...")
    print("Tracking behavioral variance every 100 generations...")
    print()
    
    for gen in range(2000):
        engine.run_cycle()
        
        # Track metrics every 100 gens
        if (gen + 1) % 100 == 0:
            # BEHAVIORAL VARIANCE (PRIMARY METRIC)
            variance = calculate_behavioral_variance(
                engine.population,
                engine.resource_system,
                engine.spatial_env
            )
            variance_history.append((gen + 1, variance))
            
            # Other metrics
            resource_stats = engine.resource_system.get_statistics()
            fsd_stats = engine.fsd.get_statistics()
            
            entropy = resource_stats['specialization_entropy']
            entropy_history.append((gen + 1, entropy))
            
            pressure_active = fsd_stats['pressure_active']
            pressure_history.append((gen + 1, pressure_active))
            
            total_innovations = fsd_stats['total_innovations']
            innovation_history.append((gen + 1, total_innovations))
            
            # Progress report
            pressure_str = "[PRESSURE]" if pressure_active else "          "
            print(f"  Gen {gen+1}: {pressure_str} "
                  f"Variance={variance:.4f}, "
                  f"Entropy={entropy:.3f}, "
                  f"Innovations={total_innovations}, "
                  f"Pop={len(engine.population)}")
            
            # Early feedback at 200 gens
            if gen + 1 == 200:
                print()
                print("  " + "=" * 66)
                print(f"  EARLY FEEDBACK (200 generations):")
                print(f"    Behavioral variance: {variance:.4f}")
                print(f"    Target for success: > 0.08")
                print(f"    Current trajectory: {'ON TRACK' if variance > 0.02 else 'NEEDS IMPROVEMENT'}")
                print("  " + "=" * 66)
                print()
    
    print()
    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    
    final_variance = variance_history[-1][1]
    final_entropy = entropy_history[-1][1]
    final_fsd = engine.fsd.get_statistics()
    
    print(f"\nBehavioral Variance (PRIMARY METRIC):")
    print(f"  Initial: {variance_history[0][1]:.4f}")
    print(f"  Final: {final_variance:.4f}")
    print(f"  Change: {final_variance - variance_history[0][1]:+.4f}")
    print(f"  Target: > 0.08")
    print()
    
    print(f"FSD Performance:")
    print(f"  Stagnation events: {final_fsd['stagnation_events']}")
    print(f"  Pressure applications: {final_fsd['pressure_count']}")
    print(f"  Pressure releases: {final_fsd['pressure_releases']}")
    print(f"  Total innovations: {final_fsd['total_innovations']}")
    print(f"  Resource exploitations: {final_fsd['resource_exploitations']}")
    print(f"  Constraint resolutions: {final_fsd['constraint_resolutions']}")
    print()
    
    print(f"Resource Specialization:")
    print(f"  Final entropy: {final_entropy:.3f}")
    print(f"  Target: > 0.6")
    print()
    
    # SUCCESS CRITERIA
    print("=" * 70)
    print("SUCCESS CRITERIA")
    print("=" * 70)
    
    # C4.1: Baseline variance > 0.02
    c41_pass = variance_history[0][1] > 0.02
    print(f"C4.1: Baseline variance > 0.02")
    print(f"      Actual: {variance_history[0][1]:.4f}")
    print(f"      Result: {'PASS' if c41_pass else 'FAIL'}")
    print()
    
    # C4.2: FSD triggered
    c42_pass = final_fsd['stagnation_events'] >= 1
    print(f"C4.2: FSD triggered at least once")
    print(f"      Actual: {final_fsd['stagnation_events']} events")
    print(f"      Result: {'PASS' if c42_pass else 'FAIL'}")
    print()
    
    # C4.3: Innovations detected
    c43_pass = final_fsd['total_innovations'] > 0
    print(f"C4.3: Innovations detected")
    print(f"      Actual: {final_fsd['total_innovations']} innovations")
    print(f"      Result: {'PASS' if c43_pass else 'FAIL'}")
    print()
    
    # C4.4: Final variance > 0.08 (PRIMARY)
    c44_pass = final_variance > 0.08
    print(f"C4.4: Final behavioral variance > 0.08 (PRIMARY)")
    print(f"      Actual: {final_variance:.4f}")
    print(f"      Result: {'PASS' if c44_pass else 'FAIL'}")
    print()
    
    # C4.5: Population survived
    c45_pass = len(engine.population) > 10
    print(f"C4.5: Population survived")
    print(f"      Actual: {len(engine.population)} agents")
    print(f"      Result: {'PASS' if c45_pass else 'FAIL'}")
    print()
    
    # Overall
    all_pass = c41_pass and c42_pass and c43_pass and c44_pass and c45_pass
    print("=" * 70)
    if all_pass:
        print("[SUCCESS] Week 3 Phase 4 validation complete - all criteria met!")
        print("Ready for 10,000-generation full Week 3 validation")
    elif c44_pass:
        print("[PARTIAL SUCCESS] Primary metric (variance) achieved!")
        print("Some secondary criteria not met - review FSD configuration")
    else:
        print("[NEEDS WORK] Primary variance target not achieved")
        print(f"Current: {final_variance:.4f}, Target: > 0.08")
        print("Consider adjusting environmental pressures or extending run")
    
    return all_pass


if __name__ == '__main__':
    try:
        success = run_week3_phase4_validation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
