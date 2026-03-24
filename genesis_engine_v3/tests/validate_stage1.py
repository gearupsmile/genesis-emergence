import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.genesis_engine import GenesisEngine

def validate_stage1():
    print("Starting Stage 1 Validation (CPPN AgentV4)...")
    try:
        engine = GenesisEngine(population_size=100, mutation_rate=0.2, agent_type='cppn')
        
        for generation in range(500):
            engine.run_cycle()
            
            if (generation + 1) % 100 == 0:
                pop_size = len(engine.population)
                
                total_nodes = 0
                total_conns = 0
                actions = {'M': 0, 'S': 0, 'I': 0}
                
                for agent in engine.population:
                    total_nodes += len(agent.genome.nodes)
                    total_conns += len(agent.genome.connections)
                    action = agent.decide_action(engine.substrate.U, engine.substrate.V, engine.substrate.S)
                    actions[action] = actions.get(action, 0) + 1
                    
                avg_nodes = total_nodes / pop_size if pop_size > 0 else 0
                avg_conns = total_conns / pop_size if pop_size > 0 else 0
                
                print(f"Gen {generation + 1}: PopSize: {pop_size}, "
                      f"AvgNodes: {avg_nodes:.2f}, AvgConns: {avg_conns:.2f}, "
                      f"Actions: {actions}")
                      
                if pop_size == 0:
                    print("Population went extinct.")
                    break
                    
        print("\nStage 1 Validation complete without crashes.")
    except Exception as e:
        print(f"\nCRASH ENCOUNTERED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    validate_stage1()
