"""
ParetoCoevolutionEvaluator - Emergent Fitness through Pareto Dominance

This module implements multi-dimensional, population-relative fitness evaluation
based on Pareto dominance. Success is defined relationally within the population
rather than by external goals.

Phase 4.1: Emergent Fitness & Co-Evolution
"""

from typing import List, Dict, Tuple


class ParetoCoevolutionEvaluator:
    """
    Evaluator based on Pareto dominance and population-relative distinction.
    
    Key Concepts:
    - Multi-dimensional profiles: Agents described by 6 metrics
    - Pareto dominance: Agent A dominates B if better in ≥1 metric, not worse in any
    - Distinction score: Based on how many agents you dominate vs are dominated by
    - No external goal: Success is relative to population
    """
    
    def calculate_profile(self, agent) -> List[float]:
        """
        Extract multi-dimensional profile from agent.
        
        Args:
            agent: StructurallyEvolvableAgent instance
            
        Returns:
            List of 6 metrics:
            [phenotype_length, genome_length, metabolic_cost, 
             expressed_ratio, linkage_groups, age]
             
        Metrics:
            1. phenotype_length: Number of instructions (if developed)
            2. genome_length: Total number of genes
            3. metabolic_cost: Cumulative cost of genome
            4. expressed_ratio: Fraction of genes expressed
            5. linkage_groups: Number of linkage groups
            6. age: Agent's current age
            
        Example:
            >>> evaluator = ParetoCoevolutionEvaluator()
            >>> profile = evaluator.calculate_profile(agent)
            >>> # [5.0, 10.0, 0.05, 0.5, 8.0, 15.0]
        """
        # 1. Phenotype length
        if agent.phenotype is not None:
            phenotype_length = float(len(agent.phenotype))
        else:
            phenotype_length = 0.0
        
        # 2. Genome length
        genome_length = float(agent.genome.get_length())
        
        # 3. Metabolic cost (invert so lower cost = higher value)
        # Use 1/(1+cost) so it's bounded [0,1] and higher is better
        metabolic_cost_inverse = 1.0 / (1.0 + agent.genome.metabolic_cost)
        
        # 4. Expressed ratio
        if genome_length > 0:
            # Get expressed indices from linkage structure
            expressed_indices = agent.linkage_structure.get_expressed_indices(
                int(genome_length)
            )
            expressed_ratio = float(len(expressed_indices)) / genome_length
        else:
            expressed_ratio = 0.0
        
        # 5. Linkage groups
        linkage_groups = float(agent.linkage_structure.get_num_groups())
        
        # 6. Age
        age = float(agent.age)
        
        return [
            phenotype_length,
            genome_length,
            metabolic_cost_inverse,
            expressed_ratio,
            linkage_groups,
            age
        ]
    
    def _dominates(self, profile_a: List[float], profile_b: List[float]) -> bool:
        """
        Check if profile A Pareto-dominates profile B.
        
        A dominates B if:
        - A is better (≥) in ALL metrics
        - A is strictly better (>) in AT LEAST ONE metric
        
        Args:
            profile_a: First agent's profile
            profile_b: Second agent's profile
            
        Returns:
            True if A dominates B, False otherwise
        """
        better_in_at_least_one = False
        
        for a_val, b_val in zip(profile_a, profile_b):
            if a_val < b_val:
                # A is worse in this metric - cannot dominate
                return False
            if a_val > b_val:
                # A is better in this metric
                better_in_at_least_one = True
        
        return better_in_at_least_one
    
    def get_pareto_dominance(self, profiles: List[Tuple[str, List[float]]]) -> Dict:
        """
        Calculate Pareto dominance relationships for all agents.
        
        Args:
            profiles: List of (agent_id, profile) tuples
            
        Returns:
            Dict mapping agent_id to:
            {
                'domination_count': int,  # How many agents this dominates
                'dominated_count': int,   # How many agents dominate this
                'is_pareto_front': bool   # True if dominated_count == 0
            }
            
        Example:
            >>> profiles = [
            ...     ('agent1', [10, 5, 0.8, 0.5, 3, 10]),
            ...     ('agent2', [5, 3, 0.6, 0.3, 2, 5])
            ... ]
            >>> results = evaluator.get_pareto_dominance(profiles)
            >>> results['agent1']['domination_count']  # agent1 dominates agent2
            1
        """
        results = {}
        
        # Initialize results for each agent
        for agent_id, _ in profiles:
            results[agent_id] = {
                'domination_count': 0,
                'dominated_count': 0,
                'is_pareto_front': False
            }
        
        # Compare all pairs
        for i, (id_a, profile_a) in enumerate(profiles):
            for j, (id_b, profile_b) in enumerate(profiles):
                if i == j:
                    continue
                
                if self._dominates(profile_a, profile_b):
                    # A dominates B
                    results[id_a]['domination_count'] += 1
                    results[id_b]['dominated_count'] += 1
        
        # Mark Pareto front (non-dominated agents)
        for agent_id in results:
            if results[agent_id]['dominated_count'] == 0:
                results[agent_id]['is_pareto_front'] = True
        
        return results
    
    def evaluate_population(self, population: List) -> Dict[str, float]:
        """
        Calculate distinction scores for all agents in population.
        
        Args:
            population: List of StructurallyEvolvableAgent instances
            
        Returns:
            Dict mapping agent.id to distinction_score
            
        Distinction Score Formula:
            distinction_score = (domination_count + 1) / (dominated_count + 1)
            
        - Pareto front agents (dominated_count=0): Highest scores
        - Dominated agents: Lower scores based on domination ratio
        - Rewards dominating many, penalizes being dominated by many
        
        Example:
            >>> evaluator = ParetoCoevolutionEvaluator()
            >>> scores = evaluator.evaluate_population(population)
            >>> # {'agent1': 3.0, 'agent2': 1.5, 'agent3': 0.5}
        """
        # Extract profiles for all agents
        profiles = []
        for agent in population:
            profile = self.calculate_profile(agent)
            profiles.append((agent.id, profile))
        
        # Calculate Pareto dominance relationships
        dominance_results = self.get_pareto_dominance(profiles)
        
        # Calculate distinction scores
        distinction_scores = {}
        for agent_id, results in dominance_results.items():
            domination_count = results['domination_count']
            dominated_count = results['dominated_count']
            
            # Distinction score formula
            distinction_score = (domination_count + 1) / (dominated_count + 1)
            distinction_scores[agent_id] = distinction_score
        
        return distinction_scores
    
    def get_pareto_front(self, population: List) -> List:
        """
        Get the Pareto front (non-dominated agents) from population.
        
        Args:
            population: List of StructurallyEvolvableAgent instances
            
        Returns:
            List of agents on the Pareto front
        """
        # Extract profiles
        profiles = [(agent.id, self.calculate_profile(agent)) for agent in population]
        
        # Get dominance relationships
        dominance_results = self.get_pareto_dominance(profiles)
        
        # Filter to Pareto front
        pareto_front = [
            agent for agent in population
            if dominance_results[agent.id]['is_pareto_front']
        ]
        
        return pareto_front


