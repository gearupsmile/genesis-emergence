/**
 * Gray-Scott Reaction-Diffusion Visualizer
 * Real-time JavaScript implementation with pattern monitoring
 */

// Parameter presets
const PRESETS = {
    spots: { F: 0.0367, k: 0.0649, Du: 0.16, Dv: 0.08, name: 'Spots (Mitosis)' },
    stripes: { F: 0.035, k: 0.060, Du: 0.16, Dv: 0.08, name: 'Stripes (Labyrinthine)' },
    waves: { F: 0.025, k: 0.050, Du: 0.16, Dv: 0.08, name: 'Waves (Pulsating)' },
    coral: { F: 0.0545, k: 0.062, Du: 0.16, Dv: 0.08, name: 'Coral Growth' },
    spirals: { F: 0.018, k: 0.051, Du: 0.16, Dv: 0.08, name: 'Spiral Waves' },
    moving_spots: { F: 0.014, k: 0.054, Du: 0.16, Dv: 0.08, name: 'Moving Spots' }
};

// Color schemes
const COLOR_SCHEMES = {
    grayscale: (v) => [v * 255, v * 255, v * 255],
    viridis: (v) => {
        // Simplified viridis colormap
        const r = Math.max(0, Math.min(255, 68 + v * (253 - 68)));
        const g = Math.max(0, Math.min(255, 1 + v * (231 - 1)));
        const b = Math.max(0, Math.min(255, 84 + v * (37 - 84)));
        return [r, g, b];
    },
    plasma: (v) => {
        // Simplified plasma colormap
        const r = Math.max(0, Math.min(255, 13 + v * (240 - 13)));
        const g = Math.max(0, Math.min(255, 8 + v * (249 - 8)));
        const b = Math.max(0, Math.min(255, 135 - v * 135));
        return [r, g, b];
    },
    inferno: (v) => {
        // Simplified inferno colormap
        const r = Math.max(0, Math.min(255, v * 252));
        const g = Math.max(0, Math.min(255, v * v * 255));
        const b = Math.max(0, Math.min(255, Math.sqrt(v) * 164));
        return [r, g, b];
    }
};

// Agent class for simple agent-based system
class Agent {
    constructor(x, y, energy = 100) {
        this.x = x;
        this.y = y;
        this.energy = energy;
        this.alive = true;
        this.age = 0;

        // Agent parameters (tuned for sustainable populations - matching Python)
        this.ENERGY_START = 100.0;
        this.ENERGY_METABOLISM = 0.3;  // Reduced from 0.5
        this.ENERGY_CONSUMPTION_RATE = 5.0;  // Increased from 2.0
        this.ENERGY_REPRODUCTION_THRESHOLD = 120.0;  // Reduced from 150.0
        this.ENERGY_REPRODUCTION_COST = 40.0;  // Reduced from 50.0
        this.MOVEMENT_SPEED = 1.0;
        this.SENSING_RADIUS = 5;

        // Statistics
        this.total_consumed = 0;
        this.offspring_count = 0;
    }

    senseGradient(U, width, height) {
        // Sense U gradient in 4 directions
        const cx = Math.floor(Math.max(0, Math.min(width - 1, this.x)));
        const cy = Math.floor(Math.max(0, Math.min(height - 1, this.y)));
        const radius = this.SENSING_RADIUS;

        // Sample in 4 directions
        const north = U[Math.max(0, cy - radius) * width + cx];
        const south = U[Math.min(height - 1, cy + radius) * width + cx];
        const west = U[cy * width + Math.max(0, cx - radius)];
        const east = U[cy * width + Math.min(width - 1, cx + radius)];

        // Compute gradient
        let dx = east - west;
        let dy = south - north;

        // Normalize
        const magnitude = Math.sqrt(dx * dx + dy * dy);
        if (magnitude > 0) {
            dx /= magnitude;
            dy /= magnitude;
        }

        return { dx, dy };
    }

