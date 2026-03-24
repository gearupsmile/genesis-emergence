import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.cppn_genome import CPPNGenome

def test_minimal_feedforward():
    genome = CPPNGenome()
    in1 = genome.add_input_node('x')
    in2 = genome.add_input_node('y')
    out1 = genome.add_output_node('move_x', activation='linear')
    out2 = genome.add_output_node('move_y', activation='linear')

    genome.add_connection(in1, out1, 1.0)
    genome.add_connection(in2, out2, -1.0)
    genome.add_connection(in1, out2, 0.5)

    inputs = {'x': 2.0, 'y': 3.0}
    outputs = genome.activate(inputs)

    assert 'move_x' in outputs
    assert 'move_y' in outputs
    print("Outputs:", outputs)

    assert abs(outputs['move_x'] - 2.0) < 1e-6
    assert abs(outputs['move_y'] - (3.0 * -1.0 + 2.0 * 0.5)) < 1e-6
    print("test_minimal_feedforward passed.")

if __name__ == '__main__':
    test_minimal_feedforward()
