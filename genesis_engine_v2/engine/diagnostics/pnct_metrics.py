"""
PNCT Metrics: Phenotypic Novelty & Complexity Trajectory Analysis

This module provides diagnostic metrics to distinguish between:
- High-variance equilibrium (random walk in metric space)
- True open-ended evolution (directional exploration, novelty accumulation)

Key Metrics:
1. Genome Architecture Complexity (GAC): Structural complexity measures
2. Normalized Novelty Distance (NND): Behavioral novelty between epochs
3. Expressed Phenotype Complexity (EPC): Phenotypic complexity measures
"""

from typing import List, Dict, Tuple, Optional
import statistics


def lz_complexity(s: str) -> float:
    """
    Compute Lempel-Ziv complexity of a string.
    
    Measures algorithmic complexity by counting unique substrings
    encountered during a left-to-right scan.
    
    Args:
        s: Input string
        
    Returns:
        Normalized LZ complexity (0.0 to 1.0)
        
    Examples:
        lz_complexity("AAAAA") -> low (repetitive)
        lz_complexity("ABCABC") -> medium (some pattern)
        lz_complexity("ABCDEF") -> high (no repetition)
    """
    if not s or len(s) == 0:
        return 0.0
    
    if len(s) == 1:
        return 0.5  # Single character has medium complexity
    
    n = len(s)
    i = 0
    complexity = 0
    
    while i < n:
        # Find longest prefix of s[i:] that appears in s[0:i]
        max_len = 0
        for length in range(1, n - i + 1):
            substring = s[i:i+length]
            # Check if this substring appears before position i
            if i > 0 and substring in s[:i]:
                max_len = length
            else:
                # First occurrence or not found - stop extending
                if i == 0 or max_len > 0:
                    break
        
        # Move past this substring (or single char if no match)
        step = max(1, max_len + 1)  # +1 to include the new character
        i += step
        complexity += 1
    
    # Normalize: more unique patterns = higher complexity
    # For highly repetitive strings, complexity will be low
    # For random strings, complexity will be high
    max_theoretical = n  # Upper bound
    return min(1.0, complexity / max(1, max_theoretical * 0.5))


def extract_expressed_phenotype(agent, translator) -> List[str]:
    """
    Extract expressed phenotype (instruction list) from an agent.
    
    Args:
        agent: StructurallyEvolvableAgent instance
        translator: CodonTranslator instance
        
    Returns:
        List of instruction strings
    """
    # Get expressed gene indices
    genome_length = agent.genome.get_length()
    expressed_indices = agent.linkage_structure.get_expressed_indices(genome_length)
    
    if not expressed_indices:
        return []
    
    # Extract expressed codons
    codons = agent.genome.sequence
    expressed_codons = [codons[i] for i in expressed_indices if i < len(codons)]
    
    # Translate to instructions using translate_agent method
    instructions = []
    for codon in expressed_codons:
        try:
            instruction = translator.translate_agent(codon)
            if instruction:  # Only add if translation succeeded
                instructions.append(instruction)
        except (KeyError, ValueError, AttributeError):
            # Skip invalid codons
            continue
    
    return instructions


