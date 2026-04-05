"""
Quick test to verify quadratic metabolic cost controls genome bloat.

This test runs 2,000 generations and verifies:
1. Genome length stabilizes < 100 genes
2. Performance remains > 5 gen/sec
3. Evolution still occurs (not frozen)
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator
from engine.diagnostics.pnct_metrics import PNCTLogger


def test_bloat_control():
    """Test that quadratic cost prevents genome bloat."""
    print("=" * 70)
    print("GENOME BLOAT CONTROL TEST (2,000 generations)")
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
        gac_interval=200,
        nnd_interval=400,
        translator=translator
    )
    
    print("Running evolution...")
    print(f"{'Gen':>6} {'Pop':>5} {'GAC':>7} {'Cost':>7} {'Time':>8}")
    print("-" * 50)
    
    start_time = time.time()
    last_report = start_time
    
    for gen in range(2000):
        engine.run_cycle()
        pnct_logger.log_metrics(gen + 1, engine.population, engine.internal_evaluator, translator)
        
        if (gen + 1) % 200 == 0:
            current_time = time.time()
            interval_time = current_time - last_report
            last_report = current_time
            
            gac_hist = pnct_logger.get_gac_history()
            if gac_hist:
                gac_mean = gac_hist[-1]['genome_length']['mean']
                # Estimate average metabolic cost
                avg_cost = 0.001 * (gac_mean ** 1.5)
                print(f"{gen+1:6d} {len(engine.population):5d} {gac_mean:7.1f} {avg_cost:7.3f} {interval_time:8.2f}s")
    
    total_time = time.time() - start_time
    gens_per_sec = 2000 / total_time
    
    print("-" * 50)
    print(f"Total time: {total_time:.2f}s ({gens_per_sec:.1f} gen/s)")
    print()
    
    # Verify results
    gac_hist = pnct_logger.get_gac_history()
    final_gac = gac_hist[-1]['genome_length']['mean']
    final_cost = 0.001 * (final_gac ** 1.5)
    
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Final genome length: {final_gac:.1f} genes")
    print(f"Final metabolic cost: {final_cost:.3f}")
    print(f"Performance: {gens_per_sec:.1f} gen/s")
    print()
    
    # Checks
    passed = True
    
    if final_gac < 100:
        print("[PASS] Genome length controlled (< 100 genes)")
    else:
        print(f"[FAIL] Genome bloat detected ({final_gac:.1f} genes)")
        passed = False
    
    if gens_per_sec > 5:
        print(f"[PASS] Performance acceptable ({gens_per_sec:.1f} > 5 gen/s)")
    else:
        print(f"[FAIL] Performance too slow ({gens_per_sec:.1f} < 5 gen/s)")
        passed = False
    
    # Check evolution occurred
    gac_values = [h['genome_length']['mean'] for h in gac_hist]
    if len(set(gac_values)) > 3:
        print("[PASS] Evolution occurred (genome length varied)")
    else:
        print("[FAIL] Evolution frozen (no variation)")
        passed = False
    
    print()
    
    if passed:
        print("=" * 70)
        print("[SUCCESS] QUADRATIC COST WORKS!")
        print("=" * 70)
        print("\nGenome bloat is controlled. Ready for 200k experiment.")
        return 0
    else:
        print("=" * 70)
        print("[FAILED] BLOAT CONTROL INSUFFICIENT")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    exit_code = test_bloat_control()
    sys.exit(exit_code)
