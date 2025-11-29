# Gray-Scott Parameter Guide

Complete reference for Gray-Scott reaction-diffusion parameters and pattern formation.

## Parameter Overview

The Gray-Scott model has four key parameters:

| Parameter | Symbol | Description | Typical Range |
|-----------|--------|-------------|---------------|
| Feed Rate | F | Rate at which U is added | 0.01 - 0.08 |
| Kill Rate | k | Rate at which V is removed | 0.045 - 0.07 |
| U Diffusion | Du | Diffusion rate for chemical U | 0.16 - 0.21 |
| V Diffusion | Dv | Diffusion rate for chemical V | 0.08 - 0.11 |

## Stable Pattern Presets

### Spots (Mitosis)

**Parameters**: F=0.0367, k=0.0649, Du=0.16, Dv=0.08

**Description**: Creates stable spots that periodically divide (mitosis-like behavior). This is one of the most stable and visually striking patterns.

**Characteristics**:
- Forms within 500-1000 cycles
- Spots maintain consistent size
- Division occurs when spots grow too large
- Highly stable for 10,000+ cycles

**Best for**: Demonstrating self-organization and replication

---

### Stripes (Labyrinthine)

**Parameters**: F=0.035, k=0.060, Du=0.16, Dv=0.08

**Description**: Creates maze-like stripe patterns that form intricate networks.

**Characteristics**:
- Forms within 1000-2000 cycles
- Creates connected labyrinth structures
- Relatively stable once formed
- Some slow evolution of pattern

**Best for**: Complex spatial structures

---

### Waves (Pulsating)

**Parameters**: F=0.025, k=0.050, Du=0.16, Dv=0.08

**Description**: Dynamic wave patterns that pulse and propagate across the domain.

**Characteristics**:
- Highly dynamic, never fully stabilizes
- Waves propagate and interact
- Creates beautiful temporal patterns
- Requires longer observation (2000+ cycles)

**Best for**: Studying wave dynamics and temporal evolution

---

### Coral Growth

**Parameters**: F=0.0545, k=0.062, Du=0.16, Dv=0.08

**Description**: Branching structures resembling coral growth.

**Characteristics**:
- Slow formation (2000+ cycles)
- Creates dendritic (tree-like) patterns
- Branches grow and interact
- Moderately stable

**Best for**: Biomimetic pattern formation

---

### Spiral Waves

**Parameters**: F=0.018, k=0.051, Du=0.16, Dv=0.08

**Description**: Rotating spiral patterns similar to those in chemical oscillators.

**Characteristics**:
- Forms spiral cores that rotate
- Highly dynamic
- Can have multiple spiral centers
- Requires large grid (256×256+)

**Best for**: Studying oscillatory dynamics

---

### Moving Spots

**Parameters**: F=0.014, k=0.054, Du=0.16, Dv=0.08

**Description**: Spots that drift and move across the domain.

**Characteristics**:
- Spots have directional motion
- Can collide and merge
- Requires very long runs (5000+ cycles)
- Sensitive to initial conditions

**Best for**: Studying particle-like behavior

## Parameter Space Map

The Gray-Scott parameter space can be visualized as regions in F-k space:

```
k
^
|  Uniform
|  ┌─────────────────────────
|  │
|  │  Spots    Stripes
|  │    ●        ●
|  │              
|  │  Waves   Coral
|  │    ●        ●
|  │
|  │  Spirals  Moving
|  │    ●        ●
|  │
|  └─────────────────────────> F
   Chaotic
```

### Regions

- **Lower-left (low F, low k)**: Chaotic, unstable patterns
- **Upper-right (high F, high k)**: Uniform, no pattern formation
- **Middle diagonal**: Stable patterns (our presets)

## Stability Considerations

### CFL Condition

For numerical stability, the diffusion must satisfy:

```
D · dt / dx² < 0.5
```

With our default values (dt=1.0, dx=1.0, D≤0.21):
- Maximum safe D ≈ 0.25
- Our presets use Du=0.16, Dv=0.08 (well within limits)

### Mass Conservation

The total amount of U + V should remain approximately constant. Our implementation:
- Tracks mass conservation error
- Typical error < 0.001 (0.1%)
- Errors > 0.01 indicate potential instability

### Pattern Stability Metrics

**V Standard Deviation** indicates pattern type:
- **< 0.01**: Uniform (no pattern)
- **0.01 - 0.05**: Forming
- **0.05 - 0.15**: Stable pattern
- **0.15 - 0.30**: Complex/dynamic pattern
- **> 0.30**: Chaotic

## Tuning Guidelines

### To increase pattern complexity:
- Decrease F slightly (more feeding)
- Increase k slightly (more killing)
- Use larger grid size

### To stabilize patterns:
- Move toward middle of stable region
- Increase grid size
- Use longer initialization period

### To speed up formation:
- Use multiple initial spots
- Increase initial perturbation amplitude
- Start closer to pattern equilibrium

## Advanced Parameters

### Time Step (dt)

Default: 1.0

- **Smaller dt**: More stable, slower computation
- **Larger dt**: Faster computation, risk of instability
- Adjust if changing diffusion rates

### Spatial Step (dx)

Default: 1.0

- Affects scale of patterns
- Must satisfy CFL condition
- Usually kept at 1.0 for simplicity

### Diffusion Ratio (Du/Dv)

Default: 2.0 (Du=0.16, Dv=0.08)

- **Higher ratio**: Sharper pattern boundaries
- **Lower ratio**: Smoother, more diffuse patterns
- Ratio of 2.0 is standard for most patterns

## Parameter Discovery

To find new stable patterns:

1. **Start from known stable region**
2. **Make small changes** (±0.001 to ±0.005)
3. **Test for 5000+ cycles**
4. **Verify stability metrics**:
   - Mass conservation error < 0.01
   - No NaN/Infinity
   - V std in reasonable range

### Example Search

```python
from parameters import GrayScottParams
from physics_engine import GrayScottEngine

# Start from spots preset
base_F, base_k = 0.0367, 0.0649

# Search nearby
for dF in [-0.002, 0, 0.002]:
    for dk in [-0.002, 0, 0.002]:
        params = GrayScottParams(
            F=base_F + dF,
            k=base_k + dk,
            Du=0.16,
            Dv=0.08
        )
        # Test stability...
```

## Common Issues

### Pattern doesn't form

- **Cause**: Parameters in uniform region
- **Solution**: Move toward lower F or lower k

### Pattern becomes chaotic

- **Cause**: Parameters too extreme
- **Solution**: Move toward middle of stable region

### Pattern forms then disappears

- **Cause**: Slow drift toward uniform state
- **Solution**: Adjust F/k ratio, increase grid size

### Numerical instability

- **Cause**: CFL condition violated or extreme parameters
- **Solution**: Reduce dt, verify parameter ranges

## References

For deeper understanding:

1. **Pearson (1993)**: Original parameter space classification
2. **McGough & Riley (2004)**: Pattern formation mechanisms
3. **Lee et al. (1993)**: Laplacian computation methods

## Visualization Tips

- **V field**: Shows patterns best (primary visualization)
- **U field**: Shows inverse patterns (complementary)
- **Grayscale**: Best for scientific analysis
- **Color maps**: Better for presentations and aesthetics
- **Time-lapse**: Reveals formation dynamics

---

*For implementation details, see README.md*  
*For testing procedures, see test_stability.py*
