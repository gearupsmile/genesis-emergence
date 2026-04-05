# Zero-Fitness Issue - Diagnosis and Fix

## Problem
GenesisEngine.run_cycle() was logging `avg_fitness=0.00` for all generations, blocking Phase 3 success testing.

## Root Cause
**ID Mismatch Between fitness_scores and Population**

In the original `run_cycle()` flow:
1. Step 3: Calculate `fitness_scores` for current population
2. Step 4: Replace population with offspring (NEW agent IDs)
3. Step 5: Apply AIS culling
4. **Log statistics**: `fitness_scores.get(agent.id, 0.0)` for NEW population

The `fitness_scores` dict contained IDs from the OLD population, but `_log_statistics()` was iterating over the NEW population (offspring). Since the IDs didn't match, `fitness_scores.get(agent.id, 0.0)` returned the default value `0.0` for all agents.

## Diagnostic Process
Created `debug_fitness_issue.py` to trace agent state through the cycle:
- Confirmed agents ARE being developed (phenotype not None)
- Confirmed fitness calculation works correctly (formula produces 0.95-0.97)
- Identified that phenotypes are often empty lists (filtered expression)
- Discovered ID mismatch between fitness_scores dict and new population

## Solution
**Move statistics logging to BEFORE reproduction**

Modified `engine/genesis_engine.py`:
```python
# Step 3: Evaluation
fitness_scores = {agent.id: calculate_fitness(agent) for agent in self.population}

# Track statistics BEFORE reproduction (while IDs still match)
self._log_statistics(fitness_scores, [])  # No purging yet

# Step 4: Selection & Reproduction
# ... create offspring and replace population ...

# Step 5: AIS Culling
# ... purge agents ...

# Update statistics with purge count
if self.statistics:
    self.statistics[-1]['num_purged'] = len(purged_ids)
    self.statistics[-1]['population_size'] = len(self.population)  # After purging
```

## Results
**Before Fix:**
```
Gen 1: avg_fitness=0.00, max_fitness=0.00
Gen 2: avg_fitness=0.00, max_fitness=0.00
```

**After Fix:**
```
Gen 1: avg_fitness=1.25, max_fitness=3.88
Gen 2: avg_fitness=1.55, max_fitness=3.88
Gen 5: avg_fitness=3.68, max_fitness=4.81
Gen 19: avg_fitness=3.79 (evolved from 0.96!)
```

## Verification
- ✅ `test_bootstrap_evaluator.py`: All tests pass (6/6)
- ✅ `test_genesis_engine.py`: All tests pass (6/6)
- ✅ Fitness values are non-zero and realistic (0.96 to 4.81)
- ✅ Fitness evolves over generations (selection pressure working)
- ✅ No regressions in other functionality

## Additional Observations
Agents often have empty phenotypes (phenotype_length=0) due to filtered expression with linkage probabilities. This is expected behavior - the LinkageStructure's expression probabilities control which genes are expressed. When all groups fail their probability checks, the phenotype is an empty list, resulting in fitness ≈ 1.0 (baseline).

This creates interesting evolutionary dynamics where:
- Agents with more expressed genes have higher fitness
- Selection pressure favors agents with linkage structures that express genes
- Linkage evolution can adapt expression patterns

## Status
✅ **FIXED** - GenesisEngine now produces valid, non-zero fitness scores and demonstrates working evolution.
