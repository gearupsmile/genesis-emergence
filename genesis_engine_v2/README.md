# Genesis Engine v2

**Phases 1.1, 1.2 & 1.3: Complete Foundational Architecture**

Genesis Engine v2 is a complete reboot focused on building robust artificial life from the ground up, with genetic architecture, universal lifecycle laws, and foundational entity classes.

## Overview

This implementation introduces three foundational systems:

1. **CodonTranslator** (Phase 1.1): Translates triplet genetic codes (codons) into phenotypic instructions with **genetic code degeneracy** for mutational robustness

2. **ArtificialImmuneSystem** (Phase 1.2): A stateless universal law that manages entity lifecycles through forgetting and purging rules

3. **KernelAgent & KernelWorld** (Phase 1.3): Foundational entity classes that own their state, integrate with CodonTranslator for phenotype development, and work seamlessly with AIS

## Key Features

### Genetic Code Degeneracy

Just like biological genetic codes, our system implements degeneracy:
- Multiple codons produce the same phenotypic outcome
- Single-point mutations don't always change the phenotype
- Provides evolutionary stability while allowing gradual adaptation

**Example:**
```python
translator = CodonTranslator()
translator.translate_agent('AAA')  # Returns: 'move_forward'
translator.translate_agent('AAT')  # Returns: 'move_forward' (degenerate)
```

### Dual Translation Tables

- **Agent Table**: Maps codons to agent behaviors (movement, energy management, reproduction, sensing)
- **World Table**: Maps codons to environmental parameters (resources, temperature, space, mutation rates)

### Current Implementation

- **12 codons** in agent_table mapping to **6 unique instructions** (2:1 degeneracy)
- **12 codons** in world_table mapping to **6 unique instructions** (2:1 degeneracy)
- Extensible design for future genetic complexity

### Artificial Immune System (Stateless Architecture)

The AIS is a **stateless universal law** that applies forgetting and purging rules:
- **No internal state**: AIS stores only immutable law parameters
- **Entity sovereignty**: Each entity owns its `relevance_score` and `age`
- **Pure function**: `apply_cycle()` is deterministic with no side effects

**Forgetting Rule**: After `expiry_cycle` (default: 1000), relevance scores decay by `decay_rate` (default: 0.001) each cycle

**Purging Rule**: Entities with `relevance_score < viability_threshold` (default: 0.1) are removed

**Example:**
```python
ais = ArtificialImmuneSystem()

# Entities own their state
entities = [
    {'id': 'agent_1', 'relevance_score': 1.0, 'age': 0},
    {'id': 'agent_2', 'relevance_score': 1.0, 'age': 0},
]

# Apply universal law
updated_entities, purged_ids = ais.apply_cycle(entities)
# updated_entities: entities with incremented age and decayed scores
# purged_ids: IDs of entities that fell below viability threshold
```

### KernelAgent and KernelWorld (State Sovereignty)

Foundational entity classes that own their state and integrate with the system:
- **State ownership**: Each entity owns `id`, `genotype`, `relevance_score`, `age`
- **CodonTranslator integration**: Develop phenotypes/physics from genotypes
- **AIS compatibility**: Dictionary conversion for lifecycle management

**Example:**
```python
from engine import KernelAgent, KernelWorld, CodonTranslator, ArtificialImmuneSystem

translator = CodonTranslator()
ais = ArtificialImmuneSystem()

# Create entities
agent = KernelAgent('AAAAATACA')
world = KernelWorld('GAAGCTGGA')

# Develop phenotypes
phenotype = agent.develop(translator)  # ['move_forward', 'move_forward', 'turn_left']
physics = world.develop_physics(translator)  # ['increase_resources', ...]

# AIS integration
entities = [agent.to_dict(), world.to_dict()]
updated, purged = ais.apply_cycle(entities)
agent.update_from_dict(updated[0])  # Update agent state
```

## Project Structure

