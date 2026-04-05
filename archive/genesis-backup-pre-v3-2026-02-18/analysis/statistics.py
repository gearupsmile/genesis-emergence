"""
Statistical Assessment Module for Phase 6 Deep Probe Analysis

Implements statistical tests to distinguish bounded equilibrium from open-ended evolution:
- Mann-Kendall trend test (monotonic trends)
- Change point detection (plateau identification)
- NND saturation test (novelty decline)
- Growth rate calculation (derivatives)
"""

import numpy as np
from scipy import stats
from typing import Tuple, List, Dict


def mann_kendall_trend_test(metric_series: np.ndarray) -> Dict:
    """
    Mann-Kendall test for monotonic upward trend.
    
    Args:
        metric_series: Time series of metric values
        
    Returns:
        Dict with 'trend' ('increasing', 'decreasing', 'no trend'), 
        'p_value', and 'tau' (Kendall's tau statistic)
    """
    n = len(metric_series)
    
    if n < 3:
        return {'trend': 'insufficient_data', 'p_value': 1.0, 'tau': 0.0}
    
    # Calculate S statistic
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            s += np.sign(metric_series[j] - metric_series[i])
    
    # Calculate variance
    var_s = n * (n - 1) * (2 * n + 5) / 18
    
    # Calculate Z score
    if s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0
    
    # Two-tailed p-value
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    
    # Kendall's tau
    tau = s / (n * (n - 1) / 2)
    
    # Determine trend
    if p_value < 0.05:
        trend = 'increasing' if s > 0 else 'decreasing'
    else:
        trend = 'no_trend'
    
    return {
        'trend': trend,
        'p_value': p_value,
        'tau': tau,
        'z_score': z
    }


