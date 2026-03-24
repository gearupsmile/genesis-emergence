import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.cppn_genome import CPPNGenome

def test_mutations():
    genome = CPPNGenome()
    in1 = genome.add_input_node('x')
    in2 = genome.add_input_node('y')
    out1 = genome.add_output_node('move_x', activation='tanh')

    genome.add_connection(in1, out1, 1.0)
    genome.add_connection(in2, out1, -1.0)

    initial_nodes = len(genome.nodes)
    initial_conns = len(genome.connections)

    # 1. Add node
    assert genome.add_node_mutation() == True
    assert len(genome.nodes) == initial_nodes + 1
    assert len(genome.connections) == initial_conns + 2

    # 2. Add connection
    success = False
    for _ in range(20):
        if genome.add_connection_mutation():
            success = True
            break
    assert success == True
    assert len(genome.connections) == initial_conns + 3

    # 3. Mutate activation
    assert genome.mutate_activation_function() == True

    # 4. Mutate weights
    weights_before = [c.weight for c in genome.connections.values()]
    genome.mutate_weights()
    weights_after = [c.weight for c in genome.connections.values()]
    assert weights_before != weights_after

    # 5. Run loop for 100 mutations
    for _ in range(100):
        genome.mutate()
        # Verify it doesn't crash during activate
        try:
            genome.activate({'x': 1.0, 'y': 0.5})
        except Exception as e:
            assert False, f"Activation crashed after mutation: {e}"

    print("test_mutations passed.")

if __name__ == '__main__':
    test_mutations()
