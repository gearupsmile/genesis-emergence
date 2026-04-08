import numpy as np
from genesis_engine_v3.engine.cppn_genome import CPPNGenome

class CPPNEnvironment:
    """
    Generates 2D environmental property maps from a CPPN genome.
    This enables infinite granularity in environment physics where parameters
    like feed rate, kill rate, and diffusion coefficients can vary per-cell.
    """
    def __init__(self, cppn_genome: CPPNGenome, width: int = 50, height: int = 50):
        self.cppn_genome = cppn_genome
        self.width = width
        self.height = height

    def generate_property_map(self, property_name: str, min_val: float = 0.0, max_val: float = 1.0) -> np.ndarray:
        """
        Evaluate the CPPN over all (x, y) coordinates to generate a 2D property map.
        The CPPN is expected to output a value usually around [-1, 1] or [0, 1] based on activation.
        We will normalize the output to [min_val, max_val].
        """
        prop_map = np.zeros((self.height, self.width), dtype=np.float32)
        
        for y in range(self.height):
            # Normalize y to [-1, 1]
            ny = (y / max(1, self.height - 1)) * 2.0 - 1.0
            for x in range(self.width):
                # Normalize x to [-1, 1]
                nx = (x / max(1, self.width - 1)) * 2.0 - 1.0
                
                inputs = {
                    'x': nx,
                    'y': ny,
                    # We can add other inputs later like distance from center
                }
                outputs = self.cppn_genome.activate(inputs)
                raw_val = outputs.get(property_name, 0.0)
                
                # Assume raw_val is typically [-1, 1] from tanh or [0, 1] from sigmoid.
                # Here we just blindly apply a min-max scaling, treating raw_val as roughly [0, 1]
                # If using tanh, map from [-1, 1] to [0, 1] first:
                val_01 = (raw_val + 1.0) / 2.0
                val_01 = max(0.0, min(1.0, val_01)) # Clamp strictly
                
                prop_map[y, x] = min_val + val_01 * (max_val - min_val)
                
        return prop_map


class V5Substrate:
    """
    Enhanced Gray-Scott Substrate that uses per-cell arrays for parameters
    instead of flat scalars. Integrates the expressive environments.
    """
    def __init__(self, width: int, height: int, f_map: np.ndarray, k_map: np.ndarray, 
                 diff_u_map: np.ndarray, diff_v_map: np.ndarray):
        self.width = width
        self.height = height
        
        # Chemical concentrations
        self.U = np.ones((height, width), dtype=np.float32)
        self.V = np.zeros((height, width), dtype=np.float32)
        self.S = np.zeros((height, width), dtype=np.float32) # Secretion
        
        # Heterogeneous parameter maps
        self.f = f_map
        self.k = k_map
        self.diff_u = diff_u_map
        self.diff_v = diff_v_map
        self.diff_s = 0.1 # Constant for now, or can be a map
        self.decay_s = 0.01

        # Add a little initial V to break symmetry
        center_y, center_x = height//2, width//2
        r = 5
        self.V[center_y-r:center_y+r, center_x-r:center_x+r] = 0.3
        self.U[center_y-r:center_y+r, center_x-r:center_x+r] = 0.7

    def step(self):
        """Update using 2D parameter arrays"""
        # Laplacian using array rolling
        lap_U = (np.roll(self.U, 1, axis=0) + np.roll(self.U, -1, axis=0) +
                 np.roll(self.U, 1, axis=1) + np.roll(self.U, -1, axis=1) - 4 * self.U)
        lap_V = (np.roll(self.V, 1, axis=0) + np.roll(self.V, -1, axis=0) +
                 np.roll(self.V, 1, axis=1) + np.roll(self.V, -1, axis=1) - 4 * self.V)
        lap_S = (np.roll(self.S, 1, axis=0) + np.roll(self.S, -1, axis=0) +
                 np.roll(self.S, 1, axis=1) + np.roll(self.S, -1, axis=1) - 4 * self.S)

        uvv = self.U * self.V * self.V
        
        # Element-wise operations using per-cell matrices
        new_U = self.U + (self.diff_u * lap_U - uvv + self.f * (1.0 - self.U))
        new_V = self.V + (self.diff_v * lap_V + uvv - (self.f + self.k) * self.V)
        new_S = self.S + (self.diff_s * lap_S - self.decay_s * self.S)

        self.U = np.clip(new_U, 0, 1)
        self.V = np.clip(new_V, 0, 1)
        self.S = np.clip(new_S, 0, 1)

    def deposit_secretion(self, x: int, y: int, amount: float):
        # 3x3 deposit
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                ny, nx = (y + dy) % self.height, (x + dx) % self.width
                self.S[ny, nx] = min(1.0, self.S[ny, nx] + amount / 9.0)
