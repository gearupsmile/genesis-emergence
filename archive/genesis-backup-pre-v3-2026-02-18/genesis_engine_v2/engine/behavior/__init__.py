"""
Behavior Module - Action-Based Behavioral Tracking

Tracks what agents DO (actions) rather than what they ARE (structure).
This is the emergency fix for Week 3 behavioral diversity issue.
"""

__all__ = ['BehavioralTracker', 'ActionRecorder']

from .behavioral_tracker import BehavioralTracker
from .action_recorder import ActionRecorder
