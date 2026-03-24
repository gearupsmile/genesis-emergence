import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.cppn_genome import CPPNGenome

def test_crossover():
    parent1 = CPPNGenome()
    in1 = parent1.add_input_node('x')
    out1 = parent1.add_output_node('move_x')
    parent1.add_connection(in1, out1, 1.0)

    parent2 = parent1.copy()

    # Diverge
    parent1.add_node_mutation() # adds node and 2 conns
    parent2.add_connection_mutation()

    child = CPPNGenome.crossover(parent1, parent2)

    # Child should have union of innovations
    expected_innovations = set(parent1.connections.keys()).union(set(parent2.connections.keys()))
    child_innovations = set(child.connections.keys())
    assert child_innovations == expected_innovations

    # Distance check
    dist = parent1.compatibility_distance(parent2)
    assert dist > 0.0

    print("test_crossover passed.")

if __name__ == '__main__':
    test_crossover()
