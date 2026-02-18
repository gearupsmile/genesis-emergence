"""
Active Diversity Manager - Diversity Module

Maintains an archive of functionally rare agents for crisis recovery.
Uses behavioral clustering to identify and preserve rare strategies.

Week 2 - Path B: Concentration-Preservation
"""

__all__ = ['ActiveDiversityManager', 'BehavioralSignature', 'extract_behavioral_signature']

from .active_diversity_manager import ActiveDiversityManager, extract_behavioral_signature
