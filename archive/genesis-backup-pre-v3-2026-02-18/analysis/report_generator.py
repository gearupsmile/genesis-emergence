"""
Report Generator for Phase 6 Deep Probe Analysis

Produces comprehensive HTML/text report with:
- Executive summary
- All visualizations
- Statistical test results
- Pivot recommendation
- Raw data summary
"""

from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))

from phase6_analyzer import DeepProbeAnalyzer
from visualization import generate_all_plots
from statistics import comprehensive_assessment
from decision_maker import assess_oee_potential, format_decision_report


def generate_phase6_report(run_directory: str, output_file: str = None):
    """
    Generate comprehensive Phase 6 Deep Probe analysis report.
    
    Args:
        run_directory: Path to run directory with checkpoints
        output_file: Optional output file path (default: run_dir/report.txt)
    """
    run_dir = Path(run_directory)
    
    if output_file is None:
        output_file = run_dir / "analysis_report.txt"
    else:
        output_file = Path(output_file)
    
    print("=" * 70)
    print("PHASE 6 DEEP PROBE - COMPREHENSIVE ANALYSIS REPORT")
    print("=" * 70)
    print()
    
    # === STEP 1: Load Data ===
    print("Step 1: Loading data...")
    analyzer = DeepProbeAnalyzer(run_directory)
    data = analyzer.load_and_process()
    print()
    
    # === STEP 2: Generate Visualizations ===
    print("Step 2: Generating visualizations...")
    viz_dir = run_dir / "visualizations"
    generate_all_plots(data, viz_dir)
    print()
    
    # === STEP 3: Statistical Assessment ===
    print("Step 3: Running statistical tests...")
    stats_results = comprehensive_assessment(data)
    print("  Statistical analysis complete")
    print()
    
    # === STEP 4: Pivot Decision ===
    print("Step 4: Making pivot decision...")
    decision = assess_oee_potential(data, stats_results)
    print(f"  Recommendation: {decision['recommendation']}")
    print(f"  Confidence: {decision['confidence_score']}%")
    print()
    
    # === STEP 5: Generate Report ===
    print("Step 5: Writing report...")
    
    with open(output_file, 'w') as f:
        # Header
        f.write("=" * 70 + "\n")
        f.write("PHASE 6 DEEP PROBE - ANALYSIS REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Run Directory: {run_directory}\n")
        f.write("\n")
        
        # === EXECUTIVE SUMMARY ===
        f.write("=" * 70 + "\n")
        f.write("EXECUTIVE SUMMARY\n")
        f.write("=" * 70 + "\n\n")
        
        metadata = data['metadata']
        f.write(f"Total Generations: {metadata['total_generations']:,}\n")
        f.write(f"Final Population: {metadata['final_population']}\n")
        f.write(f"Checkpoints Analyzed: {metadata['num_checkpoints']}\n")
        f.write(f"Data Points: GAC={metadata['gac_points']}, "
                f"EPC={metadata['epc_points']}, NND={metadata['nnd_points']}\n")
        f.write("\n")
        
        # Quick metrics
        if data['gac']:
            gac_start = data['gac'][0]['genome_mean']
            gac_end = data['gac'][-1]['genome_mean']
            gac_change = ((gac_end - gac_start) / gac_start * 100) if gac_start > 0 else 0
            f.write(f"GAC (Genome Length): {gac_start:.1f} -> {gac_end:.1f} ({gac_change:+.1f}%)\n")
        
        if data['epc']:
            epc_start = data['epc'][0]['lz_mean']
            epc_end = data['epc'][-1]['lz_mean']
            epc_change = ((epc_end - epc_start) / epc_start * 100) if epc_start > 0 else 0
            f.write(f"EPC (LZ Complexity): {epc_start:.3f} -> {epc_end:.3f} ({epc_change:+.1f}%)\n")
        
        if data['nnd']:
            nnd_start = data['nnd'][0]['mean_nnd']
            nnd_end = data['nnd'][-1]['mean_nnd']
            nnd_change = ((nnd_end - nnd_start) / nnd_start * 100) if nnd_start > 0 else 0
            f.write(f"NND (Novelty): {nnd_start:.3f} -> {nnd_end:.3f} ({nnd_change:+.1f}%)\n")
        
        f.write("\n")
        
        # === PIVOT DECISION ===
        f.write(format_decision_report(decision))
        f.write("\n\n")
        
        # === STATISTICAL RESULTS ===
        f.write("=" * 70 + "\n")
        f.write("STATISTICAL TEST RESULTS\n")
        f.write("=" * 70 + "\n\n")
        
        # GAC Statistics
        if 'gac' in stats_results:
            f.write("GAC (Genome Architecture Complexity):\n")
            f.write("-" * 40 + "\n")
            
            trend = stats_results['gac']['trend_test']
            f.write(f"  Mann-Kendall Trend: {trend['trend']}\n")
            f.write(f"    p-value: {trend['p_value']:.4f}\n")
            f.write(f"    Kendall's tau: {trend['tau']:.3f}\n")
            
            growth = stats_results['gac']['growth_rate']
            f.write(f"  Growth Rate: {growth['derivative_trend']}\n")
            f.write(f"    Mean derivative: {growth['mean_derivative']:.4f}\n")
            f.write(f"    Mean acceleration: {growth['mean_acceleration']:.6f}\n")
            
            change_pts = stats_results['gac']['change_points']
            if change_pts:
                f.write(f"  Change Points: {change_pts}\n")
            else:
                f.write(f"  Change Points: None detected\n")
            f.write("\n")
        
        # EPC Statistics
        if 'epc' in stats_results:
            f.write("EPC (Expressed Phenotype Complexity):\n")
            f.write("-" * 40 + "\n")
            
            trend = stats_results['epc']['trend_test']
            f.write(f"  Mann-Kendall Trend: {trend['trend']}\n")
            f.write(f"    p-value: {trend['p_value']:.4f}\n")
            f.write(f"    Kendall's tau: {trend['tau']:.3f}\n")
            
            growth = stats_results['epc']['growth_rate']
            f.write(f"  Growth Rate: {growth['derivative_trend']}\n")
            f.write(f"    Mean derivative: {growth['mean_derivative']:.6f}\n")
            f.write("\n")
        
        # NND Statistics
        if 'nnd' in stats_results:
            f.write("NND (Normalized Novelty Distance):\n")
            f.write("-" * 40 + "\n")
            
            sat = stats_results['nnd']['saturation_test']
            f.write(f"  Saturation Test: {'SATURATED' if sat['saturated'] else 'NOT SATURATED'}\n")
            f.write(f"    p-value: {sat['p_value']:.4f}\n")
            f.write(f"    First half mean: {sat['first_half_mean']:.3f}\n")
            f.write(f"    Second half mean: {sat['second_half_mean']:.3f}\n")
            f.write(f"    Percent change: {sat['percent_change']:.1f}%\n")
            
            trend = stats_results['nnd']['trend_test']
            f.write(f"  Mann-Kendall Trend: {trend['trend']}\n")
            f.write(f"    p-value: {trend['p_value']:.4f}\n")
            f.write("\n")
        
        # === VISUALIZATIONS ===
        f.write("=" * 70 + "\n")
        f.write("VISUALIZATIONS\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"All plots saved to: {viz_dir}\n\n")
        f.write("Generated plots:\n")
        f.write("  1. gac_trajectory.png - Genome length over time\n")
        f.write("  2. epc_trajectory.png - Phenotypic complexity over time\n")
        f.write("  3. nnd_distribution.png - Novelty distribution by epoch\n")
        f.write("  4. correlation_heatmap.png - Metric correlations\n")
        f.write("  5. phase_space_3d.png - 3D evolutionary trajectory\n")
        f.write("\n")
        
        # === FOOTER ===
        f.write("=" * 70 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 70 + "\n")
    
    print(f"Report saved to: {output_file}")
    print()
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    
    return {
        'report_file': str(output_file),
        'visualization_dir': str(viz_dir),
        'decision': decision,
        'statistics': stats_results
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python report_generator.py <run_directory>")
        sys.exit(1)
    
    result = generate_phase6_report(sys.argv[1])
    
    print("\nKey Results:")
    print(f"  Recommendation: {result['decision']['recommendation']}")
    print(f"  Confidence: {result['decision']['confidence_score']}%")
    print(f"  Report: {result['report_file']}")
