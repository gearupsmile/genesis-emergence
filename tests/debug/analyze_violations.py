"""
Violation Log Analysis - Find the Pattern

Analyze the violation logs from the 25k run to understand:
1. Are the same agents being violated repeatedly?
2. What genome lengths are causing violations?
3. Is there a pattern in when violations occur?
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict


def analyze_violation_log(log_file):
    """Analyze a single violation log file."""
    print(f"\nAnalyzing: {log_file.name}")
    print("-" * 70)
    
    with open(log_file, 'r') as f:
        violations = json.load(f)
    
    print(f"Total violation events: {len(violations)}")
    
    # Analyze by generation
    generations = [v['generation'] for v in violations]
    print(f"Generation range: {min(generations)} to {max(generations)}")
    
    # Count terminated agents per event
    total_terminated = sum(v['terminated_count'] for v in violations)
    print(f"Total agents terminated: {total_terminated}")
    
    # Sample a few violations
    print(f"\nSample violations:")
    for i, v in enumerate(violations[:5]):
        print(f"  Event {i+1}: Gen {v['generation']}, {v['terminated_count']} agent(s) terminated")
        if 'terminated_ids' in v:
            print(f"    IDs: {v['terminated_ids'][:2]}")  # Show first 2 IDs
    
    return violations


def main():
    """Main analysis function."""
    print("=" * 70)
    print("VIOLATION LOG ANALYSIS")
    print("=" * 70)
    
    log_dir = Path("runs/25k_physics_v2_validation_20260106_152505/logs")
    
    if not log_dir.exists():
        print(f"ERROR: Log directory not found: {log_dir}")
        return
    
    # Analyze the final violation log
    final_log = log_dir / "violations_025000.json"
    
    if not final_log.exists():
        print(f"ERROR: Final log not found: {final_log}")
        return
    
    violations = analyze_violation_log(final_log)
    
    # Deep analysis
    print("\n" + "=" * 70)
    print("DEEP ANALYSIS")
    print("=" * 70)
    
    # Check if same agents appear multiple times
    all_terminated_ids = []
    for v in violations:
        all_terminated_ids.extend(v['terminated_ids'])
    
    id_counts = Counter(all_terminated_ids)
    repeated_ids = {id: count for id, count in id_counts.items() if count > 1}
    
    print(f"\nAgent ID Analysis:")
    print(f"  Unique agents terminated: {len(id_counts)}")
    print(f"  Total termination events: {len(all_terminated_ids)}")
    print(f"  Agents terminated multiple times: {len(repeated_ids)}")
    
    if repeated_ids:
        print(f"\n  Top 5 most frequently terminated agents:")
        for agent_id, count in sorted(repeated_ids.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {agent_id[:16]}: {count} times")
        
        print("\n  [SMOKING GUN] Agents are being terminated MULTIPLE times!")
        print("  This means they are surviving, reproducing, and being re-terminated.")
        print("  The gatekeeper is NOT preventing reproduction of violating agents.")
    
    # Generation pattern
    print(f"\nGeneration Pattern:")
    gen_counts = Counter(v['generation'] for v in violations)
    
    # Show first 10 generations with violations
    print(f"  First 10 generations with violations:")
    for gen in sorted(gen_counts.keys())[:10]:
        print(f"    Gen {gen}: {gen_counts[gen]} event(s)")
    
    # Check for consecutive violations
    consecutive_gens = []
    sorted_gens = sorted(gen_counts.keys())
    for i in range(len(sorted_gens) - 1):
        if sorted_gens[i+1] == sorted_gens[i] + 1:
            consecutive_gens.append((sorted_gens[i], sorted_gens[i+1]))
    
    if consecutive_gens:
        print(f"\n  Consecutive generation violations: {len(consecutive_gens)} pairs")
        print(f"  Example: Gens {consecutive_gens[0][0]}-{consecutive_gens[0][1]}")


if __name__ == '__main__':
    main()
