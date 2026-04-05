"""
Micro-Phase Decision Logic

Analyzes mutation profiling data and recommends next steps based on
GAC/EPC efficiency and mutation operator balance.
"""

from typing import Dict, Tuple


def analyze_micro_phase_results(report: Dict) -> Tuple[str, str, Dict]:
    """
    Analyze micro-phase diagnostic report and make recommendation.
    
    Args:
        report: Diagnostic report from MutationProfiler
        
    Returns:
        (recommendation, rationale, metrics) tuple where:
        - recommendation: One of PROCEED, CALIBRATE_MUTATIONS, EASE_CONSTRAINT
        - rationale: Human-readable explanation
        - metrics: Key metrics that informed the decision
    """
    efficiency = report['efficiency']
    gac_epc_ratio = efficiency['average_gac_epc_ratio']
    junk_dna_pct = efficiency['junk_dna_percentage']
    correlation = report['gac_epc_correlation']
    
    metrics = {
        'gac_epc_ratio': gac_epc_ratio,
        'junk_dna_percentage': junk_dna_pct,
        'gac_epc_correlation': correlation,
        'genes_added': efficiency['total_genes_added'],
        'expressed_genes': efficiency['expressed_genes']
    }
    
    # Decision logic
    
    # Case 1: Too permissive - high junk growth
    if gac_epc_ratio > 5.0 and junk_dna_pct > 30.0:
        recommendation = "CALIBRATE_MUTATIONS"
        rationale = (
            f"GAC/EPC ratio ({gac_epc_ratio:.2f}) is high and {junk_dna_pct:.1f}% "
            f"of genes are unexpressed 'junk DNA'. Mutation operators are too "
            f"permissive, allowing excessive non-functional growth. "
            f"Recommendation: Reduce add_gene probability or implement complexity budget."
        )
    
    # Case 2: Too harsh - stagnation
    elif gac_epc_ratio < 0.5 and efficiency['total_genes_added'] < 100:
        recommendation = "EASE_CONSTRAINT"
        rationale = (
            f"GAC/EPC ratio ({gac_epc_ratio:.2f}) is very low with only "
            f"{efficiency['total_genes_added']} genes added. Selection pressure "
            f"may be too harsh, preventing evolutionary exploration. "
            f"Recommendation: Reduce metabolic cost coefficient or increase mutation rate."
        )
    
    # Case 3: Balanced - proceed
    elif 1.0 <= gac_epc_ratio <= 3.0 and junk_dna_pct < 30.0:
        recommendation = "PROCEED"
        rationale = (
            f"System is balanced. GAC/EPC ratio ({gac_epc_ratio:.2f}) is moderate, "
            f"junk DNA ({junk_dna_pct:.1f}%) is controlled, and "
            f"{efficiency['expressed_genes']}/{efficiency['total_genes_added']} "
            f"added genes are expressed. Ready for parameter optimization and 200k run."
        )
    
    # Case 4: Moderate issues - proceed with caution
    else:
        recommendation = "PROCEED_WITH_MONITORING"
        rationale = (
            f"Metrics are within acceptable ranges but not optimal. "
            f"GAC/EPC ratio: {gac_epc_ratio:.2f}, Junk DNA: {junk_dna_pct:.1f}%. "
            f"Recommend proceeding but monitoring closely during 200k run."
        )
    
    return recommendation, rationale, metrics


def generate_decision_report(report: Dict, output_file: str = None) -> str:
    """
    Generate human-readable decision report.
    
    Args:
        report: Diagnostic report from MutationProfiler
        output_file: Optional file to write report to
        
    Returns:
        Report text
    """
    recommendation, rationale, metrics = analyze_micro_phase_results(report)
    
    report_text = []
    report_text.append("=" * 70)
    report_text.append("MICRO-PHASE DIAGNOSTIC REPORT")
    report_text.append("=" * 70)
    report_text.append("")
    
    # Metrics summary
    report_text.append("KEY METRICS:")
    report_text.append(f"  GAC/EPC Efficiency Ratio: {metrics['gac_epc_ratio']:.2f}")
    report_text.append(f"  Junk DNA Percentage: {metrics['junk_dna_percentage']:.1f}%")
    report_text.append(f"  GAC/EPC Correlation: {metrics['gac_epc_correlation']:.3f}")
    report_text.append(f"  Genes Added: {metrics['genes_added']}")
    report_text.append(f"  Expressed Genes: {metrics['expressed_genes']}")
    report_text.append("")
    
    # Mutation operator activity
    report_text.append("MUTATION OPERATOR ACTIVITY:")
    for op, count in report['mutation_operators'].items():
        report_text.append(f"  {op}: {count}")
    report_text.append("")
    
    # Decision
    report_text.append("=" * 70)
    report_text.append(f"RECOMMENDATION: {recommendation}")
    report_text.append("=" * 70)
    report_text.append("")
    report_text.append(rationale)
    report_text.append("")
    
    # Interpretation guide
    report_text.append("INTERPRETATION GUIDE:")
    report_text.append("  - GAC/EPC Ratio < 1: Tight constraint, slow growth")
    report_text.append("  - GAC/EPC Ratio 1-3: Balanced, healthy evolution")
    report_text.append("  - GAC/EPC Ratio > 5: Excessive junk growth")
    report_text.append("  - Junk DNA < 20%: Excellent")
    report_text.append("  - Junk DNA 20-30%: Acceptable")
    report_text.append("  - Junk DNA > 30%: Problematic")
    report_text.append("")
    
    report_str = "\n".join(report_text)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report_str)
    
    return report_str
