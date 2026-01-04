# Evolutionary Constraint Verification

## Overview

The Genesis Engine v2 now includes **mandatory pre-flight verification** of critical evolutionary constraints before any major experiment runs. This system prevents bugs in core evolutionary mechanics from reaching production experiments.

## Why Verification is Critical

During development, we discovered that the quadratic metabolic cost formula was correctly calculated but **not applied during selection**. This allowed genomes to bloat to 413 genes, causing a 68% performance degradation. The bug went undetected until after a 3-hour experiment run.

**The verification system prevents this class of bug.**

## Automated Checks

The `ConstraintChecker` class (`engine/verification/constraint_checker.py`) performs the following checks:

### 1. Metabolic Cost Application (CRITICAL)
- **What it checks**: Verifies that metabolic cost penalty is applied during tournament selection
- **How**: Creates mock population with short (5 genes) and bloated (50 genes) genomes, runs selection 100 times
- **Pass criteria**: Short genomes must be selected >1.5× more often than bloated genomes
- **Why critical**: Without this, genome bloat destroys performance and invalidates experiments

### 2. AIS Purging
- **What it checks**: Confirms Artificial Immune System removes low-relevance agents
- **How**: Creates agents with low relevance scores beyond expiry age, runs purge
- **Pass criteria**: At least some agents must be purged

### 3. Pareto Dominance
- **What it checks**: Validates Pareto ranking algorithm correctly identifies dominated agents
- **How**: Creates test population with known dominance relationships
- **Pass criteria**: Dominated agents must have worse (higher) rank

### 4. Linkage Inheritance
- **What it checks**: Confirms genes in linkage groups are properly associated
- **How**: Creates linkage structure and verifies group membership
- **Pass criteria**: Genes added to same group must remain together

## Usage

### Running Experiments with Verification (Default)

```bash
# Verification runs automatically
python scripts/launch_final_probe.py

# Dry run with verification
python scripts/launch_final_probe.py --dry-run
```

### Skipping Verification (NOT RECOMMENDED)

```bash
# Only use for debugging/testing
python scripts/launch_final_probe.py --skip-verification
```

## Verification Report

Each run generates `verification_report.log` in the run directory:

```
======================================================================
EVOLUTIONARY CONSTRAINT VERIFICATION REPORT
======================================================================
Timestamp: 2026-01-04T21:45:00

[PASS] metabolic_cost
  PASS - Short genomes selected 78/100 times, bloated 22/100 times 
  (ratio: 3.55). Cost penalty is applied.

[PASS] ais_purging
  PASS - AIS purged 5/5 low-relevance agents

[PASS] pareto_dominance
  PASS - Pareto ranking correct (dominated agent has worse rank)

[PASS] linkage_inheritance
  PASS - Linkage groups correctly maintain gene associations

======================================================================
Overall: PASSED
======================================================================
```

## What Happens on Failure

If any check fails, the experiment **aborts immediately** with a clear error:

```
======================================================================
CRITICAL: EVOLUTIONARY CONSTRAINT VIOLATED
======================================================================

One or more critical evolutionary constraints failed verification.
The experiment CANNOT proceed until these issues are resolved.

See detailed report: runs/deep_probe_200k_20260104_214500/logs/verification_report.log
```

## Testing the Verification System

To verify the system works, you can intentionally break a constraint:

```python
# In bootstrap_evaluator.py, comment out the cost penalty:
# winner = max(tournament, key=get_penalized_score)
winner = max(tournament, key=lambda agent: fitness_scores.get(agent.id, 0.0))
```

Then run:
```bash
python scripts/launch_final_probe.py --dry-run
```

Expected output:
```
[FAIL] metabolic_cost
  FAIL - Selection ratio 1.02 too low. Expected > 1.5 based on cost 
  difference. Metabolic cost penalty NOT being applied!

CRITICAL: EVOLUTIONARY CONSTRAINT VIOLATED
```

## Design Philosophy

**"Trust, but verify."** 

The verification system embodies defensive programming:
1. **Automated**: No manual testing required
2. **Mandatory**: Cannot be bypassed without explicit flag
3. **Fast**: Completes in <10 seconds
4. **Comprehensive**: Covers all critical evolutionary mechanics
5. **Actionable**: Clear error messages guide debugging

This ensures that core evolutionary physics are correctly wired before investing hours in long-running experiments.