class ComplexityTracker:
    """
    Computes Genome Architecture Complexity (GAC) metrics.
    
    Tracks structural complexity of the population:
    - Genome length (number of genes)
    - Number of linkage groups
    - Average linkage group size
    
    Returns mean, median, and variance for each metric.
    """
    
    def __init__(self):
        """Initialize the complexity tracker."""
        pass
    
    def calculate_metrics(self, population: List) -> Dict[str, Dict[str, float]]:
        """
        Calculate GAC metrics for a population.
        
        Args:
            population: List of StructurallyEvolvableAgent instances
            
        Returns:
            Dict with structure:
            {
                'genome_length': {'mean': float, 'median': float, 'variance': float},
                'linkage_groups': {'mean': float, 'median': float, 'variance': float},
                'avg_group_size': {'mean': float, 'median': float, 'variance': float}
            }
        """
        if not population:
            return self._empty_metrics()
        
        # Extract metrics from population
        genome_lengths = [agent.genome.get_length() for agent in population]
        linkage_groups = [agent.linkage_structure.get_num_groups() for agent in population]
        
        # Calculate average group sizes
        avg_group_sizes = []
        for agent in population:
            num_groups = agent.linkage_structure.get_num_groups()
            genome_len = agent.genome.get_length()
            avg_size = genome_len / num_groups if num_groups > 0 else 0
            avg_group_sizes.append(avg_size)
        
        # Compute statistics
        return {
            'genome_length': self._compute_stats(genome_lengths),
            'linkage_groups': self._compute_stats(linkage_groups),
            'avg_group_size': self._compute_stats(avg_group_sizes)
        }
    
    def _compute_stats(self, values: List[float]) -> Dict[str, float]:
        """Compute mean, median, variance for a list of values."""
        if not values:
            return {'mean': 0.0, 'median': 0.0, 'variance': 0.0}
        
        return {
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'variance': statistics.variance(values) if len(values) > 1 else 0.0
        }
    
    def _empty_metrics(self) -> Dict[str, Dict[str, float]]:
        """Return empty metrics structure."""
        empty = {'mean': 0.0, 'median': 0.0, 'variance': 0.0}
        return {
            'genome_length': empty.copy(),
            'linkage_groups': empty.copy(),
            'avg_group_size': empty.copy()
        }
    
    def compute_epc(self, agent, translator) -> Dict[str, float]:
        """
        Compute Expressed Phenotype Complexity (EPC) for an agent.
        
        Args:
            agent: StructurallyEvolvableAgent instance
            translator: CodonTranslator instance
            
        Returns:
            Dict with:
            - 'lz_complexity': Lempel-Ziv complexity of expressed codons
            - 'instruction_diversity': Number of unique instruction types
            - 'control_flow_estimate': Count of control flow instructions
        """
        # Extract expressed phenotype
        instructions = extract_expressed_phenotype(agent, translator)
        
        if not instructions:
            return {
                'lz_complexity': 0.0,
                'instruction_diversity': 0.0,
                'control_flow_estimate': 0.0
            }
        
        # Get expressed codon string for LZ complexity
        genome_length = agent.genome.get_length()
        expressed_indices = agent.linkage_structure.get_expressed_indices(genome_length)
        codons = agent.genome.sequence
        expressed_codons = [codons[i] for i in expressed_indices if i < len(codons)]
        codon_string = ''.join(expressed_codons)
        
        # Compute metrics
        lz_comp = lz_complexity(codon_string)
        
        # Instruction diversity: unique instruction types
        unique_instructions = len(set(instructions))
        max_diversity = len(instructions) if instructions else 1
        instruction_div = unique_instructions / max_diversity
        
        # Control flow estimate: count IF/LOOP instructions
        control_flow_count = sum(1 for inst in instructions 
                                if 'IF' in inst or 'LOOP' in inst or 'WHILE' in inst)
        control_flow_est = control_flow_count / len(instructions) if instructions else 0.0
        
        return {
            'lz_complexity': lz_comp,
            'instruction_diversity': instruction_div,
            'control_flow_estimate': control_flow_est
        }
    
    def calculate_epc_population(self, population: List, translator) -> Dict[str, Dict[str, float]]:
        """
        Calculate EPC metrics for entire population.
        
        Args:
            population: List of StructurallyEvolvableAgent instances
            translator: CodonTranslator instance
            
        Returns:
            Dict with mean, median, variance, p90 for each EPC metric
        """
        if not population:
            empty = {'mean': 0.0, 'median': 0.0, 'variance': 0.0, 'p90': 0.0}
            return {
                'lz_complexity': empty.copy(),
                'instruction_diversity': empty.copy(),
                'control_flow_estimate': empty.copy()
            }
        
        # Compute EPC for each agent
        lz_values = []
        diversity_values = []
        control_flow_values = []
        
        for agent in population:
            epc = self.compute_epc(agent, translator)
            lz_values.append(epc['lz_complexity'])
            diversity_values.append(epc['instruction_diversity'])
            control_flow_values.append(epc['control_flow_estimate'])
        
        # Compute statistics with 90th percentile
        return {
            'lz_complexity': self._compute_stats_with_p90(lz_values),
            'instruction_diversity': self._compute_stats_with_p90(diversity_values),
            'control_flow_estimate': self._compute_stats_with_p90(control_flow_values)
        }
    
    def _compute_stats_with_p90(self, values: List[float]) -> Dict[str, float]:
        """Compute mean, median, variance, and 90th percentile."""
        if not values:
            return {'mean': 0.0, 'median': 0.0, 'variance': 0.0, 'p90': 0.0}
        
        sorted_values = sorted(values)
        p90_index = int(len(sorted_values) * 0.9)
        
        return {
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'variance': statistics.variance(values) if len(values) > 1 else 0.0,
            'p90': sorted_values[p90_index] if sorted_values else 0.0
        }


