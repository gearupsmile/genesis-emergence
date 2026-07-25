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

    def step(self, substrate) -> str:
        """
        Executes one environment step and records action in action_history.
        """
        action = super().step(substrate)
        self.action_history.append(action)
        # Keep action history reasonably bounded (last 1000 actions)
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
