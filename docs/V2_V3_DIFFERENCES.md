# Genesis V2 vs V3 - Architectural Differences

## V2 (Stable Baseline)
- **Environment**: Passive (fixed F/k maps)
- **Interaction**: Depletion-based (Grey-Scott consumption)
- **Archives**: Genotype only
- **Complexity Metric**: LZ on position trace
- **Control**: No sham control built-in

## V3 (Experimental)
- **Environment**: Active (Agents can secrete chemicals to modify local F/k)
- **Interaction**: Secretion-based (3x3 neighborhood effects)
- **Archives**: Genotype + Environment Snapshot (Niche Construction)
- **Complexity Metric**: LZ on action trace (Agency metric)
- **Control**: Integrated Sham control (randomized feedback)
- **Framing**: Free Energy Principle / Markov Blanket

## Migration Status
- **Date**: 2026-02-18
- **Base**: V2 Stable
- **Branch**: `v3-secretion`
- **Version**: `3.0.0-dev`
