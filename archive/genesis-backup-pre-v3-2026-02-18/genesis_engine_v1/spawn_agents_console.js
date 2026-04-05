// Simple test script to spawn agents via browser console
// Open visualizer.html, then run this in the console:

// Wait for visualizer to load
setTimeout(() => {
    console.log('Spawning 20 agents...');

    // Access the visualizer instance
    const viz = window.visualizer || window.v;

    if (viz && viz.population) {
        viz.population.spawnRandom(20, viz.gridSize, viz.gridSize);
        viz.population.enabled = true;
        console.log(`Spawned agents. Population: ${viz.population.agents.length}`);
    } else {
        console.error('Visualizer not found. Make sure page is loaded.');
    }
}, 1000);
