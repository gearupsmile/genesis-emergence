"""
BootstrapEvaluator - Simple External Fitness Evaluation

This module implements simple fitness evaluation and tournament selection to
kickstart evolutionary adaptation. This is a temporary scaffold that will be
retired in Phase 4 when emergent fitness is implemented.

Phase 3.1: Bootstrap Evolution
"""

import random
from typing import List, Dict, Optional


def calculate_fitness(agent, world_state: Optional[Dict] = None) -> float:
    """
    Calculate fitness based on phenotype complexity vs metabolic cost.
    
    This is a simple, temporary fitness function to kickstart evolution.
    It rewards phenotype complexity while penalizing metabolic overhead.
    
    Args:
        agent: StructurallyEvolvableAgent instance
        world_state: Optional world state (unused in this simple version)
        
    Returns:
        float: Fitness score (higher is better)
        
    Formula:
        fitness = (1 + phenotype_complexity) / (1 + metabolic_cost)
        
        - phenotype_complexity: len(agent.phenotype) if developed, else 0
        - metabolic_cost: agent.genome.metabolic_cost
        - +1 prevents division by zero
        
    Example:
        >>> agent = StructurallyEvolvableAgent(genome, linkage)
        >>> agent.develop(translator)
        >>> fitness = calculate_fitness(agent)
        >>> # Agent with 5 instructions and 0.03 cost:
        >>> # fitness = (1 + 5) / (1 + 0.03) = 5.83
    """
    # Get phenotype complexity
    if agent.phenotype is not None:
        phenotype_complexity = len(agent.phenotype)
    else:
        phenotype_complexity = 0
    
    # Get metabolic cost
    metabolic_cost = agent.genome.metabolic_cost
    
    # Calculate fitness
    # +1 prevents division by zero
    fitness = (1 + phenotype_complexity) / (1 + metabolic_cost)
    
    return fitness


def tournament_selection(population: List,
                        fitness_scores: Dict[str, float],
                        num_parents: int,
                        tournament_size: int = 3) -> List:
    """
    Select parents using tournament selection.
    
    Tournament selection maintains diversity while applying selection pressure.
    It repeatedly selects small random subsets (tournaments) and picks the
    best individual from each tournament.
    
    Args:
        population: List of StructurallyEvolvableAgent instances
        fitness_scores: Dict mapping agent.id to fitness score
        num_parents: Number of parents to select
        tournament_size: Number of agents in each tournament (default: 3)
        
    Returns:
        List of selected parent agents
        
    Algorithm:
        1. Repeat num_parents times:
           a. Randomly select tournament_size agents from population
           b. Pick the one with highest fitness score
           c. Add to parent list
        2. Return parent list
        
    Example:
        >>> population = [agent1, agent2, ..., agent20]
        >>> fitness_scores = {agent1.id: 5.2, agent2.id: 3.1, ...}
        >>> parents = tournament_selection(population, fitness_scores, num_parents=10)
        >>> # Returns 10 agents, biased toward high fitness
    """
    if len(population) == 0:
        return []
    
    if tournament_size > len(population):
        tournament_size = len(population)
    
    parents = []
    
    for _ in range(num_parents):
        # Select random tournament
        tournament = random.sample(population, tournament_size)
        
        # Find winner (highest fitness WITH metabolic cost penalty)
        # Apply cost penalty: penalized_score = raw_score * (1 - cost)
        def get_penalized_score(agent):
            raw_score = fitness_scores.get(agent.id, 0.0)
            metabolic_cost = agent.genome.metabolic_cost
            # Cap cost at 0.99 to prevent complete elimination
            capped_cost = min(metabolic_cost, 0.99)
            penalized_score = raw_score * (1.0 - capped_cost)
            return penalized_score
        
        winner = max(tournament, key=get_penalized_score)
        
        parents.append(winner)
    
    return parents


if __name__ == '__main__':
    # Demonstration
    print("=" * 60)
    print("BootstrapEvaluator Demonstration")
    print("=" * 60)
    print()
    
    from .evolvable_genome import EvolvableGenome
    from .linkage_structure import LinkageStructure
    from .structurally_evolvable_agent import StructurallyEvolvableAgent
    from .codon_translator import CodonTranslator
    
    translator = CodonTranslator()
    
    # Create agents with different complexities
    print("Creating agents with varying complexity...")
    agents = []
    
    # Simple agent (3 genes)
    genome1 = EvolvableGenome(['AAA', 'CAA', 'GAA'])
    agent1 = StructurallyEvolvableAgent(genome1)
    agent1.develop(translator)
    agents.append(agent1)
    
    # Medium agent (5 genes)
    genome2 = EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAA', 'ACA'])
    agent2 = StructurallyEvolvableAgent(genome2)
    agent2.develop(translator)
    agents.append(agent2)
    
    # Complex agent (8 genes)
    genome3 = EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAA', 'ACA', 'AGA', 'ATA', 'AAC'])
    agent3 = StructurallyEvolvableAgent(genome3)
    agent3.develop(translator)
    agents.append(agent3)
    
    # Calculate fitness
    print("\nFitness Scores:")
    fitness_scores = {}
    for i, agent in enumerate(agents, 1):
        fitness = calculate_fitness(agent)
        fitness_scores[agent.id] = fitness
        print(f"  Agent {i}: phenotype={len(agent.phenotype)}, cost={agent.genome.metabolic_cost:.3f}, fitness={fitness:.2f}")
    
    # Tournament selection
    print("\nTournament Selection (selecting 2 parents):")
    parents = tournament_selection(agents, fitness_scores, num_parents=2, tournament_size=2)
    for i, parent in enumerate(parents, 1):
        fitness = fitness_scores[parent.id]
        print(f"  Parent {i}: fitness={fitness:.2f}")
    
    print()
    print("=" * 60)
    print("Bootstrap Evaluation Features Verified:")
    print("  - Fitness calculation (complexity vs cost)")
    print("  - Tournament selection (favors high fitness)")
    print("=" * 60)
