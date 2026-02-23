"""
Feature 3 Verification Script
"""
import sys
import os
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.genesis_engine import GenesisEngine
from engine.behavior.behavioral_tracker import BehavioralTracker

def verify_feature_3():
    print("Initializing Engine...")
    engine = GenesisEngine(population_size=10, mutation_rate=0.1)
    
    # 1. Verify Action Trace Recording
    print("\nRunning 20 generations to gather traces...")
    
    # Run loop
    for gen in range(20):
        engine.run_cycle()
        
    # Check traces
    agents_with_trace = 0
    total_actions = 0
    
    # Check traces for ALL agents tracked (past and present)
    agents_with_trace = 0
    total_actions = 0
    
    # ActionRecorder stores history in agent_histories dict
    recorder = engine.behavioral_tracker.action_recorder
    print(f"Total histories tracked: {len(recorder.agent_histories)}")
    
    for agent_id, history in recorder.agent_histories.items():
        trace_len = len(history.action_trace)
        if trace_len > 0:
            agents_with_trace += 1
            total_actions += trace_len
            # Print a sample trace
            if agents_with_trace == 1:
                trace_str = "".join([code for _, code in history.action_trace])
                print(f"Sample Trace (Agent {agent_id[:8]}): {trace_str}")
    
    print(f"Agents with traces: {agents_with_trace}/{len(recorder.agent_histories)}")
    if agents_with_trace == 0:
        print("FAIL: No action traces recorded")
        return
    print("PASS: Action traces recorded")
    
    # 2. Verify LZ Complexity Calculation
    print("\nCalculating LZ Complexity...")
    complexities = []
    for agent_id in recorder.agent_histories:
        lz = engine.behavioral_tracker.calculate_lz_complexity(agent_id)
        if lz > 0: # Only count non-zero (sufficient length)
            complexities.append(lz)
    
    if len(complexities) > 0:
        avg_lz = np.mean(complexities)
        print(f"Average LZ Complexity (for {len(complexities)} agents): {avg_lz:.4f}")
        print(f"Min LZ: {min(complexities):.4f}, Max LZ: {max(complexities):.4f}")
    else:
        print("No agents had sufficient trace length (>10)")
        avg_lz = 0.0
    
    if avg_lz > 0:
        print("PASS: Non-zero LZ complexity calculated")
    else:
        print("WARNING: LZ complexity is 0.0 (might be too short or repetitive)")
        
    # 3. Test LZ Logic with Synthetic Data
    print("\nTesting LZ Logic with Synthetic Data...")
    tracker = engine.behavioral_tracker
    
    # Repetitive string
    repetitive = "M" * 100
    lz_rep = tracker._lz76_complexity(repetitive)
    norm_rep = lz_rep / 100.0
    print(f"Repetitive ('M'*100) LZ: {lz_rep}, Norm: {norm_rep:.4f}")
    
    # Alternating
    alternating = "MS" * 50
    lz_alt = tracker._lz76_complexity(alternating)
    norm_alt = lz_alt / 100.0
    print(f"Alternating ('MS'*50) LZ: {lz_alt}, Norm: {norm_alt:.4f}")
    
    # Random-ish
    import random
    random_str = "".join(random.choice(['M', 'S', 'I']) for _ in range(100))
    lz_rnd = tracker._lz76_complexity(random_str)
    norm_rnd = lz_rnd / 100.0
    print(f"Random LZ: {lz_rnd}, Norm: {norm_rnd:.4f}")
    
    if lz_rep < lz_rnd:
        print("PASS: Random complexity > Repetitive complexity")
    else:
        print("FAIL: LZ logic might be flawed")

if __name__ == "__main__":
    verify_feature_3()