    move(U, width, height) {
        if (!this.alive) return;

        // Sense gradient
        const { dx, dy } = this.senseGradient(U, width, height);

        // Move in gradient direction
        this.x += dx * this.MOVEMENT_SPEED;
        this.y += dy * this.MOVEMENT_SPEED;

        // Wrap around boundaries (periodic)
        this.x = (this.x + width) % width;
        this.y = (this.y + height) % height;
    }

    consume(U, width, height) {
        if (!this.alive) return 0;

        // Get current grid position
        const x = Math.floor(Math.max(0, Math.min(width - 1, this.x)));
        const y = Math.floor(Math.max(0, Math.min(height - 1, this.y)));
        const idx = y * width + x;

        // Consume available U (limited by what's there)
        const availableU = U[idx];
        const consumption = Math.min(availableU, 0.1); // Max 0.1 U per cycle

        // Remove from field
        U[idx] -= consumption;

        // Gain energy
        const energyGained = consumption * this.ENERGY_CONSUMPTION_RATE;
        this.energy += energyGained;
        this.total_consumed += consumption;

        return consumption;
    }

    metabolize() {
        if (!this.alive) return;

        this.energy -= this.ENERGY_METABOLISM;
        this.age++;

        // Check for death
        if (this.energy <= 0) {
            this.alive = false;
            this.energy = 0;
        }
    }

    canReproduce() {
        return this.alive && this.energy >= this.ENERGY_REPRODUCTION_THRESHOLD;
    }

    reproduce() {
        if (!this.canReproduce()) return null;

        // Pay reproduction cost
        this.energy -= this.ENERGY_REPRODUCTION_COST;

        // Create offspring at nearby position (small random offset)
        const offsetX = (Math.random() - 0.5) * 10;
        const offsetY = (Math.random() - 0.5) * 10;

        const offspring = new Agent(
            this.x + offsetX,
            this.y + offsetY,
            this.ENERGY_REPRODUCTION_COST  // Offspring starts with parent's investment
        );

        this.offspring_count++;

        return offspring;
    }

    getEnergyColor() {
        // Energy-based color: red (low) -> yellow (medium) -> green (high)
        const ratio = Math.max(0, Math.min(100, this.energy)) / 100;

        if (ratio < 0.5) {
            // Red to Yellow
            const t = ratio * 2;
            return `rgb(255, ${Math.floor(t * 255)}, 0)`;
        } else {
            // Yellow to Green
            const t = (ratio - 0.5) * 2;
            return `rgb(${Math.floor((1 - t) * 255)}, 255, 0)`;
        }
    }
}

class GrayScottSimulator {
    constructor(width, height) {
        this.width = width;
        this.height = height;

        // Double buffering for U and V
        this.U = new Float64Array(width * height);
        this.V = new Float64Array(width * height);
        this.U_new = new Float64Array(width * height);
        this.V_new = new Float64Array(width * height);

        // Parameters
        this.params = { ...PRESETS.spots };
        this.dt = 1.0;
        this.dx = 1.0;

        // State
        this.cycle = 0;
        this.running = false;
        this.cyclesPerFrame = 1;

        // Statistics
        this.initialMass = 0;
        this.fps = 0;
        this.lastFrameTime = 0;
        this.frameCount = 0;

        this.initialize();
    }

    initialize() {
        // Initialize with U=1, V=0 everywhere
        for (let i = 0; i < this.width * this.height; i++) {
            this.U[i] = 1.0;
            this.V[i] = 0.0;
        }

        // Add random perturbations in center region
        const startX = Math.floor(this.width / 4);
        const endX = Math.floor(3 * this.width / 4);
        const startY = Math.floor(this.height / 4);
        const endY = Math.floor(3 * this.height / 4);

        for (let y = startY; y < endY; y++) {
            for (let x = startX; x < endX; x++) {
                const idx = y * this.width + x;
                this.U[idx] += (Math.random() - 0.5) * 0.2;  // Increased from 0.1
                this.V[idx] += Math.random() * 0.25;  // Increased from 0.1
            }
        }

        this.clampValues();
        this.initialMass = this.getTotalMass();
        this.cycle = 0;
    }

