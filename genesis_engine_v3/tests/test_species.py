import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.cppn_genome import CPPNGenome
from engine.structurally_evolvable_agent import AgentV4
from engine.species import assign_species

def test_species_assignment():
    g1 = CPPNGenome()
    in1 = g1.add_input_node('x')
    out1 = g1.add_output_node('move_x')
    g1.add_connection(in1, out1, 1.0)
    
    a1 = AgentV4(0, 0, genome=g1)
    
    g2 = g1.copy()
    a2 = AgentV4(0, 0, genome=g2)
    
    g3 = g1.copy()
    for _ in range(50): g3.add_node_mutation()
    for _ in range(50): g3.add_connection_mutation()
    a3 = AgentV4(0, 0, genome=g3)
    
    population = [a1, a2, a3]
    species_list = assign_species(population, [], compatibility_threshold=2.0)
    
    assert len(species_list) == 2
    assert sum(len(s.members) for s in species_list) == 3
    
    s0 = species_list[0]
    s0.members[0].energy = 1.0
    
    # If using 2 members
    if len(s0.members) > 1:
        s0.members[1].energy = 2.0
        
    s0.update_representative()
    
    print("test_species_assignment passed.")

if __name__ == '__main__':
    test_species_assignment()
