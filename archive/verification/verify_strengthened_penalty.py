"""
Quick 5k test to verify strengthened penalty (e^-2*cost) prevents bloat.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator
from engine.diagnostics.pnct_metrics import PNCTLogger

def test_strengthened_penalty():
    """Run 5000 generations with strengthened penalty."""
    print("="*70)
    print("STRENGTHENED PENALTY VERIFICATION (e^-2*cost)")
    print("="*70)
    print()
    print("Target: GAC should stay < 40 (ideally < 35)")
    print()
    
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
    
    for gen in range(5000):
        engine.run_cycle()
        pnct_logger.log_metrics(gen + 1, engine.population, engine.internal_evaluator, translator)
        
        if (gen + 1) % 500 == 0:
            gac_hist = pnct_logger.get_gac_history()
            epc_hist = pnct_logger.get_epc_history()
            
            if gac_hist:
                gac_mean = gac_hist[-1]['genome_length']['mean']
                epc_mean = epc_hist[-1]['lz_complexity']['mean'] if epc_hist else 0
                
                if gac_mean > 40:
                    status = "[!] Still too high"
                elif gac_mean > 30:
                    status = "[!] Borderline"
                else:
                    status = "[OK] Healthy"
                
                print(f"{gen+1:6d} {len(engine.population):5d} {gac_mean:8.1f} {epc_mean:8.3f} {status:>20}")
    
    print("-"*70)
    print()
    
    gac_hist = pnct_logger.get_gac_history()
    if gac_hist:
        final_gac = gac_hist[-1]['genome_length']['mean']
        initial_gac = gac_hist[0]['genome_length']['mean']
        max_gac = max(h['genome_length']['mean'] for h in gac_hist)
        
        print(f"Initial GAC: {initial_gac:.1f}")
        print(f"Final GAC: {final_gac:.1f}")
        print(f"Max GAC: {max_gac:.1f}")
        print()
        
        if max_gac < 40:
            print("[SUCCESS] Strengthened penalty is working!")
            print(f"  GAC stayed below 40 (max: {max_gac:.1f})")
            return True
        else:
            print("[FAILURE] Still not strong enough")
            print(f"  GAC reached {max_gac:.1f}")
            return False
    
    return False

if __name__ == "__main__":
    success = test_strengthened_penalty()
    sys.exit(0 if success else 1)
