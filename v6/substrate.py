import numpy as np
from v5.src.cppn_environment import V5Substrate, CPPNEnvironment

def create_v6_substrate(env_genome, width=50, height=50, config=None):
    """
    Creates a substrate for V6 experiments.
    If config.baseline_mode is True or gray_scott_scalars is None, it uses the V5 CPPN mapped parameters.
    If config.gray_scott_scalars is provided, it overrides F and k with uniform maps.
    """
    # Build standard CPPN environment maps
    gen = CPPNEnvironment(env_genome.cppn_genome, width, height)
    f_map = gen.generate_property_map('f', 0.01, 0.1)
    k_map = gen.generate_property_map('k', 0.04, 0.07)
    u_map = gen.generate_property_map('diff_U', 0.8, 1.0)
    v_map = gen.generate_property_map('diff_V', 0.4, 0.6)
    
    # Override F and k if specified in config
    if config is not None and config.gray_scott_scalars is not None:
        f_val, k_val = config.gray_scott_scalars
        f_map = np.full((height, width), f_val, dtype=np.float32)
        k_map = np.full((height, width), k_val, dtype=np.float32)
        
    return V5Substrate(width, height, f_map, k_map, u_map, v_map)
