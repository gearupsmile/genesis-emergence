"""
Metabolic Cost Parameter Sweep

Runs experiments with different cost function parameters to find the optimal
balance between genome complexity (GAC) and functional complexity (EPC).

Optimizes: coefficient and exponent in cost = coefficient * (genes ** exponent)
"""

import sys
from pathlib import Path
import time
import json
from datetime import datetime
import itertools

# Add genesis_engine_v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator
from engine.diagnostics.pnct_metrics import PNCTLogger
from engine.evolvable_genome import EvolvableGenome


# Configuration (embedded to avoid yaml dependency)
CONFIG = {
    'parameters': {
        'coefficients': [0.001, 0.003, 0.005, 0.008, 0.01],
        'exponents': [1.0, 1.3, 1.5, 1.7, 2.0]
    },
    'experiment': {
        'generations': 5000,
        'population_size': 50
    },
    'optimization': {
        'constraints': {
            'min_gac': 10,
            'max_gac': 100,
            'min_epc': 0.3
        }
    },
    'output': {
        'results_dir': 'runs/parameter_sweep',
        'summary_file': 'sweep_summary.json',
        'best_params_file': 'best_parameters.json'
    }
}


def run_single_experiment(coefficient, exponent, generations=5000, population_size=50):
    """
    Run a single experiment with given cost parameters.
    
    Returns:
        Dict with results (final_gac, final_epc, runtime, etc.)
    """
    # Temporarily set the cost parameters
    original_coeff = EvolvableGenome.COST_COEFFICIENT
    original_exp = EvolvableGenome.COST_EXPONENT
    
    EvolvableGenome.COST_COEFFICIENT = coefficient
    EvolvableGenome.COST_EXPONENT = exponent
    
    try:
        # Initialize engine
        engine = GenesisEngine(
            population_size=population_size,
            mutation_rate=0.3,
            simulation_steps=10
        )
        
        translator = CodonTranslator()
        pnct_logger = PNCTLogger(
            gac_interval=500,
            nnd_interval=1000,
            translator=translator
        )
        
        start_time = time.time()
        
        # Run evolution
        for gen in range(generations):
            engine.run_cycle()
            pnct_logger.log_metrics(
                gen + 1,
                engine.population,
                engine.internal_evaluator,
                translator
            )
        
        runtime = time.time() - start_time
        
        # Extract final metrics
        gac_hist = pnct_logger.get_gac_history()
        epc_hist = pnct_logger.get_epc_history()
        
        final_gac_mean = gac_hist[-1]['genome_length']['mean'] if gac_hist else 0
        final_gac_median = gac_hist[-1]['genome_length']['median'] if gac_hist else 0
        final_gac_std = gac_hist[-1]['genome_length'].get('std', 0) if gac_hist else 0
        
        final_epc_mean = epc_hist[-1]['lz_complexity']['mean'] if epc_hist else 0
        final_epc_p90 = epc_hist[-1]['lz_complexity'].get('p90', 0) if epc_hist else 0
        
        # Calculate hypervolume (simplified - area under Pareto front)
        # For each agent, calculate (EPC, 1/GAC) point
        epc_gac_points = []
        for agent in engine.population:
            genome_len = agent.genome.get_length()
            if genome_len > 0:
                # Translate and calculate EPC
                from engine.diagnostics.pnct_metrics import lz_complexity, extract_expressed_phenotype
                phenotype = extract_expressed_phenotype(agent, translator)
                if phenotype:
                    epc = lz_complexity(phenotype)
                    epc_gac_points.append((epc, 1.0 / genome_len))
        
        # Simple hypervolume: sum of (epc * (1/gac))
        hypervolume = sum(epc * inv_gac for epc, inv_gac in epc_gac_points) if epc_gac_points else 0
        
        results = {
            'coefficient': coefficient,
            'exponent': exponent,
            'final_gac_mean': final_gac_mean,
            'final_gac_median': final_gac_median,
            'final_gac_std': final_gac_std,
            'final_epc_mean': final_epc_mean,
            'final_epc_p90': final_epc_p90,
            'hypervolume': hypervolume,
            'runtime': runtime,
            'gens_per_sec': generations / runtime,
            'population_size': len(engine.population)
        }
        
        return results
        
    finally:
        # Restore original parameters
        EvolvableGenome.COST_COEFFICIENT = original_coeff
        EvolvableGenome.COST_EXPONENT = original_exp