    setParams(preset) {
        this.params = { ...PRESETS[preset] };
    }

    clampValues() {
        for (let i = 0; i < this.U.length; i++) {
            this.U[i] = Math.max(0, Math.min(1, this.U[i]));
            this.V[i] = Math.max(0, Math.min(1, this.V[i]));

            // Ensure U + V <= 1.0
            const total = this.U[i] + this.V[i];
            if (total > 1.0) {
                this.U[i] /= total;
                this.V[i] /= total;
            }
        }
    }

    getLaplacian(field, x, y) {
        const w = this.width;
        const h = this.height;

        // Periodic boundary conditions
        const xm1 = (x - 1 + w) % w;
        const xp1 = (x + 1) % w;
        const ym1 = (y - 1 + h) % h;
        const yp1 = (y + 1) % h;

        const center = field[y * w + x];
        const left = field[y * w + xm1];
        const right = field[y * w + xp1];
        const top = field[ym1 * w + x];
        const bottom = field[yp1 * w + x];

        return left + right + top + bottom - 4 * center;
    }

    step() {
        const { F, k, Du, Dv } = this.params;

        for (let y = 0; y < this.height; y++) {
            for (let x = 0; x < this.width; x++) {
                const idx = y * this.width + x;

                const u = Math.max(0, Math.min(1, this.U[idx]));
                const v = Math.max(0, Math.min(1, this.V[idx]));

                // Compute Laplacians
                const lapU = this.getLaplacian(this.U, x, y);
                const lapV = this.getLaplacian(this.V, x, y);

                // Reaction term with overflow protection
                const v2 = v * v;
                const reaction = Math.min(1.0, u * v2);

                // Gray-Scott equations
                const dU = Du * lapU - reaction + F * (1 - u);
                const dV = Dv * lapV + reaction - (F + k) * v;

                // Update
                this.U_new[idx] = u + this.dt * dU;
                this.V_new[idx] = v + this.dt * dV;
            }
        }

        // Swap buffers
        [this.U, this.U_new] = [this.U_new, this.U];
        [this.V, this.V_new] = [this.V_new, this.V];

        // Clamp values
        this.clampValues();

        this.cycle++;
    }

    getTotalMass() {
        let sum = 0;
        for (let i = 0; i < this.U.length; i++) {
            sum += this.U[i] + this.V[i];
        }
        return sum;
    }

    getStatistics() {
        let vMin = Infinity, vMax = -Infinity, vSum = 0, vSum2 = 0;

        for (let i = 0; i < this.V.length; i++) {
            const v = this.V[i];
            vMin = Math.min(vMin, v);
            vMax = Math.max(vMax, v);
            vSum += v;
            vSum2 += v * v;
        }

        const n = this.V.length;
        const vMean = vSum / n;
        const vStd = Math.sqrt(vSum2 / n - vMean * vMean);

        const currentMass = this.getTotalMass();
        const massError = this.initialMass > 0
            ? Math.abs(currentMass - this.initialMass) / this.initialMass
            : 0;

        return {
            vMin, vMax, vMean, vStd,
            vRange: vMax - vMin,
            massError,
            cycle: this.cycle
        };
    }
}

class Visualizer {
    constructor() {
        this.canvas = document.getElementById('simulationCanvas');
        this.ctx = this.canvas.getContext('2d');

        // Simulation grid size
        this.gridSize = 256;
        this.simulator = new GrayScottSimulator(this.gridSize, this.gridSize);

        // Agent system
        this.agents = [];
        this.populationStats = {
            births: 0,
            deaths: 0
        };

        // Display
        this.colorScheme = 'grayscale';
        this.imageData = this.ctx.createImageData(this.canvas.width, this.canvas.height);

        // Animation
        this.animationId = null;
        this.lastTime = performance.now();
        this.frameCount = 0;
        this.fpsUpdateInterval = 30;

        this.setupEventListeners();
        this.updateParamDisplay();
        this.render();
    }