class NoveltyAnalyzer:
    """
    Computes Normalized Novelty Distance (NND) between Pareto fronts.
    
    Measures behavioral novelty by comparing expressed phenotypes
    across evolutionary epochs using Hamming distance on codon strings.
    """
    
    def __init__(self):
        """Initialize the novelty analyzer."""
        self.previous_front = None
        self.previous_variance = 1.0  # Default normalization factor
    
    def extract_expressed_codons(self, agent) -> str:
        """
        Extract expressed codon string from an agent.
        
        Uses LinkageStructure.get_expressed_indices() to determine
        which codons are actually expressed in the phenotype.
        
        Args:
            agent: StructurallyEvolvableAgent instance
            
        Returns:
            String of expressed codons (e.g., "ACGTUACG...")
        """
        genome_length = agent.genome.get_length()
        expressed_indices = agent.linkage_structure.get_expressed_indices(genome_length)
        codons = agent.genome.sequence  # Use sequence attribute
        
        # Extract only expressed codons
        expressed_codons = [codons[i] for i in expressed_indices if i < len(codons)]
        
        return ''.join(expressed_codons)
    
    def hamming_distance(self, str1: str, str2: str) -> float:
        """
        Calculate Hamming distance between two strings.
        
        Handles strings of different lengths by padding shorter one.
        
        Args:
            str1, str2: Codon strings to compare
            
        Returns:
            Hamming distance (number of differing positions)
        """
        # Pad to same length
        max_len = max(len(str1), len(str2))
        str1_padded = str1.ljust(max_len, 'X')  # Pad with placeholder
        str2_padded = str2.ljust(max_len, 'X')
        
        # Count differences
        distance = sum(c1 != c2 for c1, c2 in zip(str1_padded, str2_padded))
        
        return float(distance)
    
    def calculate_nnd(self, current_front: List, pareto_evaluator) -> Dict[str, float]:
        """
        Calculate Normalized Novelty Distance for current Pareto front.
        
        Args:
            current_front: List of agents in current Pareto front
            pareto_evaluator: ParetoCoevolutionEvaluator instance
            
        Returns:
            Dict with:
            - 'mean_nnd': Average normalized novelty distance
            - 'max_nnd': Maximum normalized novelty distance
            - 'min_nnd': Minimum normalized novelty distance
            - 'front_size': Number of agents in current front
        """
        if not current_front:
            return {'mean_nnd': 0.0, 'max_nnd': 0.0, 'min_nnd': 0.0, 'front_size': 0}
        
        # First epoch - no previous front to compare
        if self.previous_front is None:
            self.previous_front = current_front
            self._update_variance(current_front)
            return {
                'mean_nnd': 0.0,
                'max_nnd': 0.0,
                'min_nnd': 0.0,
                'front_size': len(current_front)
            }
        
        # Extract expressed codons for both fronts
        current_codons = [self.extract_expressed_codons(agent) for agent in current_front]
        previous_codons = [self.extract_expressed_codons(agent) for agent in self.previous_front]
        
        # Calculate minimum distance for each current agent to previous front
        novelty_distances = []
        for curr_codon in current_codons:
            min_dist = min(self.hamming_distance(curr_codon, prev_codon) 
                          for prev_codon in previous_codons)
            
            # Normalize by previous epoch's variance
            normalized_dist = min_dist / self.previous_variance if self.previous_variance > 0 else 0
            novelty_distances.append(normalized_dist)
        
        # Update for next epoch
        self.previous_front = current_front
        self._update_variance(current_front)
        
        # Return statistics
        return {
            'mean_nnd': statistics.mean(novelty_distances) if novelty_distances else 0.0,
            'max_nnd': max(novelty_distances) if novelty_distances else 0.0,
            'min_nnd': min(novelty_distances) if novelty_distances else 0.0,
            'front_size': len(current_front)
        }
    
    def _update_variance(self, front: List):
        """
        Update variance estimate from current front.
        
        Calculates maximum pairwise distance within the front
        to use as normalization factor for next epoch.
        """
        if len(front) < 2:
            self.previous_variance = 1.0
            return
        
        # Extract codons
        codons = [self.extract_expressed_codons(agent) for agent in front]
        
        # Calculate all pairwise distances
        distances = []
        for i in range(len(codons)):
            for j in range(i + 1, len(codons)):
                dist = self.hamming_distance(codons[i], codons[j])
                distances.append(dist)
        
        # Use maximum distance as variance estimate
        self.previous_variance = max(distances) if distances else 1.0


