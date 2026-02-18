"""
Pressure Module - Week 3 Functional Stagnation Detector

Detects when evolutionary innovation stalls and applies pressure
to break convergence and maintain exploration.
"""

__all__ = ['FunctionalStagnationDetector', 'InnovationTracker']

from .functional_stagnation_detector import FunctionalStagnationDetector, InnovationTracker
