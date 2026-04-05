import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.genesis_engine import GenesisEngine

def run_speciation_test():
    engine = GenesisEngine(population_size=100, mutation_rate=0.2, agent_type='cppn', compatibility_threshold=0.3, stagnation_limit=500)
    
    print("Running Speciation Test for 500 generations...")
    try:
        for gen in range(500):
            engine.run_cycle()
            
            # Print basic info
            if (gen+1) % 100 == 0:
                print(f"Gen {gen+1} | Pop: {len(engine.population)} | Species: {len(engine.species_list)}")
            
        print("\nSpeciation Test Complete.")
        
        # Verify species count
        print(f"Final species count: {len(engine.species_list)}")
        assert len(engine.species_list) >= 2, "Expected at least 2 species"
        assert len(engine.population) == 100, "Population collapsed"
        
        print("test_speciation_run.py passed.")
        
    except Exception as e:
        print(f"Crash: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_speciation_test()
