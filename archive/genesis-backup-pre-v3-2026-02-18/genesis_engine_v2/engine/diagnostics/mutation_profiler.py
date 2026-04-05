"""
Mutation Profiler - Diagnostic Module for Mutation Operator Analysis

Tracks mutation events and analyzes the balance between genome growth (GAC)
and functional innovation (EPC) to identify "junk DNA" accumulation.
"""

from typing import Dict, List, Tuple
from collections import defaultdict
import json


class MutationProfiler:
    """
    Profiles mutation operator activity and GAC/EPC efficiency.
    
    Tracks:
    - Mutation operator frequency (add_gene, remove_gene, point_mutation, etc.)
    - GAC/EPC efficiency ratio (genome growth vs functional complexity)
    - Expressed vs unexpressed genes
    - Linkage dynamics
    """
    
    def __init__(self):
        """Initialize mutation profiler."""
        self.mutation_counts = defaultdict(int)
        self.gac_history = []
        self.epc_history = []
        self.efficiency_ratios = []
        
        # Track added genes
        self.added_genes = []  # List of (generation, agent_id, codon, expressed)
        self.gene_expression_tracking = {}  # gene_id -> (added_gen, expressed_gen or None)
        
        # Linkage dynamics
        self.linkage_events = []  # List of (generation, event_type, details)
        
    def log_mutation_event(self, generation: int, agent_id: str, 
                          mutation_type: str, details: Dict = None):
        """
        Log a mutation event.
        
        Args:
            generation: Current generation
            agent_id: ID of agent being mutated
            mutation_type: Type of mutation (add_gene, remove_gene, point_mutation, etc.)
            details: Additional details about the mutation
        """
        self.mutation_counts[mutation_type] += 1
        
        # Track gene additions specifically
        if mutation_type == 'add_gene' and details:
            codon = details.get('codon', '')
            expressed = details.get('expressed', False)
            unique = details.get('unique', False)
            
            gene_id = f"{agent_id}_{generation}_{len(self.added_genes)}"
            self.added_genes.append({
                'generation': generation,
                'agent_id': agent_id,
                'gene_id': gene_id,
                'codon': codon,
                'expressed': expressed,
                'unique': unique
            })
            
            self.gene_expression_tracking[gene_id] = {
                'added_gen': generation,
                'expressed_gen': generation if expressed else None
            }
    
    def log_gac_epc(self, generation: int, gac_mean: float, epc_mean: float):
        """
        Log GAC and EPC values for efficiency calculation.
        
        Args:
            generation: Current generation
            gac_mean: Mean genome architecture complexity (genome length)
            epc_mean: Mean expressed phenotype complexity (LZ complexity)
        """
        self.gac_history.append({'generation': generation, 'value': gac_mean})
        self.epc_history.append({'generation': generation, 'value': epc_mean})
        
        # Calculate efficiency ratio if we have previous data
        if len(self.gac_history) > 1 and len(self.epc_history) > 1:
            delta_gac = gac_mean - self.gac_history[-2]['value']
            delta_epc = epc_mean - self.epc_history[-2]['value']
            
            # Avoid division by zero
            if abs(delta_epc) > 0.001:
                ratio = abs(delta_gac) / abs(delta_epc)
            else:
                ratio = float('inf') if abs(delta_gac) > 0.001 else 0.0
            
            self.efficiency_ratios.append({
                'generation': generation,
                'ratio': ratio,
                'delta_gac': delta_gac,
                'delta_epc': delta_epc
            })
    
    def log_linkage_event(self, generation: int, event_type: str, details: Dict):
        """
        Log linkage structure changes.
        
        Args:
            generation: Current generation
            event_type: Type of event (merge, split, new_group)
            details: Event details
        """
        self.linkage_events.append({
            'generation': generation,
            'event_type': event_type,
            'details': details
        })
    
    def calculate_junk_dna_percentage(self, lookback_generations: int = 100) -> float:
        """
        Calculate percentage of added genes that remain unexpressed.
        
        Args:
            lookback_generations: How far back to look
            
        Returns:
            Percentage of unexpressed genes (0-100)
        """
        if not self.added_genes:
            return 0.0
        
        current_gen = self.gac_history[-1]['generation'] if self.gac_history else 0
        cutoff_gen = current_gen - lookback_generations
        
        # Count genes added before cutoff
        old_genes = [g for g in self.added_genes if g['generation'] <= cutoff_gen]
        
        if not old_genes:
            return 0.0
        
        # Count how many are still unexpressed
        unexpressed = sum(1 for g in old_genes if not g['expressed'])
        
        return (unexpressed / len(old_genes)) * 100.0
    
    def get_operator_activity_summary(self) -> Dict[str, int]:
        """
        Get summary of mutation operator activity.
        
        Returns:
            Dict mapping operator name to count
        """
        return dict(self.mutation_counts)
    
    def get_average_efficiency_ratio(self) -> float:
        """
        Get average GAC/EPC efficiency ratio.
        
        Returns:
            Average ratio (higher = more junk growth)
        """
        if not self.efficiency_ratios:
            return 0.0
        
        # Filter out infinite ratios
        valid_ratios = [r['ratio'] for r in self.efficiency_ratios 
                       if r['ratio'] != float('inf')]
        
        if not valid_ratios:
            return 0.0
        
        return sum(valid_ratios) / len(valid_ratios)
    
    def get_linkage_formation_rate(self) -> float:
        """
        Calculate rate of linkage group formation.
        
        Returns:
            Average linkage events per generation
        """
        if not self.linkage_events or not self.gac_history:
            return 0.0
        
        total_gens = self.gac_history[-1]['generation'] - self.gac_history[0]['generation']
        
        if total_gens == 0:
            return 0.0
        
        return len(self.linkage_events) / total_gens
    
    def generate_diagnostic_report(self) -> Dict:
        """
        Generate comprehensive diagnostic report.
        
        Returns:
            Dict with all diagnostic metrics
        """
        report = {
            'mutation_operators': self.get_operator_activity_summary(),
            'efficiency': {
                'average_gac_epc_ratio': self.get_average_efficiency_ratio(),
                'junk_dna_percentage': self.calculate_junk_dna_percentage(100),
                'total_genes_added': len(self.added_genes),
                'expressed_genes': sum(1 for g in self.added_genes if g['expressed']),
                'unique_genes': sum(1 for g in self.added_genes if g['unique'])
            },
            'linkage': {
                'total_events': len(self.linkage_events),
                'formation_rate': self.get_linkage_formation_rate()
            },
            'gac_epc_correlation': self._calculate_correlation(),
            'generations_profiled': len(self.gac_history)
        }
        
        return report
    
    def _calculate_correlation(self) -> float:
        """Calculate correlation between GAC and EPC."""
        if len(self.gac_history) < 2 or len(self.epc_history) < 2:
            return 0.0
        
        # Simple correlation calculation
        gac_values = [h['value'] for h in self.gac_history]
        epc_values = [h['value'] for h in self.epc_history]
        
        # Ensure same length
        min_len = min(len(gac_values), len(epc_values))
        gac_values = gac_values[:min_len]
        epc_values = epc_values[:min_len]
        
        # Calculate means
        gac_mean = sum(gac_values) / len(gac_values)
        epc_mean = sum(epc_values) / len(epc_values)
        
        # Calculate correlation
        numerator = sum((g - gac_mean) * (e - epc_mean) 
                       for g, e in zip(gac_values, epc_values))
        
        gac_var = sum((g - gac_mean) ** 2 for g in gac_values)
        epc_var = sum((e - epc_mean) ** 2 for e in epc_values)
        
        denominator = (gac_var * epc_var) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def save_report(self, filepath: str):
        """Save diagnostic report to JSON file."""
        report = self.generate_diagnostic_report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