class PNCTLogger:
    """
    Orchestrates PNCT metric logging at specified intervals.
    
    Integrates ComplexityTracker and NoveltyAnalyzer to provide
    comprehensive diagnostic metrics for evolutionary dynamics.
    """
    
    def __init__(self, gac_interval: int = 500, nnd_interval: int = 1000, translator=None):
        """
        Initialize PNCT logger.
        
        Args:
            gac_interval: Generations between GAC/EPC logging
            nnd_interval: Generations between NND logging
            translator: CodonTranslator instance for EPC metrics
        """
        self.gac_interval = gac_interval
        self.nnd_interval = nnd_interval
        self.translator = translator
        
        self.complexity_tracker = ComplexityTracker()
        self.novelty_analyzer = NoveltyAnalyzer()
        
        self.gac_history = []
        self.epc_history = []
        self.nnd_history = []
    
    def should_log_gac(self, generation: int) -> bool:
        """Check if GAC should be logged this generation."""
        return generation % self.gac_interval == 0
    
    def should_log_nnd(self, generation: int) -> bool:
        """Check if NND should be logged this generation."""
        return generation % self.nnd_interval == 0
    
    def log_metrics(self, generation: int, population: List, pareto_evaluator, translator=None) -> Dict:
        """
        Log PNCT metrics for current generation.
        
        Args:
            generation: Current generation number
            population: List of agents
            pareto_evaluator: ParetoCoevolutionEvaluator instance
            translator: CodonTranslator instance (for EPC metrics)
            
        Returns:
            Dict with logged metrics (empty if not a logging generation)
        """
        metrics = {'generation': generation}
        
        # Log GAC if interval reached
        if self.should_log_gac(generation):
            gac_metrics = self.complexity_tracker.calculate_metrics(population)
            metrics['gac'] = gac_metrics
            self.gac_history.append({'generation': generation, **gac_metrics})
            
            # Log EPC alongside GAC if translator available
            if translator or self.translator:
                trans = translator or self.translator
                epc_metrics = self.complexity_tracker.calculate_epc_population(population, trans)
                metrics['epc'] = epc_metrics
                self.epc_history.append({'generation': generation, **epc_metrics})
        
        # Log NND if interval reached
        if self.should_log_nnd(generation):
            # Get Pareto front
            pareto_front = pareto_evaluator.get_pareto_front(population)
            nnd_metrics = self.novelty_analyzer.calculate_nnd(pareto_front, pareto_evaluator)
            metrics['nnd'] = nnd_metrics
            self.nnd_history.append({'generation': generation, **nnd_metrics})
        
        return metrics
    
    def get_gac_history(self) -> List[Dict]:
        """Get complete GAC history."""
        return self.gac_history
    
    def get_epc_history(self) -> List[Dict]:
        """Get complete EPC history."""
        return self.epc_history
    
    def get_nnd_history(self) -> List[Dict]:
        """Get complete NND history."""
        return self.nnd_history
