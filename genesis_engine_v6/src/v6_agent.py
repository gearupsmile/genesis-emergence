"""
v6_agent.py - V6 Agent with Structurally Constrained Evolution (Max Nodes Cap)
"""

import uuid
import random
from typing import Optional, Dict
from genesis_engine_v3.engine.cppn_genome import CPPNGenome
from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4

class DummyLinkage:
    def get_num_groups(self): return 1
    def create_offspring(self, mr): return self
    def get_expressed_indices(self, *args, **kwargs): return []

class V6Agent(AgentV4):
    """
    Genesis V6 Agent.
    Extends AgentV4 with support for node capacity capping (max_nodes).
    """

    def __init__(self, x: int, y: int, genome: Optional[CPPNGenome] = None,
                 lineage_id: Optional[str] = None, max_nodes: Optional[int] = None):
        super().__init__(x, y, genome=genome, lineage_id=lineage_id)
        self.max_nodes = max_nodes
        self.action_history = []  # List of actions ('S', 'M', 'I')

    def mutate(self):
        """
        Custom mutation function for V6Agent.
        If max_nodes is specified and len(self.genome.nodes) >= max_nodes,
        add_node_mutation() is blocked.
        Connection addition, weight mutation, and activation mutations remain enabled.
        """
        # Invalidate CPPN cached structures
        if hasattr(self.genome, '_in_map'): delattr(self.genome, '_in_map')
        if hasattr(self.genome, '_input_nodes'): delattr(self.genome, '_input_nodes')
        if hasattr(self.genome, '_output_nodes'): delattr(self.genome, '_output_nodes')
        if hasattr(self.genome, '_topo_order'): delattr(self.genome, '_topo_order')
        if hasattr(self.genome, '_eval_tuples'): delattr(self.genome, '_eval_tuples')



        # Node mutation blocked if at or above max_nodes ceiling
        if self.max_nodes is None or len(self.genome.nodes) < self.max_nodes:
            if random.random() < 0.03:
                self.genome.add_node_mutation()

        if random.random() < 0.05:
            self.genome.add_connection_mutation()
        if random.random() < 0.10:
            self.genome.mutate_activation_function()
        if random.random() < 0.80:
            self.genome.mutate_weights()

    def decide_action(self, U_field, V_field, S_field) -> str:
        h, w = U_field.shape
        x, y = int(self.x), int(self.y)

        gu_x = float(U_field[y, (x+1)%w] - U_field[y, (x-1)%w])
        gu_y = float(U_field[(y+1)%h, x] - U_field[(y-1)%h, x])
        gv_x = float(V_field[y, (x+1)%w] - V_field[y, (x-1)%w])
        gv_y = float(V_field[(y+1)%h, x] - V_field[(y-1)%h, x])
        gs_x = float(S_field[y, (x+1)%w] - S_field[y, (x-1)%w])
        gs_y = float(S_field[(y+1)%h, x] - S_field[(y-1)%h, x])

        inputs = (self.x / w, self.y / h, self.energy, gu_x, gu_y, gv_x, gv_y, gs_x, gs_y)
        outputs = self.genome.activate(inputs)

        if isinstance(outputs, dict):
            move_x = outputs.get('move_x', 0.0)
            move_y = outputs.get('move_y', 0.0)
            secrete = outputs.get('secrete', 0.0)
        else:
            move_x, move_y, secrete = outputs[0], outputs[1], outputs[2]

        action = 'I'
        if secrete > 0.5:
            action = 'S'
            self.energy -= 0.05
        else:
            dx = 1 if move_x > 0.3 else (-1 if move_x < -0.3 else 0)
            dy = 1 if move_y > 0.3 else (-1 if move_y < -0.3 else 0)
            if dx != 0 or dy != 0:
                self.x = (self.x + dx) % w
                self.y = (self.y + dy) % h
                action = 'M'
                self.energy -= 0.01
            else:
                self.energy -= 0.01

        return action

    def step(self, substrate) -> str:
        """
        Executes one environment step and records action in action_history.
        """
        action = self.decide_action(substrate.U, substrate.V, substrate.S)
        if action == 'S' and hasattr(substrate, 'deposit_secretion'):
            substrate.deposit_secretion(int(self.x), int(self.y), 0.5)

        self.action_history.append(action)
        if len(self.action_history) > 1000:
            self.action_history.pop(0)
        return action


    def reproduce(self, mutation_rate: float = 0.1) -> 'V6Agent':
        """
        Create offspring with mutated genome while preserving lineage and max_nodes cap.
        """
        child_genome = self.genome.copy()
        child = V6Agent(
            x=self.x,
            y=self.y,
            genome=child_genome,
            lineage_id=self.lineage_id,
            max_nodes=self.max_nodes
        )
        child.mutate()
        child.energy = 1.0
        return child

    def __repr__(self) -> str:
        cap_str = f", max_nodes={self.max_nodes}" if self.max_nodes else ""
        return (f"V6Agent(id={self.id[:8]}..., nodes={len(self.genome.nodes)}, "
                f"conns={len(self.genome.connections)}{cap_str})")
