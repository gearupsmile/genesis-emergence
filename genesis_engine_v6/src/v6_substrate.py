"""
v6_substrate.py - Substrate and Gray-Scott reaction-diffusion with secretion physics for V6
"""

import numpy as np
from scipy.ndimage import laplace
from genesis_engine_v3.engine.substrate import Substrate
from v5.src.cppn_environment import V5Substrate, CPPNEnvironment
from v5.src.coevolution import EnvironmentGenome

class V6Substrate(V5Substrate):
    """
    V6 Substrate extending V5Substrate for co-evolutionary reaction-diffusion environments.
    """
    pass

__all__ = ['Substrate', 'V5Substrate', 'V6Substrate', 'CPPNEnvironment', 'EnvironmentGenome']

