import uuid
from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4

class AgentV6(AgentV4):
    def __init__(self, x: int, y: int, genome=None, lineage_id=None, config=None):
        super().__init__(x, y, genome, lineage_id)
        self.config = config
        self.action_history = ""
        
    def get_metabolic_cost(self):
        """
        Calculates metabolic cost based on config.
        """
        if self.config is None or self.config.baseline_mode or self.config.cost_exponent is None:
            # Baseline V5 calculation
            return len(self.genome.connections) * 0.01
        
        # Experiment 2: Configurable exponent
        num_nodes = len(self.genome.nodes)
        return 0.005 * (num_nodes ** self.config.cost_exponent)

    def step(self, substrate) -> str:
        """
        Overrides V4 step to deduct per-step maintenance cost if enabled.
        """
        # Call base action decision which deducts action energy
        action = super().step(substrate)
        
        self.action_history += action
        
        # Experiment 3: Per-step maintenance cost
        if self.config is not None and self.config.per_step_maintenance_cost:
            self.energy -= self.get_metabolic_cost()
            
        return action
        
    def reproduce(self, mutation_rate=0.1):
        """
        Overrides reproduce to deduct reproduction cost and pass config to offspring.
        """
        child_genome = self.genome.copy()
        child_genome.mutate()
        child = AgentV6(self.x, self.y, genome=child_genome, lineage_id=self.lineage_id, config=self.config)
        child.energy = 1.0
        
        # Deduct reproduction cost from parent
        self.energy -= self.get_metabolic_cost()
        
        return child
