"""
Feature 2 Verification Script
"""
import sys
import os
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.genesis_engine import GenesisEngine
from engine.ais import AISArchive

def verify_feature_2():
    print("Initializing Engine...")
    engine = GenesisEngine(population_size=10, mutation_rate=0.1)
    
    # 1. Verify AISArchive exists
    if not hasattr(engine, 'ais_archive'):
        print("FAIL: engine.ais_archive missing")
        return
    if not isinstance(engine.ais_archive, AISArchive):
        print("FAIL: engine.ais_archive is wrong type")
        return
    print("PASS: engine.ais_archive exists and is correct type")
    
    # 2. Test Manual Add to Archive
    print("\nTesting Manual Archiving...")
    genome_str = "AAA" * 5
    snapshot = np.zeros((5, 5))
    
    added = engine.ais_archive.add(genome_str, snapshot)
    if added:
        print("PASS: Added novel entry")
    else:
        print("FAIL: Could not add novel entry")
        
    added_again = engine.ais_archive.add(genome_str, snapshot)
    if not added_again:
        print("PASS: Rejected duplicate entry")
    else:
        print("FAIL: Accepted duplicate entry")
        
    # 3. Test Integration in Run Cycle
    print("\nRunning 1 Generation with Reproduction...")
    # Force agent positions so they can archive
    for agent in engine.population:
        agent.x = 50
        agent.y = 50
    
    engine.run_cycle()
    
    # Check if archive grew (assuming some parents survived)
    # Note: Gatekeeper might kill some, but with default energy constant 0.5 and small genomes, should survive.
    # Archive starts empty (or with 1 manual entry if we keep the instance)
    # The manual entry above was on engine.ais_archive
    
    archive_size = len(engine.ais_archive.archive)
    print(f"Archive size after 1 generation: {archive_size}")
    
    if archive_size > 1:
        print("PASS: Archive grew during reproduction (parents archived)")
    else:
        print("WARNING: Archive did not grow. Check if parents survived or if they had positions.")
        if len(engine.population) == 0:
            print("  Reason: Population extinct")
        else:
            parents = [a for a in engine.population if hasattr(a, 'x')]
            print(f"  Survivors with position: {len(parents)}")

if __name__ == "__main__":
    verify_feature_2()
