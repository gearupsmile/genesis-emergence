"""
Phase 4.3: Complete Genesis Engine Test - "The Genesis Moment"

This script executes the final validation of the Genesis Engine v2:
- 15,000 total generations
- 10,000 generations of transition (external -> internal fitness)
- 5,000 generations of pure endogenous evolution
- Verification of 3 success criteria from blueprint

Success Criteria:
1. Increasing or stable complexity (genome length doesn't collapse)
2. Novel, unpredicted phenomena (emergent behaviors)
3. No stagnant state (ongoing evolutionary activity)
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine


def detect_surprises(statistics, window_size=500):
    """
    Detect novel, unpredicted phenomena in the evolutionary data.
    
    Returns list of "surprise" events with generation and description.
    """
    surprises = []
    
    if len(statistics) < window_size:
        return surprises
    
    # Analyze recent window
    recent = statistics[-window_size:]
    
    # Check for sudden genome length changes
    genome_lengths = [s['avg_genome_length'] for s in recent]
    if len(genome_lengths) > 10:
        recent_avg = sum(genome_lengths[-10:]) / 10
        earlier_avg = sum(genome_lengths[:10]) / 10
        
        if recent_avg > earlier_avg * 2:
            surprises.append({
                'generation': statistics[-1]['generation'],
                'type': 'genome_explosion',
                'description': f'Genome length doubled: {earlier_avg:.1f} -> {recent_avg:.1f}'
            })
        elif recent_avg < earlier_avg * 0.5:
            surprises.append({
                'generation': statistics[-1]['generation'],
                'type': 'genome_collapse',
                'description': f'Genome length halved: {earlier_avg:.1f} -> {recent_avg:.1f}'
            })
    
    # Check for internal score spikes
    if len(recent) > 10:
        internal_scores = [s['avg_internal_score'] for s in recent]
        max_internal = max(internal_scores)
        avg_internal = sum(internal_scores) / len(internal_scores)
        
        if max_internal > avg_internal * 2:
            surprises.append({
                'generation': statistics[-1]['generation'],
                'type': 'internal_score_spike',
                'description': f'Internal score spike: avg={avg_internal:.2f}, max={max_internal:.2f}'
            })
    
    # Check for linkage group changes
    linkage_groups = [s['avg_linkage_groups'] for s in recent]
    if len(linkage_groups) > 10:
        recent_linkage = sum(linkage_groups[-10:]) / 10
        earlier_linkage = sum(linkage_groups[:10]) / 10
        
        if abs(recent_linkage - earlier_linkage) > 10:
            surprises.append({
                'generation': statistics[-1]['generation'],
                'type': 'linkage_reorganization',
                'description': f'Linkage groups shifted: {earlier_linkage:.1f} -> {recent_linkage:.1f}'
            })
    
    return surprises


def analyze_success_criteria(statistics, transition_end=10000, total_gens=15000):
    """
    Analyze the three success criteria from the blueprint.
    
    Returns: (success: bool, report: dict)
    """
    report = {
        'criterion_1_complexity': {'passed': False, 'details': ''},
        'criterion_2_novelty': {'passed': False, 'details': ''},
        'criterion_3_activity': {'passed': False, 'details': ''},
        'overall': False
    }
    
    # Get post-transition data (generations 10000-15000)
    post_transition = [s for s in statistics if s['generation'] >= transition_end]
    
    if len(post_transition) < 1000:
        report['criterion_1_complexity']['details'] = "Insufficient post-transition data"
        return False, report
    
    # Criterion 1: Increasing or stable complexity
    genome_lengths = [s['avg_genome_length'] for s in post_transition]
    
    start_complexity = sum(genome_lengths[:100]) / 100
    end_complexity = sum(genome_lengths[-100:]) / 100
    min_complexity = min(genome_lengths)
    
    # Success if complexity doesn't collapse and shows some activity
    complexity_stable = min_complexity > 1.0  # Not collapsed to trivial
    complexity_viable = end_complexity > start_complexity * 0.5  # Not massive decline
    
    if complexity_stable and complexity_viable:
        report['criterion_1_complexity']['passed'] = True
        report['criterion_1_complexity']['details'] = (
            f"Complexity maintained: start={start_complexity:.1f}, "
            f"end={end_complexity:.1f}, min={min_complexity:.1f}"
        )
    else:
        report['criterion_1_complexity']['details'] = (
            f"Complexity collapsed: start={start_complexity:.1f}, "
            f"end={end_complexity:.1f}, min={min_complexity:.1f}"
        )
    
    # Criterion 2: Novel, unpredicted phenomena
    all_surprises = []
    for i in range(len(statistics) - 500, len(statistics), 500):
        if i > 0:
            surprises = detect_surprises(statistics[:i], window_size=500)
            all_surprises.extend(surprises)
    
    if len(all_surprises) > 0:
        report['criterion_2_novelty']['passed'] = True
        report['criterion_2_novelty']['details'] = (
            f"Detected {len(all_surprises)} novel phenomena: " +
            ", ".join([s['type'] for s in all_surprises[:3]])
        )
    else:
        report['criterion_2_novelty']['details'] = "No significant novel phenomena detected"
    
    # Criterion 3: No stagnant state (ongoing activity)
    # Check variance in metrics over post-transition period
    internal_scores = [s['avg_internal_score'] for s in post_transition]
    genome_variance = sum((x - sum(genome_lengths)/len(genome_lengths))**2 for x in genome_lengths) / len(genome_lengths)
    internal_variance = sum((x - sum(internal_scores)/len(internal_scores))**2 for x in internal_scores) / len(internal_scores)
    
    # Also check population persistence
    pop_sizes = [s['population_size'] for s in post_transition]
    min_pop = min(pop_sizes)
    avg_pop = sum(pop_sizes) / len(pop_sizes)
    
    activity_present = genome_variance > 0.1 or internal_variance > 0.01
    population_viable = min_pop > 10 and avg_pop > 50
    
    if activity_present and population_viable:
        report['criterion_3_activity']['passed'] = True
        report['criterion_3_activity']['details'] = (
            f"Ongoing activity: genome_var={genome_variance:.2f}, "
            f"internal_var={internal_variance:.2f}, min_pop={min_pop}, avg_pop={avg_pop:.0f}"
        )
    else:
        report['criterion_3_activity']['details'] = (
            f"Stagnation detected: genome_var={genome_variance:.2f}, "
            f"internal_var={internal_variance:.2f}, min_pop={min_pop}"
        )
    
    # Overall success
    report['overall'] = (
        report['criterion_1_complexity']['passed'] and
        report['criterion_2_novelty']['passed'] and
        report['criterion_3_activity']['passed']
    )
    
    return report['overall'], report


def run_genesis_moment_test():
    """Execute the Genesis Moment test."""
    print("=" * 70)
    print("PHASE 4.3: COMPLETE GENESIS ENGINE TEST")
    print("The Genesis Moment - 15,000 Generation Evolution")
    print("=" * 70)
    print()
    
    # Test parameters
    population_size = 100
    mutation_rate = 0.1
    transition_start = 0
    transition_total = 10000
    total_generations = 15000
    log_interval = 250
    
    print(f"Test Parameters:")
    print(f"  Population Size: {population_size}")
    print(f"  Mutation Rate: {mutation_rate}")
    print(f"  Transition Period: {transition_start} - {transition_total}")
    print(f"  Total Generations: {total_generations}")
    print(f"  Logging Interval: Every {log_interval} generations")
    print()
    
    print("Evolution Timeline:")
    print(f"  Gen 0-{transition_total}: Transition (external -> internal fitness)")
    print(f"  Gen {transition_total}-{total_generations}: Pure endogenous evolution")
    print()
    
    # Initialize engine
    print("Initializing GenesisEngine...")
    engine = GenesisEngine(
        population_size=population_size,
        mutation_rate=mutation_rate,
        simulation_steps=10,
        transition_start_generation=transition_start,
        transition_total_generations=transition_total
    )
    print(f"  Engine initialized: {engine}")
    print()
    
    # Run evolution
    print("=" * 70)
    print("RUNNING EVOLUTION")
    print("=" * 70)
    print()
    print(f"{'Gen':>6} {'Pop':>5} {'Weight':>7} {'External':>9} {'Internal':>9} {'Final':>7} {'Genome':>7} {'Time (s)':>10}")
    print("-" * 70)
    
    start_time = time.time()
    last_log_time = start_time
    surprises_detected = []
    
    for gen in range(total_generations):
        engine.run_cycle()
        
        # Log every log_interval generations
        if (gen + 1) % log_interval == 0 or gen == 0:
            stats = engine.statistics[-1]
            current_time = time.time()
            elapsed = current_time - last_log_time
            last_log_time = current_time
            
            print(f"{gen + 1:6d} {stats['population_size']:5d} "
                  f"{stats['transition_weight']:7.2f} "
                  f"{stats['avg_external_score']:9.2f} "
                  f"{stats['avg_internal_score']:9.2f} "
                  f"{stats['avg_final_score']:7.2f} "
                  f"{stats['avg_genome_length']:7.1f} "
                  f"{elapsed:10.2f}")
        
        # Detect surprises periodically
        if (gen + 1) % 1000 == 0:
            new_surprises = detect_surprises(engine.statistics, window_size=500)
            if new_surprises:
                for surprise in new_surprises:
                    if surprise not in surprises_detected:
                        surprises_detected.append(surprise)
                        print(f"\n  [SURPRISE] Gen {surprise['generation']}: {surprise['description']}\n")
    
    total_time = time.time() - start_time
    print("-" * 70)
    print(f"Total time: {total_time:.2f} seconds ({total_time/60:.2f} minutes, {total_time/3600:.2f} hours)")
    print()
    
    # Success Analysis
    print("=" * 70)
    print("SUCCESS CRITERIA ANALYSIS")
    print("=" * 70)
    print()
    
    success, report = analyze_success_criteria(
        engine.statistics,
        transition_end=transition_total,
        total_gens=total_generations
    )
    
    print("Criterion 1: Increasing or Stable Complexity")
    print(f"  Status: {'[PASS]' if report['criterion_1_complexity']['passed'] else '[FAIL]'}")
    print(f"  {report['criterion_1_complexity']['details']}")
    print()
    
    print("Criterion 2: Novel, Unpredicted Phenomena")
    print(f"  Status: {'[PASS]' if report['criterion_2_novelty']['passed'] else '[FAIL]'}")
    print(f"  {report['criterion_2_novelty']['details']}")
    if surprises_detected:
        print(f"  Surprise Events:")
        for surprise in surprises_detected[:5]:
            print(f"    - Gen {surprise['generation']}: {surprise['description']}")
    print()
    
    print("Criterion 3: No Stagnant State (Ongoing Activity)")
    print(f"  Status: {'[PASS]' if report['criterion_3_activity']['passed'] else '[FAIL]'}")
    print(f"  {report['criterion_3_activity']['details']}")
    print()
    
    # Final Verdict
    print("=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)
    print()
    
    if success:
        print("[SUCCESS] PHASE 4 SUCCESS!")
        print()
        print("All three success criteria met:")
        print("  1. Complexity maintained in post-transition period")
        print("  2. Novel phenomena emerged during evolution")
        print("  3. Population remains active and viable")
        print()
        print("The Genesis Engine v2 has successfully demonstrated:")
        print("  - Smooth transition from external to emergent fitness")
        print("  - Sustained evolution without external goals")
        print("  - Emergent complexity and novelty")
        print()
        print("GENESIS ENGINE V2 - COMPLETE!")
    else:
        print("[FAILURE] PHASE 4 FAILURE")
        print()
        print("One or more success criteria not met:")
        if not report['criterion_1_complexity']['passed']:
            print("  X Complexity collapsed or declined significantly")
        if not report['criterion_2_novelty']['passed']:
            print("  X No significant novel phenomena detected")
        if not report['criterion_3_activity']['passed']:
            print("  X Population stagnated or became inactive")
        print()
        print("Further investigation and tuning required.")
    
    print()
    print("=" * 70)
    
    return success


if __name__ == '__main__':
    success = run_genesis_moment_test()
    sys.exit(0 if success else 1)
