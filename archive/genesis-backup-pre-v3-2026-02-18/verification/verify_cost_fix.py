"""
Quick 1000-generation test to verify metabolic cost fix prevents genome bloat.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator
from engine.diagnostics.pnct_metrics import PNCTLogger

def test_bloat_control():
    """Run 1000 generations and verify GAC stays under control."""
    print("="*70)
    print("METABOLIC COST FIX VERIFICATION TEST")
    print("="*70)
    print()
    print("Testing that exponential penalty prevents genome bloat...")
    print("Target: GAC should stay < 50 (ideally < 30)")
    print()
    
    # Initialize engine
    engine = GenesisEngine(
        population_size=50,
        mutation_rate=0.3,
        simulation_steps=10
    )
    
    translator = CodonTranslator()
    pnct_logger = PNCTLogger(
        gac_interval=100,
        nnd_interval=1000,
        translator=translator
    )
    
    print(f"{'Gen':>6} {'Pop':>5} {'GAC':>8} {'EPC':>8} {'Status':>20}")
    print("-"*70)
    
    # Run 1000 generations
    for gen in range(1000):
        engine.run_cycle()
        
        # Log metrics
        pnct_logger.log_metrics(
            gen + 1,
            engine.population,
            engine.internal_evaluator,
            translator
        )
        
        # Report every 100 gens
        if (gen + 1) % 100 == 0:
            gac_hist = pnct_logger.get_gac_history()
            epc_hist = pnct_logger.get_epc_history()
            
            if gac_hist:
                gac_mean = gac_hist[-1]['genome_length']['mean']
                epc_mean = epc_hist[-1]['lz_complexity']['mean'] if epc_hist else 0
                
                # Check for bloat
                if gac_mean > 50:
                    status = "[!] BLOAT DETECTED"
                elif gac_mean > 30:
                    status = "[!] High complexity"
                else:
                    status = "[OK] Healthy"
                
                print(f"{gen+1:6d} {len(engine.population):5d} {gac_mean:8.1f} {epc_mean:8.3f} {status:>20}")
    
    # Final analysis
    print("-"*70)
    print()
    
    gac_hist = pnct_logger.get_gac_history()
    if gac_hist:
        final_gac = gac_hist[-1]['genome_length']['mean']
        initial_gac = gac_hist[0]['genome_length']['mean']
        
        print("RESULTS:")
        print(f"  Initial GAC: {initial_gac:.1f}")
        print(f"  Final GAC: {final_gac:.1f}")
        print(f"  Change: {final_gac - initial_gac:+.1f} ({(final_gac/initial_gac - 1)*100:+.1f}%)")
        print()
        
        if final_gac < 50:
            print("[SUCCESS] Genome bloat is CONTROLLED")
            print("   Metabolic cost penalty is working correctly!")
            return True
        else:
            print("[FAILURE] Genome bloat NOT controlled")
            print("   GAC exceeded 50, penalty may still be too weak")
            return False
    
    return False

if __name__ == "__main__":
    success = test_bloat_control()
    sys.exit(0 if success else 1)
