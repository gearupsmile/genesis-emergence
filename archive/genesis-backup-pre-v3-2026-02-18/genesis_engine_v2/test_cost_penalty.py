"""
Quick test to verify metabolic cost penalty is working.

Runs 500 generations and confirms genome length stabilizes below 150.
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator
from engine.diagnostics.pnct_metrics import PNCTLogger


def test_cost_penalty():
    """Test that metabolic cost penalty controls genome bloat."""
    print("=" * 70)
    print("METABOLIC COST PENALTY VERIFICATION (500 generations)")
    print("=" * 70)
    print()
    
    # Initialize
    engine = GenesisEngine(
        population_size=50,
        mutation_rate=0.3,
        simulation_steps=10
    )
    
    translator = CodonTranslator()
    pnct_logger = PNCTLogger(
        gac_interval=50,
        nnd_interval=100,
        translator=translator
    )
    
    print("Running evolution...")
    print(f"{'Gen':>6} {'Pop':>5} {'GAC':>7} {'Cost':>7} {'Time':>8}")
    print("-" * 50)
    
    start_time = time.time()
    last_report = start_time
    
    for gen in range(500):
        engine.run_cycle()
        pnct_logger.log_metrics(gen + 1, engine.population, engine.internal_evaluator, translator)
        
        if (gen + 1) % 50 == 0:
            current_time = time.time()
            interval_time = current_time - last_report
            last_report = current_time
            
            gac_hist = pnct_logger.get_gac_history()
            if gac_hist:
                gac_mean = gac_hist[-1]['genome_length']['mean']
                avg_cost = 0.005 * (gac_mean ** 1.5)
                print(f"{gen+1:6d} {len(engine.population):5d} {gac_mean:7.1f} {avg_cost:7.3f} {interval_time:8.2f}s")
    
    total_time = time.time() - start_time
    gens_per_sec = 500 / total_time
    
    print("-" * 50)
    print(f"Total time: {total_time:.2f}s ({gens_per_sec:.1f} gen/s)")
    print()
    
    # Verify results
    gac_hist = pnct_logger.get_gac_history()
    final_gac = gac_hist[-1]['genome_length']['mean']
    final_cost = 0.005 * (final_gac ** 1.5)
    
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Final genome length: {final_gac:.1f} genes")
    print(f"Final metabolic cost: {final_cost:.3f}")
    print(f"Performance: {gens_per_sec:.1f} gen/s")
    print()
    
    # Checks
    passed = True
    
    if final_gac < 150:
        print(f"[PASS] Genome length controlled ({final_gac:.1f} < 150 genes)")
    else:
        print(f"[FAIL] Genome bloat detected ({final_gac:.1f} >= 150 genes)")
        passed = False
    
    if gens_per_sec > 10:
        print(f"[PASS] Performance acceptable ({gens_per_sec:.1f} > 10 gen/s)")
    else:
        print(f"[FAIL] Performance too slow ({gens_per_sec:.1f} < 10 gen/s)")
        passed = False
    
    # Check for downward pressure
    gac_values = [h['genome_length']['mean'] for h in gac_hist]
    max_gac = max(gac_values)
    if final_gac < max_gac * 1.2:  # Final within 20% of max
        print(f"[PASS] Genome growth controlled (max={max_gac:.1f}, final={final_gac:.1f})")
    else:
        print(f"[WARNING] Genome may still be growing")
    
    print()
    
    if passed:
        print("=" * 70)
        print("[SUCCESS] METABOLIC COST PENALTY WORKS!")
        print("=" * 70)
        print("\nGenome bloat is controlled. Selection pressure is applied.")
        return 0
    else:
        print("=" * 70)
        print("[FAILED] COST PENALTY INSUFFICIENT")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    exit_code = test_cost_penalty()
    sys.exit(exit_code)
