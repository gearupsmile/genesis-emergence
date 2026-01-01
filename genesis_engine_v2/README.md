# Genesis Engine v2

**Phase 1.1: Foundational Genetic Architecture**

Genesis Engine v2 is a complete reboot focused on building robust artificial life from the ground up, starting with a proper genetic architecture that mirrors biological systems.

## Overview

This implementation introduces the **CodonTranslator** - a foundational module that translates triplet genetic codes (codons) into phenotypic instructions. The critical innovation is **genetic code degeneracy**, where multiple different codons map to the same instruction, providing mutational robustness similar to biological DNA.

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

## Project Structure

```
genesis_engine_v2/
├── engine/
│   ├── __init__.py
│   └── codon_translator.py    # Core genetic translation system
├── test_codon_translator.py   # Comprehensive test suite
└── README.md                   # This file
```

## Quick Start

### Running Tests

Verify the CodonTranslator implementation:

```bash
cd genesis_engine_v2
python test_codon_translator.py
```

Expected output:
```
============================================================
CodonTranslator Test Suite
Testing Phase 1.1: Foundational Genetic Architecture
============================================================

Test 1: Basic Translation
  ✓ Agent translation works
  ✓ World translation works
  PASSED

Test 2: Degeneracy Verification (CRITICAL)
  Agent Table Degeneracy:
    ✓ 'AAA' and 'AAT' both produce 'move_forward'
    ✓ 'ACA' and 'ACT' both produce 'turn_left'
    ...
  PASSED

...

✓ ALL TESTS PASSED!
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