if __name__ == '__main__':
    # Demonstration
    print("=" * 60)
    print("ParetoCoevolutionEvaluator Demonstration")
    print("=" * 60)
    print()
    
    from .evolvable_genome import EvolvableGenome
    from .linkage_structure import LinkageStructure
    from .structurally_evolvable_agent import StructurallyEvolvableAgent
    from .codon_translator import CodonTranslator
    
    translator = CodonTranslator()
    evaluator = ParetoCoevolutionEvaluator()
    
    # Create agents with different characteristics
    print("Creating diverse population...")
    
    # Agent 1: Large genome, high complexity
    genome1 = EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAA', 'ACA', 'AGA', 'ATA', 'AAC'])
    agent1 = StructurallyEvolvableAgent(genome1)
    agent1.develop(translator)
    agent1.age = 10
    
    # Agent 2: Small genome, low cost
    genome2 = EvolvableGenome(['AAA', 'CAA', 'GAA'])
    agent2 = StructurallyEvolvableAgent(genome2)
    agent2.develop(translator)
    agent2.age = 5
    
    # Agent 3: Medium genome, old age
    genome3 = EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAA', 'ACA'])
    agent3 = StructurallyEvolvableAgent(genome3)
    agent3.develop(translator)
    agent3.age = 20
    
    population = [agent1, agent2, agent3]
    
    # Calculate profiles
    print("\nAgent Profiles:")
    print("  Metrics: [phenotype_len, genome_len, cost_inv, expr_ratio, linkage, age]")
    for i, agent in enumerate(population, 1):
        profile = evaluator.calculate_profile(agent)
        print(f"  Agent {i}: {[f'{v:.2f}' for v in profile]}")
    print()
    
    # Evaluate population
    print("Pareto Dominance Analysis:")
    distinction_scores = evaluator.evaluate_population(population)
    
    for i, agent in enumerate(population, 1):
        score = distinction_scores[agent.id]
        print(f"  Agent {i}: distinction_score = {score:.2f}")
    
    # Get Pareto front
    pareto_front = evaluator.get_pareto_front(population)
    print(f"\nPareto Front: {len(pareto_front)} agent(s)")
    
    print()
    print("=" * 60)
    print("ParetoCoevolutionEvaluator Features Verified:")
    print("  - Multi-dimensional profiling")
    print("  - Pareto dominance calculation")
    print("  - Distinction scoring")
    print("  - Pareto front identification")
    print("=" * 60)
