import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'demo_output')
FRAMES_DIR = os.path.join(OUTPUT_DIR, 'frames')
LOGS_DIR = os.path.join(OUTPUT_DIR, 'logs')
VIDEOS_DIR = os.path.join(OUTPUT_DIR, 'videos')

# Ensure directories exist
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

# Simulation Hyperparameters
SEED = 42
POP_SIZE = 20
TEST_GENERATIONS = 200
FULL_GENERATIONS = 2000
STEPS_PER_GEN = 20

# V5 Specific Tweaks for Demo (Accelerated to guarantee 400+ nodes in 2000 gens)
METABOLIC_COST_EXPONENT = 1.8
NODE_MUTATION_RATE = 0.15
CONN_MUTATION_RATE = 0.20

# Visualizer Settings
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 30
SUBSTRATE_SIZE = 50  # Matches V5 default 50x50

# Colors
COLOR_V4_TINT = (0, 0, 50)     # Subtle blue
COLOR_V5_TINT = (50, 30, 0)    # Subtle amber
COLOR_TEXT = (255, 255, 255)
COLOR_BAR_BG = (50, 50, 50)
COLOR_BAR_FG = (0, 255, 0)