    setupEventListeners() {
        document.getElementById('presetSelect').addEventListener('change', (e) => {
            this.simulator.setParams(e.target.value);
            this.updateParamDisplay();
        });

        document.getElementById('startBtn').addEventListener('click', () => this.start());
        document.getElementById('pauseBtn').addEventListener('click', () => this.pause());
        document.getElementById('resetBtn').addEventListener('click', () => this.reset());
        document.getElementById('stepBtn').addEventListener('click', () => this.step());

        document.getElementById('colorScheme').addEventListener('change', (e) => {
            this.colorScheme = e.target.value;
        });

        document.getElementById('speedControl').addEventListener('change', (e) => {
            this.simulator.cyclesPerFrame = parseInt(e.target.value);
        });
    }

    updateParamDisplay() {
        const params = this.simulator.params;
        document.getElementById('paramDisplay').innerHTML = `
            <div>F = ${params.F.toFixed(4)}</div>
            <div>k = ${params.k.toFixed(4)}</div>
            <div>Du = ${params.Du.toFixed(2)}</div>
            <div>Dv = ${params.Dv.toFixed(2)}</div>
        `;
    }

    start() {
        if (!this.simulator.running) {
            this.simulator.running = true;
            this.updateStatus('running', 'Running');
            this.animate();
        }
    }

    pause() {
        this.simulator.running = false;
        this.updateStatus('paused', 'Paused');
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }

    reset() {
        this.pause();
        this.simulator.initialize();
        this.updateStatus('stopped', 'Stopped');
        this.render();
        this.updateMetrics();
    }

    step() {
        this.simulator.step();
        this.render();
        this.updateMetrics();
    }

    animate() {
        if (!this.simulator.running) return;

        // Run multiple cycles per frame for speed
        for (let i = 0; i < this.simulator.cyclesPerFrame; i++) {
            this.simulator.step();
        }

        // Update agents
        this.updateAgents();

        this.render();

        // Update metrics periodically
        this.frameCount++;
        if (this.frameCount % this.fpsUpdateInterval === 0) {
            this.updateMetrics();
            this.updateFPS();
        }

        this.animationId = requestAnimationFrame(() => this.animate());
    }

    updateAgents() {
        const newborns = [];
        let deathsThisCycle = 0;

        // Update all agents (iterate backwards to safely remove dead agents)
        for (let i = this.agents.length - 1; i >= 0; i--) {
            const agent = this.agents[i];

            // Move toward U gradient
            agent.move(this.simulator.U, this.gridSize, this.gridSize);

            // Consume energy from U field
            agent.consume(this.simulator.U, this.gridSize, this.gridSize);

            // Metabolism
            agent.metabolize();

            // Check for reproduction
            if (agent.canReproduce()) {
                const offspring = agent.reproduce();
                if (offspring) {
                    newborns.push(offspring);
                    this.populationStats.births++;
                }
            }

            // Remove dead agents
            if (!agent.alive) {
                this.agents.splice(i, 1);
                deathsThisCycle++;
                this.populationStats.deaths++;
            }
        }

        // Add newborns to population
        this.agents.push(...newborns);

        // Log population changes occasionally
        if (this.frameCount % 100 === 0 && (newborns.length > 0 || deathsThisCycle > 0)) {
            console.log(`[Cycle ${this.simulator.cycle}] Pop: ${this.agents.length}, Births: ${newborns.length}, Deaths: ${deathsThisCycle}`);
        }
    }

    render() {
        const scale = this.canvas.width / this.gridSize;
        const colorFn = COLOR_SCHEMES[this.colorScheme];

        // Render V field
        for (let y = 0; y < this.gridSize; y++) {
            for (let x = 0; x < this.gridSize; x++) {
                const idx = y * this.gridSize + x;
                const v = this.simulator.V[idx];
                const [r, g, b] = colorFn(v);

                // Draw scaled pixel
                for (let dy = 0; dy < scale; dy++) {
                    for (let dx = 0; dx < scale; dx++) {
                        const px = x * scale + dx;
                        const py = y * scale + dy;
                        const pidx = (py * this.canvas.width + px) * 4;

                        this.imageData.data[pidx] = r;
                        this.imageData.data[pidx + 1] = g;
                        this.imageData.data[pidx + 2] = b;
                        this.imageData.data[pidx + 3] = 255;
                    }
                }
            }
        }

        this.ctx.putImageData(this.imageData, 0, 0);

        // Render agents on top of pattern
        this.renderAgents();

        // Update cycle count
        document.getElementById('cycleCount').textContent = this.simulator.cycle.toLocaleString();
    }