```
genesis_engine_v2/
├── engine/
│   ├── __init__.py
│   ├── codon_translator.py    # Phase 1.1: Genetic translation
│   ├── ais.py                  # Phase 1.2: Lifecycle management
│   ├── kernel_agent.py         # Phase 1.3: Agent entities
│   └── kernel_world.py         # Phase 1.3: World entities
├── test_codon_translator.py   # CodonTranslator test suite
├── test_ais.py                 # AIS test suite
├── test_kernel_entities.py    # KernelAgent/World test suite
└── README.md                   # This file
```

## Quick Start

### Running Tests

**CodonTranslator (Phase 1.1):**
```bash
cd genesis_engine_v2
python test_codon_translator.py
```

**ArtificialImmuneSystem (Phase 1.2):**
```bash
cd genesis_engine_v2
python test_ais.py
```

Expected output for AIS:
```
============================================================
Artificial Immune System Test Suite
Testing Phase 1.2: Stateless Universal Law
============================================================

Test 4: Mass Purging of 100 Inert Entities (CRITICAL)
  Expected inert entity lifetime: 1900 cycles
  Created 100 inert entities
  [PASS] All 100 entities were purged
  [PASS] No entities remain after 2000 cycles
  ...

[SUCCESS] ALL TESTS PASSED!
```

### Using the CodonTranslator

```python
from engine import CodonTranslator

# Create translator
translator = CodonTranslator()

# Translate individual codons
instruction = translator.translate_agent('AAA')  # 'move_forward'

# Translate sequences
sequence = 'AAAAATACA'
instructions = translator.translate_sequence(sequence, 'agent')
# Returns: ['move_forward', 'move_forward', 'turn_left']

# Examine degeneracy
codons = translator.get_degenerate_codons('move_forward', 'agent')
# Returns: ['AAA', 'AAT']

# Get statistics
stats = translator.get_degeneracy_stats()
# Returns detailed degeneracy metrics for both tables
```

## Design Philosophy

### Why Degeneracy?

Degeneracy is a fundamental feature of biological genetic codes that provides:

1. **Mutational Robustness**: Not every mutation changes the phenotype
2. **Evolvability**: Allows neutral mutations to accumulate, creating genetic diversity
3. **Stability**: Reduces the impact of random genetic drift
4. **Gradual Evolution**: Enables smooth fitness landscapes rather than abrupt changes

### Future Phases

This is Phase 1.1 of a larger blueprint. Future phases will include:

- **Phase 1.2**: Genome structure and gene expression
- **Phase 1.3**: Mutation mechanisms with realistic rates
- **Phase 2.x**: Agent behaviors and world physics
- **Phase 3.x**: Evolution and selection mechanisms
- **Phase 4.x**: Emergence of complexity

## Testing

The test suite (`test_codon_translator.py`) includes:

1. **Basic Translation**: Verifies core translation functionality
2. **Degeneracy Verification**: Critical test ensuring multiple codons produce identical outputs
3. **Sequence Translation**: Tests translation of codon sequences
4. **Invalid Codon Handling**: Ensures robust error handling
5. **Degenerate Codon Retrieval**: Tests reverse lookup functionality
6. **Degeneracy Statistics**: Validates statistical properties
7. **Case Insensitivity**: Ensures flexible input handling

## Technical Details

### Codon Format

- **Length**: Exactly 3 characters
- **Alphabet**: A, C, G, T (case-insensitive)
- **Example**: 'AAA', 'GCT', 'TAA'

### Agent Instructions

Current agent behaviors:
- `move_forward` - Forward movement
- `turn_left` - Rotation
- `consume_energy` - Energy intake
- `store_energy` - Energy storage
- `reproduce` - Reproduction trigger
- `sense_environment` - Environmental sensing

### World Instructions

Current world parameters:
- `increase_resources` / `decrease_resources` - Resource availability
- `raise_temperature` / `lower_temperature` - Environmental conditions
- `expand_space` - Spatial parameters
- `increase_mutation` - Mutation rate control

## Version History

- **v2.0.0** (2026-01-01): Initial implementation with CodonTranslator and degeneracy support

## Related

See `../genesis_engine_v1/` for the previous implementation focusing on reaction-diffusion physics and population dynamics.

---

**Genesis Engine v2** - Building artificial life from the genetic code up.