def run_parameter_sweep(quick_mode=False):
    """Run full parameter sweep."""
    print("=" * 70)
    print("METABOLIC COST PARAMETER SWEEP")
    print("=" * 70)
    print()
    
    # Use embedded configuration
    config = CONFIG.copy()
    
    if quick_mode:
        print("QUICK VALIDATION MODE: Testing 4 strategic parameter sets")
        print("Goal: Validate current parameters or find better alternative")
        print()
        # Strategic alternatives:
        # 1. Current (0.005, 1.5) - very tight
        # 2. Looser (0.003, 1.3) - less punitive
        # 3. Aggressive (0.005, 1.8) - more punitive for large genomes
        # 4. Low base (0.001, 1.5) - much lower base cost
        config['parameters']['coefficients'] = [0.001, 0.003, 0.005, 0.005]
        config['parameters']['exponents'] = [1.5, 1.3, 1.5, 1.8]
        config['experiment']['generations'] = 1000  # Faster for quick test
    
    coefficients = config['parameters']['coefficients']
    exponents = config['parameters']['exponents']
    generations = config['experiment']['generations']
    population_size = config['experiment']['population_size']
    
    print(f"Testing {len(coefficients)} coefficients × {len(exponents)} exponents")
    print(f"= {len(coefficients) * len(exponents)} total combinations")
    print(f"Each run: {generations:,} generations, population {population_size}")
    print()
    
    # Create output directory
    results_dir = Path(config['output']['results_dir'])
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Run sweep
    all_results = []
    total_combinations = len(coefficients) * len(exponents)
    
    print(f"{'#':>3} {'Coeff':>7} {'Exp':>5} {'GAC':>7} {'EPC':>7} {'HV':>8} {'Time':>8} {'Gen/s':>7}")
    print("-" * 70)
    
    for idx, (coeff, exp) in enumerate(itertools.product(coefficients, exponents), 1):
        print(f"{idx:3d} {coeff:7.4f} {exp:5.2f} ", end='', flush=True)
        
        try:
            results = run_single_experiment(coeff, exp, generations, population_size)
            all_results.append(results)
            
            print(f"{results['final_gac_mean']:7.1f} {results['final_epc_mean']:7.3f} "
                  f"{results['hypervolume']:8.2f} {results['runtime']:8.1f}s "
                  f"{results['gens_per_sec']:7.1f}")
            
        except Exception as e:
            print(f"ERROR: {e}")
            continue
    
    print("-" * 70)
    print(f"Completed {len(all_results)}/{total_combinations} experiments")
    print()
    
    # Analyze results
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print()
    
    # Sort by hypervolume (primary metric)
    sorted_results = sorted(all_results, key=lambda r: r['hypervolume'], reverse=True)
    
    # Filter by constraints
    min_gac = config['optimization']['constraints']['min_gac']
    max_gac = config['optimization']['constraints']['max_gac']
    min_epc = config['optimization']['constraints']['min_epc']
    
    valid_results = [
        r for r in sorted_results
        if min_gac <= r['final_gac_mean'] <= max_gac and r['final_epc_mean'] >= min_epc
    ]
    
    if not valid_results:
        print("WARNING: No results met all constraints!")
        valid_results = sorted_results
    
    # Top 3 parameter sets
    print("TOP 3 PARAMETER SETS:")
    print()
    
    for i, result in enumerate(valid_results[:3], 1):
        print(f"{i}. Coefficient={result['coefficient']:.4f}, Exponent={result['exponent']:.2f}")
        print(f"   GAC: {result['final_gac_mean']:.1f} ± {result['final_gac_std']:.1f}")
        print(f"   EPC: {result['final_epc_mean']:.3f} (p90: {result['final_epc_p90']:.3f})")
        print(f"   Hypervolume: {result['hypervolume']:.2f}")
        print(f"   Performance: {result['gens_per_sec']:.1f} gen/s")
        print()
    
    # Best parameters
    best = valid_results[0]
    
    print("=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    print()
    
    if quick_mode:
        # Quick mode: Compare against current (0.005, 1.5)
        current_params = {'coefficient': 0.005, 'exponent': 1.5}
        
        # Find current in results
        current_result = None
        for r in all_results:
            if r['coefficient'] == current_params['coefficient'] and r['exponent'] == current_params['exponent']:
                current_result = r
                break
        
        if current_result:
            current_epc = current_result['final_epc_mean']
            best_epc = best['final_epc_mean']
            epc_improvement = ((best_epc - current_epc) / current_epc * 100) if current_epc > 0 else 0
            
            current_gac = current_result['final_gac_mean']
            best_gac = best['final_gac_mean']
            gac_change = ((best_gac - current_gac) / current_gac * 100) if current_gac > 0 else 0
            
            print(f"CURRENT PARAMETERS: coefficient={current_params['coefficient']:.4f}, exponent={current_params['exponent']:.2f}")
            print(f"  EPC: {current_epc:.3f}, GAC: {current_gac:.1f}")
            print()
            print(f"BEST PARAMETERS: coefficient={best['coefficient']:.4f}, exponent={best['exponent']:.2f}")
            print(f"  EPC: {best_epc:.3f} ({epc_improvement:+.1f}%), GAC: {best_gac:.1f} ({gac_change:+.1f}%)")
            print()
            
            # Decision logic
            if abs(epc_improvement) < 5 and abs(gac_change) < 20:
                print("DECISION: **KEEP CURRENT**")
                print(f"  Current parameters are optimal. EPC difference is minimal ({epc_improvement:+.1f}%)")
                print("  and genome size is well-controlled.")
            elif epc_improvement >= 20 and gac_change < 100:
                print(f"DECISION: **SWITCH TO ({best['coefficient']:.4f}, {best['exponent']:.2f})**")
                print(f"  Significant EPC improvement ({epc_improvement:+.1f}%) with acceptable GAC change ({gac_change:+.1f}%)")
            elif epc_improvement >= 10:
                print(f"DECISION: **CONSIDER SWITCH TO ({best['coefficient']:.4f}, {best['exponent']:.2f})**")
                print(f"  Moderate EPC improvement ({epc_improvement:+.1f}%), GAC change: {gac_change:+.1f}%")
                print("  Recommend running full sweep for more data.")
            else:
                print("DECISION: **RUN FULL SWEEP**")
                print("  Results are inconclusive. Full 25-combination sweep recommended")
                print("  to find optimal parameters.")
        else:
            print(f"Best parameters: coefficient={best['coefficient']:.4f}, exponent={best['exponent']:.2f}")
            print("  (Current parameters not found in test set)")
    else:
        print(f"Best parameters: coefficient={best['coefficient']:.4f}, exponent={best['exponent']:.2f}")
        print()
        print("Justification:")
        print(f"  - Achieves highest EPC/GAC hypervolume ({best['hypervolume']:.2f})")
        print(f"  - Maintains controlled genome size ({best['final_gac_mean']:.1f} genes)")
        print(f"  - Maximizes functional complexity (EPC={best['final_epc_mean']:.3f})")
        print(f"  - Good performance ({best['gens_per_sec']:.1f} gen/s)")
    print()
    
    # Save results
    summary_file = results_dir / config['output']['summary_file']
    with open(summary_file, 'w') as f:
        json.dump({
            'sweep_config': config,
            'all_results': all_results,
            'top_3': valid_results[:3],
            'best_parameters': {
                'coefficient': best['coefficient'],
                'exponent': best['exponent']
            },
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"Results saved to: {summary_file}")
    
    # Save best parameters
    best_params_file = results_dir / config['output']['best_params_file']
    with open(best_params_file, 'w') as f:
        json.dump({
            'metabolic_cost': {
                'coefficient': best['coefficient'],
                'exponent': best['exponent'],
                'justification': f"Optimized via parameter sweep. Hypervolume: {best['hypervolume']:.2f}"
            }
        }, f, indent=2)
    
    print(f"Best parameters saved to: {best_params_file}")
    print()
    
    return best


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run metabolic cost parameter sweep')
    parser.add_argument('--quick', action='store_true',
                       help='Quick test with 2 coefficients and 2 exponents')
    
    args = parser.parse_args()
    
    best = run_parameter_sweep(quick_mode=args.quick)
    
    print("=" * 70)
    print("NEXT STEP: Update final_deep_probe.yaml with best parameters")
    print("=" * 70)