def detect_change_points(metric_series: np.ndarray, min_size: int = 50) -> List[int]:
    """
    Detect change points (plateaus) using simple threshold method.
    
    Simplified version - identifies where derivative drops below threshold.
    
    Args:
        metric_series: Time series of metric values
        min_size: Minimum segment size
        
    Returns:
        List of change point indices
    """
    if len(metric_series) < min_size * 2:
        return []
    
    # Calculate moving average derivative
    window = min(50, len(metric_series) // 10)
    derivatives = np.diff(metric_series)
    
    # Smooth derivatives
    smoothed = np.convolve(derivatives, np.ones(window)/window, mode='valid')
    
    # Find where derivative drops significantly
    threshold = np.std(smoothed) * 0.1
    change_points = []
    
    for i in range(min_size, len(smoothed) - min_size):
        if abs(smoothed[i]) < threshold:
            # Check if this is a sustained plateau
            if np.mean(np.abs(smoothed[i:i+min_size])) < threshold:
                change_points.append(i)
                break  # Only report first major plateau
    
    return change_points


def test_nnd_saturation(nnd_series: np.ndarray) -> Dict:
    """
    Test if NND saturates (decreases) in second half vs first half.
    
    Args:
        nnd_series: Time series of NND values
        
    Returns:
        Dict with 'saturated' (bool), 'p_value', 't_statistic', 
        'first_half_mean', 'second_half_mean'
    """
    n = len(nnd_series)
    
    if n < 10:
        return {
            'saturated': False,
            'p_value': 1.0,
            't_statistic': 0.0,
            'first_half_mean': 0.0,
            'second_half_mean': 0.0
        }
    
    # Split into halves
    mid = n // 2
    first_half = nnd_series[:mid]
    second_half = nnd_series[mid:]
    
    # T-test: is second half significantly lower?
    t_stat, p_value = stats.ttest_ind(first_half, second_half)
    
    first_mean = np.mean(first_half)
    second_mean = np.mean(second_half)
    
    # Saturated if second half is significantly lower (one-tailed test)
    saturated = (second_mean < first_mean) and (p_value / 2 < 0.05)
    
    return {
        'saturated': saturated,
        'p_value': p_value,
        't_statistic': t_stat,
        'first_half_mean': first_mean,
        'second_half_mean': second_mean,
        'percent_change': ((second_mean - first_mean) / first_mean * 100) if first_mean > 0 else 0
    }


def calculate_growth_rate(metric_series: np.ndarray, generations: np.ndarray = None) -> Dict:
    """
    Calculate growth rate (derivative) and acceleration (second derivative).
    
    Args:
        metric_series: Time series of metric values
        generations: Optional generation numbers (for proper scaling)
        
    Returns:
        Dict with 'mean_derivative', 'mean_acceleration', 
        'derivative_trend', 'is_growing'
    """
    if len(metric_series) < 3:
        return {
            'mean_derivative': 0.0,
            'mean_acceleration': 0.0,
            'derivative_trend': 'insufficient_data',
            'is_growing': False
        }
    
    # First derivative
    if generations is not None:
        # Account for non-uniform spacing
        derivatives = np.diff(metric_series) / np.diff(generations)
    else:
        derivatives = np.diff(metric_series)
    
    # Second derivative (acceleration)
    acceleration = np.diff(derivatives)
    
    mean_deriv = np.mean(derivatives)
    mean_accel = np.mean(acceleration)
    
    # Determine trend
    if mean_deriv > 0:
        if mean_accel > 0:
            trend = 'accelerating_growth'
        elif mean_accel < -abs(mean_deriv) * 0.1:
            trend = 'decelerating_growth'
        else:
            trend = 'steady_growth'
    elif mean_deriv < 0:
        trend = 'declining'
    else:
        trend = 'flat'
    
    return {
        'mean_derivative': mean_deriv,
        'mean_acceleration': mean_accel,
        'derivative_trend': trend,
        'is_growing': mean_deriv > 0,
        'derivative_std': np.std(derivatives)
    }


def comprehensive_assessment(data: Dict) -> Dict:
    """
    Run all statistical tests on the data.
    
    Args:
        data: Dict with 'gac', 'epc', 'nnd' time series
        
    Returns:
        Dict with all test results
    """
    results = {}
    
    # GAC analysis
    if data['gac']:
        gac_vals = np.array([d['genome_mean'] for d in data['gac']])
        gac_gens = np.array([d['generation'] for d in data['gac']])
        
        results['gac'] = {
            'trend_test': mann_kendall_trend_test(gac_vals),
            'change_points': detect_change_points(gac_vals),
            'growth_rate': calculate_growth_rate(gac_vals, gac_gens)
        }
    
    # EPC analysis
    if data['epc']:
        epc_lz = np.array([d['lz_mean'] for d in data['epc']])
        epc_gens = np.array([d['generation'] for d in data['epc']])
        
        results['epc'] = {
            'trend_test': mann_kendall_trend_test(epc_lz),
            'change_points': detect_change_points(epc_lz),
            'growth_rate': calculate_growth_rate(epc_lz, epc_gens)
        }
    
    # NND analysis
    if data['nnd']:
        nnd_vals = np.array([d['mean_nnd'] for d in data['nnd']])
        
        results['nnd'] = {
            'saturation_test': test_nnd_saturation(nnd_vals),
            'trend_test': mann_kendall_trend_test(nnd_vals)
        }
    
    return results


if __name__ == '__main__':
    # Test with synthetic data
    print("Testing statistical functions...")
    
    # Test 1: Increasing trend
    increasing = np.linspace(10, 100, 50) + np.random.normal(0, 2, 50)
    result = mann_kendall_trend_test(increasing)
    print(f"\nIncreasing series: {result['trend']} (p={result['p_value']:.4f})")
    
    # Test 2: Plateau detection
    plateau = np.concatenate([np.linspace(10, 50, 30), np.ones(20) * 50])
    change_pts = detect_change_points(plateau)
    print(f"Plateau detected at indices: {change_pts}")
    
    # Test 3: NND saturation
    saturating = np.concatenate([np.random.uniform(5, 10, 25), np.random.uniform(2, 4, 25)])
    sat_result = test_nnd_saturation(saturating)
    print(f"NND saturation: {sat_result['saturated']} (p={sat_result['p_value']:.4f})")
    
    print("\nAll tests complete!")
