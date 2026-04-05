"""
Active Diversity Manager

Implements Path B (Concentration-Preservation) approach:
- Extracts 5D behavioral signatures from agents
- Maintains dynamic clusters to identify rare strategies
- Archives agents with priority = avg_cluster_size / (cluster_size + 1)
- Capacity: 50 agents with priority-based eviction

Week 2 - Expert Prescription Implementation
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import copy


def extract_behavioral_signature(agent, translator=None) -> np.ndarray:
    """
    Extract 5-dimensional behavioral signature from agent.
    
    Simplified to use only available EvolvableGenome API.
    
    Dimensions:
    1. Energy efficiency: phenotype_length / metabolic_cost
    2. Exploration: Phenotype complexity (length)
    3. Cost efficiency: 1 / metabolic_cost
    4. Genome size: Number of genes
    5. Cost per gene: metabolic_cost / genome_length
    
    Args:
        agent: StructurallyEvolvableAgent instance
        translator: CodonTranslator (optional, for phenotype analysis)
        
    Returns:
        5D numpy array, normalized to [0, 1]
    """
    genome = agent.genome
    
    # Dimension 1: Energy efficiency (phenotype/cost)
    metabolic_cost = genome.metabolic_cost
    if agent.phenotype is not None and len(agent.phenotype) > 0:
        phenotype_complexity = len(agent.phenotype)
    else:
        phenotype_complexity = genome.get_length()
    
    energy_efficiency = phenotype_complexity / (metabolic_cost + 0.01)
    
    # Dimension 2: Exploration (phenotype complexity)
    exploration = phenotype_complexity / 50.0  # Normalize by typical max
    
    # Dimension 3: Cost efficiency (inverse cost)
    cost_efficiency = 1.0 / (metabolic_cost + 0.01)
    
    # Dimension 4: Genome size
    genome_size = genome.get_length() / 50.0  # Normalize by typical max
    
    # Dimension 5: Cost per gene (efficiency measure)
    cost_per_gene = metabolic_cost / max(genome.get_length(), 1)
    
    # Create signature vector
    signature = np.array([
        energy_efficiency,
        exploration,
        cost_efficiency,
        genome_size,
        cost_per_gene
    ])
    
    # Normalize to [0, 1] range (clip extremes)
    signature = np.clip(signature, 0, 10)  # Clip outliers
    signature = signature / 10.0  # Normalize to [0, 1]
    
    return signature


class ActiveDiversityManager:
    """
    Manages archive of functionally rare agents.
    
    Uses online k-means clustering to identify behavioral clusters
    and archives agents from under-represented clusters.
    """
    
    def __init__(self, archive_size: int = 50, n_clusters: int = 10, 
                 update_interval: int = 100):
        """
        Initialize Active Diversity Manager.
        
        Args:
            archive_size: Maximum number of agents in archive (default: 50)
            n_clusters: Number of behavioral clusters (default: 10)
            update_interval: Generations between cluster updates (default: 100)
        """
        self.archive_size = archive_size
        self.n_clusters = n_clusters
        self.update_interval = update_interval
        
        # Archive storage
        self.archive: List = []  # List of archived agents
        self.archive_signatures: List[np.ndarray] = []  # Their behavioral signatures
        self.archive_priorities: List[float] = []  # Their archival priorities
        
        # Clustering state
        self.cluster_centers: Optional[np.ndarray] = None  # k cluster centers (k x 5)
        self.cluster_assignments: List[int] = []  # Agent -> cluster mapping
        self.cluster_sizes: Dict[int, int] = defaultdict(int)  # Cluster -> size
        
        # Statistics
        self.generation_count = 0
        self.total_archived = 0
        self.total_evicted = 0
    
    def update_clusters(self, population, translator=None):
        """
        Update behavioral clusters based on current population.
        
        Uses online k-means: update cluster centers incrementally.
        
        Args:
            population: List of agents
            translator: CodonTranslator (optional)
        """
        if len(population) == 0:
            return
        
        # Extract signatures for all agents
        signatures = np.array([extract_behavioral_signature(agent, translator) 
                              for agent in population])
        
        # Initialize clusters if first time
        if self.cluster_centers is None:
            # Use k-means++ initialization
            self.cluster_centers = self._kmeans_plus_plus_init(signatures, self.n_clusters)
        
        # Assign agents to nearest cluster
        self.cluster_assignments = []
        self.cluster_sizes = defaultdict(int)
        
        for sig in signatures:
            # Find nearest cluster
            distances = np.linalg.norm(self.cluster_centers - sig, axis=1)
            cluster_id = np.argmin(distances)
            self.cluster_assignments.append(cluster_id)
            self.cluster_sizes[cluster_id] += 1
        
        # Update cluster centers (online k-means)
        if self.generation_count % self.update_interval == 0:
            for cluster_id in range(self.n_clusters):
                # Get all signatures in this cluster
                cluster_sigs = signatures[np.array(self.cluster_assignments) == cluster_id]
                if len(cluster_sigs) > 0:
                    # Update center as mean of cluster members
                    self.cluster_centers[cluster_id] = np.mean(cluster_sigs, axis=0)
        
        self.generation_count += 1
    
    def calculate_archival_priority(self, agent, translator=None) -> float:
        """
        Calculate archival priority for an agent.
        
        Priority formula: avg_cluster_size / (agent_cluster_size + 1)
        Agents from small (rare) clusters get high priority.
        
        Args:
            agent: Agent to evaluate
            translator: CodonTranslator (optional)
            
        Returns:
            Priority score (higher = more important to archive)
        """
        if self.cluster_centers is None:
            return 1.0  # Default priority if no clusters yet
        
        # Extract agent's signature
        signature = extract_behavioral_signature(agent, translator)
        
        # Find agent's cluster
        distances = np.linalg.norm(self.cluster_centers - signature, axis=1)
        cluster_id = np.argmin(distances)
        
        # Calculate priority
        agent_cluster_size = self.cluster_sizes.get(cluster_id, 1)
        avg_cluster_size = np.mean(list(self.cluster_sizes.values())) if self.cluster_sizes else 1.0
        
        # Priority = avg / (size + 1)
        # Small clusters (rare strategies) get high priority
        priority = avg_cluster_size / (agent_cluster_size + 1)
        
        return priority
    
    def archive_agent(self, agent, translator=None):
        """
        Add agent to archive if priority warrants.
        
        If archive is full, evict lowest-priority agent if new agent
        has higher priority.
        
        Args:
            agent: Agent to potentially archive
            translator: CodonTranslator (optional)
        """
        # Calculate priority
        priority = self.calculate_archival_priority(agent, translator)
        signature = extract_behavioral_signature(agent, translator)
        
        # Clone agent for archival (deep copy)
        archived_agent = copy.deepcopy(agent)
        
        # If archive not full, add directly
        if len(self.archive) < self.archive_size:
            self.archive.append(archived_agent)
            self.archive_signatures.append(signature)
            self.archive_priorities.append(priority)
            self.total_archived += 1
        else:
            # Archive full - check if new agent has higher priority than lowest
            min_priority_idx = np.argmin(self.archive_priorities)
            min_priority = self.archive_priorities[min_priority_idx]
            
            if priority > min_priority:
                # Evict lowest priority, add new agent
                self.archive[min_priority_idx] = archived_agent
                self.archive_signatures[min_priority_idx] = signature
                self.archive_priorities[min_priority_idx] = priority
                self.total_evicted += 1
                self.total_archived += 1
    
    def get_archive_composition(self) -> Dict:
        """
        Get statistics about archive composition.
        
        Returns:
            Dictionary with archive metrics
        """
        if len(self.archive) == 0:
            return {
                'size': 0,
                'cluster_distribution': {},
                'avg_priority': 0.0,
                'signature_variance': 0.0
            }
        
        # Assign archived agents to clusters
        archive_clusters = []
        for sig in self.archive_signatures:
            if self.cluster_centers is not None:
                distances = np.linalg.norm(self.cluster_centers - sig, axis=1)
                cluster_id = np.argmin(distances)
                archive_clusters.append(cluster_id)
            else:
                archive_clusters.append(0)
        
        # Cluster distribution
        cluster_dist = defaultdict(int)
        for cid in archive_clusters:
            cluster_dist[cid] += 1
        
        # Signature variance (diversity measure)
        if len(self.archive_signatures) > 1:
            sig_array = np.array(self.archive_signatures)
            signature_variance = np.mean(np.var(sig_array, axis=0))
        else:
            signature_variance = 0.0
        
        return {
            'size': len(self.archive),
            'cluster_distribution': dict(cluster_dist),
            'avg_priority': np.mean(self.archive_priorities),
            'signature_variance': float(signature_variance),
            'total_archived': self.total_archived,
            'total_evicted': self.total_evicted
        }
    
    def _kmeans_plus_plus_init(self, data: np.ndarray, k: int) -> np.ndarray:
        """
        Initialize cluster centers using k-means++ algorithm.
        
        Args:
            data: Data points (n x d)
            k: Number of clusters
            
        Returns:
            Initial cluster centers (k x d)
        """
        n_samples = data.shape[0]
        centers = []
        
        # Choose first center randomly
        first_idx = np.random.randint(n_samples)
        centers.append(data[first_idx])
        
        # Choose remaining centers
        for _ in range(1, k):
            # Calculate distance to nearest center for each point
            distances = np.array([min(np.linalg.norm(x - c) for c in centers) 
                                 for x in data])
            
            # Choose next center with probability proportional to distance^2
            probabilities = distances ** 2
            prob_sum = probabilities.sum()
            
            # Handle edge case where all distances are zero
            if prob_sum == 0 or np.isnan(prob_sum):
                next_idx = np.random.randint(n_samples)
            else:
                probabilities /= prob_sum
                next_idx = np.random.choice(n_samples, p=probabilities)
            centers.append(data[next_idx])
        
        return np.array(centers)
    
    def get_statistics(self) -> Dict:
        """Get ADM statistics."""
        return {
            'archive_size': len(self.archive),
            'total_archived': self.total_archived,
            'total_evicted': self.total_evicted,
            'generation_count': self.generation_count,
            'n_clusters': self.n_clusters
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return (f"ActiveDiversityManager(archive={len(self.archive)}/{self.archive_size}, "
                f"clusters={self.n_clusters}, gen={self.generation_count})")