    renderAgents() {
        if (this.agents.length === 0) return;

        const scale = this.canvas.width / this.gridSize;

        // Draw each agent as a colored circle
        for (const agent of this.agents) {
            if (!agent.alive) continue;

            // Convert grid position to canvas position
            const canvasX = agent.x * scale;
            const canvasY = agent.y * scale;

            // Draw agent circle
            this.ctx.beginPath();
            this.ctx.arc(canvasX, canvasY, 4, 0, Math.PI * 2);
            this.ctx.fillStyle = agent.getEnergyColor();
            this.ctx.fill();

            // Optional: Add a black outline for visibility
            this.ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
            this.ctx.lineWidth = 1;
            this.ctx.stroke();
        }
    }

    updateMetrics() {
        const stats = this.simulator.getStatistics();

        document.getElementById('vMean').textContent = stats.vMean.toFixed(3);
        document.getElementById('vStd').textContent = stats.vStd.toFixed(3);
        document.getElementById('vRange').textContent = stats.vRange.toFixed(3);

        const massErrorPct = (stats.massError * 100).toFixed(3);
        const massErrorEl = document.getElementById('massError');
        massErrorEl.textContent = massErrorPct + '%';
        massErrorEl.className = 'metric-value ' + (stats.massError > 0.01 ? 'warning' : 'success');

        // Pattern stability assessment
        const stability = this.assessStability(stats);
        document.getElementById('stability').textContent = stability;
    }

    assessStability(stats) {
        if (stats.cycle < 100) return 'Initializing';
        if (stats.vStd < 0.01) return 'Uniform (unstable)';
        if (stats.vStd > 0.3) return 'Chaotic';
        if (stats.vStd > 0.1) return 'Stable Pattern';
        return 'Forming';
    }

    updateFPS() {
        const now = performance.now();
        const elapsed = (now - this.lastTime) / 1000;
        const fps = this.fpsUpdateInterval / elapsed;

        document.getElementById('fpsDisplay').textContent = fps.toFixed(1);

        this.lastTime = now;
    }

    updateStatus(state, text) {
        const indicator = document.getElementById('statusIndicator');
        indicator.className = `status-indicator ${state}`;
        document.getElementById('statusText').textContent = text;
    }

    spawnAgents(count) {
        console.log(`Spawning ${count} agents...`);

        for (let i = 0; i < count; i++) {
            const x = Math.random() * this.gridSize;
            const y = Math.random() * this.gridSize;
            const agent = new Agent(x, y, 100);
            this.agents.push(agent);
        }

        console.log(`Total agents: ${this.agents.length}`);
        console.log(`Energy parameters: Metabolism=${this.agents[0].ENERGY_METABOLISM}, Consumption=${this.agents[0].ENERGY_CONSUMPTION_RATE}x, Reproduction threshold=${this.agents[0].ENERGY_REPRODUCTION_THRESHOLD}`);
        return this.agents.length;
    }
}

// Global reference to visualizer
let visualizerInstance = null;

// Initialize when page loads
window.addEventListener('DOMContentLoaded', () => {
    visualizerInstance = new Visualizer();

    // Expose spawnAgents to console
    window.spawnAgents = (count = 20) => {
        if (!visualizerInstance) {
            console.error('Visualizer not initialized');
            return 0;
        }
        return visualizerInstance.spawnAgents(count);
    };

    console.log('Agent system ready! Use window.spawnAgents(count) to spawn agents.');
    console.log('Example: window.spawnAgents(20)');
});
