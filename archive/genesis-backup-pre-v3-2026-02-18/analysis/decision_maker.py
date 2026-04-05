"""
Pivot Decision Algorithm for Phase 6 Deep Probe Analysis

Assesses open-ended evolution potential and makes Phase 7 pivot recommendation.

Decision Criteria:
- PROCEED: GAC/EPC show sustained upward trend (p<0.05) AND NND doesn't saturate (p>0.1)
- REDESIGN: Plateau detected before 100k gens OR NND saturation (p<0.05)
"""

from typing import Dict
import numpy as np


def assess_oee_potential(run_data: Dict, statistical_results: Dict) -> Dict:
    """
    Assess open-ended evolution potential and make pivot recommendation.
    
    Args:
        run_data: Dict with 'gac', 'epc', 'nnd', 'metadata'
        statistical_results: Dict from statistics.comprehensive_assessment()
        
    Returns:
        Dict with:
        - confidence_score: 0-100% likelihood of true OEE
        - recommendation: "PROCEED_TO_PHASE7" or "REDESIGN_ARCHITECTURE"
        - key_evidence: Top 3 data points supporting decision
        - weakness_report: Concerning patterns found
    """
    evidence = []
    weaknesses = []
    confidence_points = 0
    max_confidence = 100
    
    metadata = run_data['metadata']
    total_gens = metadata['total_generations']
    
    # === CRITERION 1: GAC Upward Trend ===
    if 'gac' in statistical_results:
        gac_trend = statistical_results['gac']['trend_test']
        gac_growth = statistical_results['gac']['growth_rate']
        
        if gac_trend['trend'] == 'increasing' and gac_trend['p_value'] < 0.05:
            confidence_points += 30
            evidence.append(f"GAC shows significant upward trend (p={gac_trend['p_value']:.4f}, tau={gac_trend['tau']:.3f})")
        elif gac_trend['trend'] == 'no_trend':
            weaknesses.append(f"GAC shows no significant trend (p={gac_trend['p_value']:.4f})")
        else:
            weaknesses.append(f"GAC is decreasing (p={gac_trend['p_value']:.4f})")
        
        # Check for plateau
        change_points = statistical_results['gac']['change_points']
        if change_points and total_gens >= 100000:
            plateau_gen = change_points[0]
            if plateau_gen < 100000:
                weaknesses.append(f"GAC plateau detected at generation {plateau_gen} (before 100k)")
                confidence_points -= 20
        
        # Check growth rate
        if gac_growth['is_growing']:
            if gac_growth['derivative_trend'] == 'accelerating_growth':
                confidence_points += 10
                evidence.append(f"GAC growth is accelerating ({gac_growth['derivative_trend']})")
            elif gac_growth['derivative_trend'] == 'steady_growth':
                confidence_points += 5
        else:
            weaknesses.append("GAC is not growing")
    
    # === CRITERION 2: EPC Upward Trend ===
    if 'epc' in statistical_results:
        epc_trend = statistical_results['epc']['trend_test']
        epc_growth = statistical_results['epc']['growth_rate']
        
        if epc_trend['trend'] == 'increasing' and epc_trend['p_value'] < 0.05:
            confidence_points += 25
            evidence.append(f"EPC shows significant upward trend (p={epc_trend['p_value']:.4f})")
        elif epc_trend['trend'] == 'no_trend':
            weaknesses.append(f"EPC shows no significant trend (p={epc_trend['p_value']:.4f})")
        
        # Check for plateau
        change_points = statistical_results['epc']['change_points']
        if change_points and total_gens >= 100000:
            plateau_gen = change_points[0]
            if plateau_gen < 100000:
                weaknesses.append(f"EPC plateau detected at generation {plateau_gen}")
                confidence_points -= 15
    
    # === CRITERION 3: NND Non-Saturation ===
    if 'nnd' in statistical_results:
        nnd_sat = statistical_results['nnd']['saturation_test']
        nnd_trend = statistical_results['nnd']['trend_test']
        
        if not nnd_sat['saturated']:
            confidence_points += 25
            evidence.append(f"NND does not saturate (p={nnd_sat['p_value']:.4f}, change={nnd_sat['percent_change']:.1f}%)")
        else:
            weaknesses.append(f"NND saturates in second half (p={nnd_sat['p_value']:.4f}, {nnd_sat['percent_change']:.1f}% decrease)")
            confidence_points -= 25
        
        # Check NND trend
        if nnd_trend['trend'] == 'increasing':
            confidence_points += 10
            evidence.append("NND is increasing (sustained novelty generation)")
        elif nnd_trend['trend'] == 'decreasing':
            weaknesses.append("NND is decreasing over time")
    
    # === CRITERION 4: Run Completeness ===
    if total_gens >= 200000:
        confidence_points += 10
        evidence.append(f"Full 200k-generation run completed")
    elif total_gens >= 100000:
        confidence_points += 5
    else:
        weaknesses.append(f"Run incomplete ({total_gens:,} < 200k generations)")
    
    # === CALCULATE FINAL CONFIDENCE ===
    confidence_score = max(0, min(100, confidence_points))
    
    # === MAKE RECOMMENDATION ===
    # PROCEED if: high confidence (>60%) AND no critical weaknesses
    critical_weaknesses = [
        w for w in weaknesses 
        if 'plateau' in w.lower() or 'saturates' in w.lower()
    ]
    
    if confidence_score >= 60 and len(critical_weaknesses) == 0:
        recommendation = "PROCEED_TO_PHASE7"
    elif confidence_score >= 40 and len(critical_weaknesses) <= 1:
        recommendation = "PROCEED_WITH_CAUTION"
    else:
        recommendation = "REDESIGN_ARCHITECTURE"
    
    # === SELECT TOP 3 EVIDENCE ===
    # Sort evidence by importance (based on keywords)
    def evidence_score(e):
        score = 0
        if 'significant' in e: score += 10
        if 'accelerating' in e: score += 5
        if 'does not saturate' in e: score += 8
        if 'sustained' in e: score += 5
        return score
    
    evidence.sort(key=evidence_score, reverse=True)
    key_evidence = evidence[:3] if len(evidence) >= 3 else evidence
    
    return {
        'confidence_score': confidence_score,
        'recommendation': recommendation,
        'key_evidence': key_evidence,
        'weakness_report': weaknesses,
        'total_generations': total_gens,
        'evidence_count': len(evidence),
        'weakness_count': len(weaknesses)
    }


