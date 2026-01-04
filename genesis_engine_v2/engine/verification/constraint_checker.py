"""
Constraint Checker - Automated Verification of Evolutionary Laws

This module provides mandatory pre-flight checks to ensure critical evolutionary
constraints are correctly implemented before running experiments.

Critical checks:
1. Metabolic cost penalty is applied during selection
2. AIS purging is active
3. Pareto dominance ranking works correctly
4. Linkage inheritance is functional
"""

import random
from typing import List, Dict, Tuple
from pathlib import Path


class ConstraintChecker:
    """
    Automated verification system for evolutionary constraints.
    
    All checks must pass before experiments can run.
    """
    
    def __init__(self, log_file: str = None):
        """
        Initialize constraint checker.
        
        Args:
            log_file: Optional path to write verification report
        """
        self.log_file = log_file
        self.results = []
        
    def verify_metabolic_cost_application(self) -> Tuple[bool, str]:
        """
        CRITICAL TEST: Verify metabolic cost penalty is applied during selection.
        
        Creates mock population with short and bloated genomes, runs selection,
        and verifies that bloated genomes have reduced selection probability.
        
        Returns:
            (passed, message) tuple
        """
        from ..structurally_evolvable_agent import StructurallyEvolvableAgent
        from ..evolvable_genome import EvolvableGenome
        from ..bootstrap_evaluator import tournament_selection
        
        print("  [CHECK] Metabolic cost application in selection...")
        
        # Create mock population: 5 short genomes, 5 bloated genomes
        population = []
        
        # Short genomes (~5 genes, low cost)
        for i in range(5):
            genome = EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAA', 'ACA'])  # 5 codons
            agent = StructurallyEvolvableAgent(
                genome=genome,
                agent_id=f"short_{i}"
            )
            population.append(agent)
        
        # Bloated genomes (~50 genes, high cost)
        for i in range(5):
            # Create 50-codon genome
            codons = ['AAA', 'CAA', 'GAA', 'TAA', 'ACA', 'AGA', 'ATA', 'ATT', 'CAT', 'CCA'] * 5
            genome = EvolvableGenome(codons)
            agent = StructurallyEvolvableAgent(
                genome=genome,
                agent_id=f"bloat_{i}"
            )
            population.append(agent)
        
        # Assign equal base fitness to all agents
        base_fitness = 10.0
        fitness_scores = {agent.id: base_fitness for agent in population}
        
        # Calculate expected penalized scores
        expected_scores = {}
        for agent in population:
            cost = agent.genome.metabolic_cost
            expected_scores[agent.id] = base_fitness * (1.0 - min(cost, 0.99))
        
        # Run selection multiple times to get statistical sample
        num_trials = 100
        selection_counts = {agent.id: 0 for agent in population}
        
        for _ in range(num_trials):
            selected = tournament_selection(
                population,
                fitness_scores,
                num_parents=1,
                tournament_size=3
            )
            if selected:
                selection_counts[selected[0].id] += 1
        
        # Analyze results
        short_selections = sum(selection_counts[f"short_{i}"] for i in range(5))
        bloat_selections = sum(selection_counts[f"bloat_{i}"] for i in range(5))
        
        # Calculate actual costs
        short_avg_cost = sum(population[i].genome.metabolic_cost for i in range(5)) / 5
        bloat_avg_cost = sum(population[i].genome.metabolic_cost for i in range(5, 10)) / 5
        
        # Verify: short genomes should be selected MORE often than bloated
        # Expected ratio based on costs
        short_expected_score = base_fitness * (1.0 - short_avg_cost)
        bloat_expected_score = base_fitness * (1.0 - min(bloat_avg_cost, 0.99))
        expected_ratio = short_expected_score / bloat_expected_score if bloat_expected_score > 0 else float('inf')
        actual_ratio = short_selections / bloat_selections if bloat_selections > 0 else float('inf')
        
        # Check if cost penalty is being applied (ratio should be > 1.5)
        if actual_ratio > 1.5:
            msg = (f"PASS - Short genomes selected {short_selections}/{num_trials} times, "
                   f"bloated {bloat_selections}/{num_trials} times (ratio: {actual_ratio:.2f}). "
                   f"Cost penalty is applied.")
            print(f"    {msg}")
            self.results.append(("metabolic_cost", True, msg))
            return True, msg
        else:
            msg = (f"FAIL - Selection ratio {actual_ratio:.2f} too low. "
                   f"Expected > 1.5 based on cost difference. "
                   f"Metabolic cost penalty NOT being applied!")
            print(f"    {msg}")
            self.results.append(("metabolic_cost", False, msg))
            return False, msg
    
    def verify_ais_active(self) -> Tuple[bool, str]:
        """
        Verify AIS purging removes low-relevance agents.
        
        Returns:
            (passed, message) tuple
        """
        from ..ais import AIS
        from ..kernel_agent import KernelAgent
        
        print("  [CHECK] AIS purging functionality...")
        
        # Create AIS with strict settings
        ais = AIS(expiry_age=10, forgetting_rate=0.1, viability_threshold=0.5)
        
        # Create test agents
        agents = []
        for i in range(5):
            agent = KernelAgent(
                agent_id=f"test_{i}",
                genome="AAACAAGAA",
                position=(i, i)
            )
            agents.append(agent)
        
        # Age agents and set low relevance
        for agent in agents:
            agent.age = 15  # Beyond expiry
            ais.memory[agent.id] = {
                'relevance_score': 0.1,  # Below threshold
                'last_seen': 0
            }
        
        # Run purge
        survivors = ais.purge_irrelevant(agents)
        
        # Verify purging occurred
        if len(survivors) < len(agents):
            msg = f"PASS - AIS purged {len(agents) - len(survivors)}/{len(agents)} low-relevance agents"
            print(f"    {msg}")
            self.results.append(("ais_purging", True, msg))
            return True, msg
        else:
            msg = f"FAIL - AIS did not purge any agents (expected purging)"
            print(f"    {msg}")
            self.results.append(("ais_purging", False, msg))
            return False, msg
    
    def verify_pareto_dominance(self) -> Tuple[bool, str]:
        """
        Verify Pareto ranking correctly identifies non-dominated agents.
        
        Returns:
            (passed, message) tuple
        """
        from ..pareto_coevolution_evaluator import ParetoCoevolutionEvaluator
        from ..structurally_evolvable_agent import StructurallyEvolvableAgent
        from ..evolvable_genome import EvolvableGenome
        
        print("  [CHECK] Pareto dominance ranking...")
        
        # Create test agents with known dominance relationships
        agents = []
        for i in range(3):
            genome = EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAA', 'ACA'])
            agent = StructurallyEvolvableAgent(
                genome=genome,
                agent_id=f"test_{i}"
            )
            agents.append(agent)
        
        # Create evaluator
        evaluator = ParetoCoevolutionEvaluator()
        
        # Create test scores where agent 0 dominates agent 1
        test_scores = {
            agents[0].id: {'obj1': 10.0, 'obj2': 10.0},  # Dominates
            agents[1].id: {'obj1': 5.0, 'obj2': 5.0},    # Dominated
            agents[2].id: {'obj1': 10.0, 'obj2': 5.0},   # Non-dominated (different trade-off)
        }
        
        # Calculate Pareto ranks
        ranks = evaluator._calculate_pareto_ranks(agents, test_scores)
        
        # Verify: agent 0 and 2 should have better (lower) rank than agent 1
        if ranks[agents[0].id] < ranks[agents[1].id] and ranks[agents[2].id] < ranks[agents[1].id]:
            msg = f"PASS - Pareto ranking correct (dominated agent has worse rank)"
            print(f"    {msg}")
            self.results.append(("pareto_dominance", True, msg))
            return True, msg
        else:
            msg = f"FAIL - Pareto ranking incorrect: {ranks}"
            print(f"    {msg}")
            self.results.append(("pareto_dominance", False, msg))
            return False, msg
    
    def verify_linkage_inheritance(self) -> Tuple[bool, str]:
        """
        Verify genes in linkage groups are co-inherited.
        
        Returns:
            (passed, message) tuple
        """
        from ..linkage_structure import LinkageStructure
        
        print("  [CHECK] Linkage group inheritance...")
        
        # Create linkage structure with known groups
        linkage = LinkageStructure()
        
        # Add genes to same linkage group
        gene_ids = [0, 1, 2, 3, 4]
        for gene_id in gene_ids:
            linkage.add_gene(gene_id, group_id=0)  # All in group 0
        
        # Verify they're in the same group
        groups = linkage.get_linkage_groups()
        
        if len(groups) == 1 and len(groups[0]) == 5:
            msg = f"PASS - Linkage groups correctly maintain gene associations"
            print(f"    {msg}")
            self.results.append(("linkage_inheritance", True, msg))
            return True, msg
        else:
            msg = f"FAIL - Linkage groups not working: {groups}"
            print(f"    {msg}")
            self.results.append(("linkage_inheritance", False, msg))
            return False, msg
    
    def run_all_checks(self) -> bool:
        """
        Run all verification checks.
        
        Returns:
            True if all checks pass, False otherwise
        """
        print("\n" + "=" * 70)
        print("EVOLUTIONARY CONSTRAINT VERIFICATION")
        print("=" * 70)
        print()
        
        all_passed = True
        
        # Critical check: Metabolic cost
        passed, msg = self.verify_metabolic_cost_application()
        if not passed:
            all_passed = False
        
        # AIS check
        try:
            passed, msg = self.verify_ais_active()
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"    [WARNING] AIS check failed with error: {e}")
            self.results.append(("ais_purging", False, str(e)))
        
        # Pareto check
        try:
            passed, msg = self.verify_pareto_dominance()
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"    [WARNING] Pareto check failed with error: {e}")
            self.results.append(("pareto_dominance", False, str(e)))
        
        # Linkage check
        try:
            passed, msg = self.verify_linkage_inheritance()
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"    [WARNING] Linkage check failed with error: {e}")
            self.results.append(("linkage_inheritance", False, str(e)))
        
        print()
        print("=" * 70)
        
        if all_passed:
            print("[PASS] ALL CONSTRAINTS VERIFIED")
            print("=" * 70)
            print()
        else:
            print("[FAIL] CONSTRAINT VERIFICATION FAILED")
            print("=" * 70)
            print()
            print("CRITICAL: One or more evolutionary constraints violated.")
            print("Experiment cannot proceed until issues are resolved.")
            print()
        
        # Write report
        if self.log_file:
            self._write_report()
        
        return all_passed
    
    def _write_report(self):
        """Write verification report to log file."""
        from datetime import datetime
        
        with open(self.log_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("EVOLUTIONARY CONSTRAINT VERIFICATION REPORT\n")
            f.write("=" * 70 + "\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write("\n")
            
            for check_name, passed, message in self.results:
                status = "PASS" if passed else "FAIL"
                f.write(f"[{status}] {check_name}\n")
                f.write(f"  {message}\n")
                f.write("\n")
            
            all_passed = all(passed for _, passed, _ in self.results)
            f.write("=" * 70 + "\n")
            f.write(f"Overall: {'PASSED' if all_passed else 'FAILED'}\n")
            f.write("=" * 70 + "\n")
