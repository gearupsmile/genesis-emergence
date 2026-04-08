# Genesis Engine V5: Co-evolutionary Open-Endedness

Genesis V5 transitions the engine from static competitive fitness into an unbounded open-ended environment generation paradigm inspired by POET (Paired Open-Ended Trailblazer).

## New Architecture

V5 introduces three major pillars:
1. **Expressive Environments (CPPN-based Substrates)**
   Instead of global scalar settings for the Gray-Scott reaction-diffusion physics, V5 employs an independent `CPPNEnvironment` that maps parameters locally. Feed rate, kill rate, and diffusion coefficients vary per cell, producing heterogeneous biomes of varying complexity.
2. **Co-evolutionary Dynamics & Goal Switching**
   The `CoevolutionOrchestrator` manages distinct parallel worlds. When an environment stagnates, it is mutated. The `POETMinimalCriteria` ensures newly sprouted environments are neither utterly trivial nor hopelessly lethal. Crucially, successful agents attempt to cross-migrate into foreign worlds (Goal Switching). If they show superior pre-adaptation, they transfer and populate that world.
3. **Advanced Open-Ended Metrics**
    - **PATA-EC**: Performance of All Transferred Agents - Enhanced Criterion analyzes the true novelty of a sprouted environment by assuring agents face authentically variant challenges, rather than simple global difficulty scalings.
    - **ANNEX**: Accumulated Novel Environments Explored logs the historical volume of distinct functional environments generated and solved.

## Running the Simulation
V5 logic resides entirely in `v5/`. Execute the central co-evolution engine from the repository root:
```bash
python v5/experiments/run_v5.py
```
Or to simply verify components:
```bash
python v5/experiments/quicktest_v5.py
```

## References
- *Wang et al. (2019)* - Paired Open-Ended Trailblazer (POET): Endlessly Generating Increasingly Complex and Diverse Learning Environments and Their Solutions.