def format_decision_report(decision: Dict) -> str:
    """Format decision as readable text report."""
    lines = []
    lines.append("=" * 70)
    lines.append("PHASE 6 → PHASE 7 PIVOT DECISION")
    lines.append("=" * 70)
    lines.append("")
    
    lines.append(f"RECOMMENDATION: {decision['recommendation']}")
    lines.append(f"CONFIDENCE SCORE: {decision['confidence_score']}%")
    lines.append("")
    
    lines.append("KEY SUPPORTING EVIDENCE:")
    for i, evidence in enumerate(decision['key_evidence'], 1):
        lines.append(f"  {i}. {evidence}")
    lines.append("")
    
    if decision['weakness_report']:
        lines.append("CONCERNING PATTERNS:")
        for i, weakness in enumerate(decision['weakness_report'], 1):
            lines.append(f"  {i}. {weakness}")
        lines.append("")
    
    lines.append(f"Data Quality: {decision['total_generations']:,} generations analyzed")
    lines.append(f"Evidence: {decision['evidence_count']} positive, {decision['weakness_count']} negative")
    lines.append("")
    
    # Interpretation
    lines.append("INTERPRETATION:")
    if decision['recommendation'] == "PROCEED_TO_PHASE7":
        lines.append("  The system shows strong evidence of open-ended evolution.")
        lines.append("  Complexity metrics are growing, and novelty is sustained.")
        lines.append("  Recommend proceeding to Phase 7 (advanced co-evolution).")
    elif decision['recommendation'] == "PROCEED_WITH_CAUTION":
        lines.append("  The system shows mixed signals.")
        lines.append("  Some positive trends but also concerning patterns.")
        lines.append("  Recommend additional experiments or parameter tuning.")
    else:
        lines.append("  The system shows signs of bounded equilibrium.")
        lines.append("  Complexity plateaus or novelty saturates.")
        lines.append("  Recommend architecture redesign before Phase 7.")
    
    lines.append("=" * 70)
    
    return "\n".join(lines)


if __name__ == '__main__':
    # Test with synthetic decision data
    print("Testing pivot decision algorithm...")
    
    # Simulate positive case
    positive_stats = {
        'gac': {
            'trend_test': {'trend': 'increasing', 'p_value': 0.001, 'tau': 0.75},
            'change_points': [],
            'growth_rate': {'is_growing': True, 'derivative_trend': 'accelerating_growth'}
        },
        'epc': {
            'trend_test': {'trend': 'increasing', 'p_value': 0.01, 'tau': 0.65},
            'change_points': [],
            'growth_rate': {'is_growing': True, 'derivative_trend': 'steady_growth'}
        },
        'nnd': {
            'saturation_test': {'saturated': False, 'p_value': 0.3, 'percent_change': 5.0},
            'trend_test': {'trend': 'increasing', 'p_value': 0.05}
        }
    }
    
    positive_data = {'metadata': {'total_generations': 200000}}
    
    decision = assess_oee_potential(positive_data, positive_stats)
    print(format_decision_report(decision))
