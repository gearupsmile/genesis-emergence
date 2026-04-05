class Species:
    def __init__(self, representative_agent, species_id):
        self.id = species_id
        self.representative = representative_agent.genome.copy()
        self.members = [representative_agent]
        self.fitness_history = []
        self.stagnation_counter = 0
        self.age = 0
        
    def update_representative(self):
        """Always keep the fittest (by energy) as the representative."""
        if not self.members:
            return
            
        best_member = max(self.members, key=lambda a: getattr(a, 'energy', 0.0) + getattr(a, 'resource_energy', 0.0))
        self.representative = best_member.genome.copy()
        
    def is_stagnant(self, max_stagnation=15):
        return self.stagnation_counter >= max_stagnation
        
    def get_adjusted_fitness(self, agent):
        # fitness sharing
        fitness = getattr(agent, 'energy', 0.0) + getattr(agent, 'resource_energy', 0.0)
        return fitness / max(1, len(self.members))
        
    def get_total_adjusted_fitness(self):
        return sum(self.get_adjusted_fitness(m) for m in self.members)

def assign_species(population, existing_species, compatibility_threshold=3.0):
    # Clear existing members
    for s in existing_species:
        s.members = []
        
    next_species_id = max([s.id for s in existing_species] + [0]) + 1
    
    for agent in population:
        found = False
        for s in existing_species:
            dist = agent.genome.compatibility_distance(s.representative)
            if dist < compatibility_threshold:
                s.members.append(agent)
                found = True
                break
                
        if not found:
            new_species = Species(agent, next_species_id)
            existing_species.append(new_species)
            next_species_id += 1
            
    # Filter out empty species
    active_species = [s for s in existing_species if len(s.members) > 0]
    return active_species
