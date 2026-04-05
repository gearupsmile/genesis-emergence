"""
Test Suite for KernelAgent and KernelWorld

This test suite verifies the foundational entity classes, with emphasis on:
1. State sovereignty (entities own their state)
2. CodonTranslator integration (phenotype/physics development)
3. AIS integration (dictionary conversion and lifecycle management)
4. Round-trip conversion integrity
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import the engine module
sys.path.insert(0, str(Path(__file__).parent))

from engine.kernel_agent import KernelAgent
from engine.kernel_world import KernelWorld
from engine.codon_translator import CodonTranslator
from engine.ais import ArtificialImmuneSystem


def test_kernel_agent_creation():
    """Test KernelAgent initialization."""
    print("Test 1: KernelAgent Creation")
    
    agent = KernelAgent('AAAAATACA')
    
    assert agent.id is not None, "Agent should have an ID"
    assert agent.genotype == 'AAAAATACA', "Genotype should be stored"
    assert agent.relevance_score == 1.0, "Initial relevance should be 1.0"
    assert agent.age == 0, "Initial age should be 0"
    assert agent.phenotype is None, "Phenotype should be None until developed"
    print("  [PASS] Agent created with correct initial state")
    
    # Test with custom ID
    agent2 = KernelAgent('AAAAATACA', agent_id='custom-id')
    assert agent2.id == 'custom-id', "Custom ID should be used"
    print("  [PASS] Custom ID works")
    
    # Test invalid genotype
    try:
        agent3 = KernelAgent('AAAA')  # Length 4, not multiple of 3
        assert False, "Should raise ValueError for invalid genotype"
    except ValueError:
        print("  [PASS] Invalid genotype rejected")
    
    print("  PASSED\n")


def test_kernel_world_creation():
    """Test KernelWorld initialization."""
    print("Test 2: KernelWorld Creation")
    
    world = KernelWorld('GAAGCTGGA')
    
    assert world.id is not None, "World should have an ID"
    assert world.genotype == 'GAAGCTGGA', "Genotype should be stored"
    assert world.relevance_score == 1.0, "Initial relevance should be 1.0"
    assert world.age == 0, "Initial age should be 0"
    assert world.physics_rules is None, "Physics should be None until developed"
    print("  [PASS] World created with correct initial state")
    
    # Test with custom ID
    world2 = KernelWorld('GAAGCTGGA', world_id='world-123')
    assert world2.id == 'world-123', "Custom ID should be used"
    print("  [PASS] Custom ID works")
    
    # Test invalid genotype
    try:
        world3 = KernelWorld('GAAG')  # Length 4, not multiple of 3
        assert False, "Should raise ValueError for invalid genotype"
    except ValueError:
        print("  [PASS] Invalid genotype rejected")
    
    print("  PASSED\n")


def test_phenotype_development():
    """Test agent phenotype development using CodonTranslator."""
    print("Test 3: Phenotype Development")
    
    translator = CodonTranslator()
    agent = KernelAgent('AAAAATACA')
    
    phenotype = agent.develop(translator)
    
    assert phenotype is not None, "Phenotype should be developed"
    assert agent.phenotype == phenotype, "Phenotype should be stored"
    assert phenotype == ['move_forward', 'move_forward', 'turn_left'], \
        f"Expected specific phenotype, got {phenotype}"
    print(f"  [PASS] Phenotype developed: {phenotype}")
    
    print("  PASSED\n")


def test_physics_development():
    """Test world physics development using CodonTranslator."""
    print("Test 4: Physics Development")
    
    translator = CodonTranslator()
    world = KernelWorld('GAAGCTGGA')
    
    physics = world.develop_physics(translator)
    
    assert physics is not None, "Physics should be developed"
    assert world.physics_rules == physics, "Physics should be stored"
    assert physics == ['increase_resources', 'decrease_resources', 'raise_temperature'], \
        f"Expected specific physics, got {physics}"
    print(f"  [PASS] Physics developed: {physics}")
    
    print("  PASSED\n")


def test_dictionary_conversion():
    """Test to_dict() and from_dict() methods."""
    print("Test 5: Dictionary Conversion")
    
    # Test agent
    agent = KernelAgent('AAAAATACA', agent_id='agent-123')
    agent.age = 5
    agent.relevance_score = 0.8
    
    agent_dict = agent.to_dict()
    assert agent_dict == {'id': 'agent-123', 'relevance_score': 0.8, 'age': 5}, \
        f"Unexpected dict: {agent_dict}"
    print(f"  [PASS] Agent to_dict(): {agent_dict}")
    
    # Reconstruct agent
    agent2 = KernelAgent.from_dict(agent_dict, 'AAAAATACA')
    assert agent2.id == 'agent-123', "ID should match"
    assert agent2.age == 5, "Age should match"
    assert agent2.relevance_score == 0.8, "Relevance should match"
    assert agent2.genotype == 'AAAAATACA', "Genotype should match"
    print("  [PASS] Agent from_dict() works")
    
    # Test world
    world = KernelWorld('GAAGCTGGA', world_id='world-456')
    world.age = 10
    world.relevance_score = 0.6
    
    world_dict = world.to_dict()
    assert world_dict == {'id': 'world-456', 'relevance_score': 0.6, 'age': 10}, \
        f"Unexpected dict: {world_dict}"
    print(f"  [PASS] World to_dict(): {world_dict}")
    
    # Reconstruct world
    world2 = KernelWorld.from_dict(world_dict, 'GAAGCTGGA')
    assert world2.id == 'world-456', "ID should match"
    assert world2.age == 10, "Age should match"
    assert world2.relevance_score == 0.6, "Relevance should match"
    print("  [PASS] World from_dict() works")
    
    print("  PASSED\n")


def test_ais_integration():
    """
    CRITICAL TEST: Simulate 10 AIS cycles with agent and world,
    verify their scores decay correctly.
    """
    print("Test 6: AIS Integration (CRITICAL)")
    
    translator = CodonTranslator()
    ais = ArtificialImmuneSystem(expiry_cycle=5, decay_rate=0.1, viability_threshold=0.1)
    
    # Create entities
    agent = KernelAgent('AAAAATACA')
    world = KernelWorld('GAAGCTGGA')
    
    # Develop phenotypes
    agent.develop(translator)
    world.develop_physics(translator)
    print(f"  Created agent: {agent}")
    print(f"  Created world: {world}")
    
    # Convert to dictionaries for AIS
    entities = [agent.to_dict(), world.to_dict()]
    
    print(f"  Initial entities: {len(entities)}")
    
    # Simulate 10 cycles
    for cycle in range(10):
        entities, purged = ais.apply_cycle(entities)
        if cycle == 0:
            print(f"  After cycle {cycle + 1}: age={entities[0]['age']}, score={entities[0]['relevance_score']:.2f}")
        if cycle == 4:
            print(f"  After cycle {cycle + 1}: age={entities[0]['age']}, score={entities[0]['relevance_score']:.3f} (decay starts)")
        if cycle == 9:
            print(f"  After cycle {cycle + 1}: age={entities[0]['age']}, score={entities[0]['relevance_score']:.2f}")
    
    # Verify both survived
    assert len(entities) == 2, f"Both should survive, got {len(entities)}"
    print(f"  [PASS] Both entities survived 10 cycles")
    
    # Verify ages
    assert entities[0]['age'] == 10, f"Expected age 10, got {entities[0]['age']}"
    assert entities[1]['age'] == 10, f"Expected age 10, got {entities[1]['age']}"
    print(f"  [PASS] Ages incremented correctly: {entities[0]['age']}")
    
    # Verify decay
    # Cycle 0: age becomes 1, no decay (age < 5)
    # Cycle 1: age becomes 2, no decay
    # Cycle 2: age becomes 3, no decay
    # Cycle 3: age becomes 4, no decay
    # Cycle 4: age becomes 5, decay starts (age >= 5), score = 0.9
    # Cycle 5: age becomes 6, decay, score = 0.8
    # Cycle 6: age becomes 7, decay, score = 0.7
    # Cycle 7: age becomes 8, decay, score = 0.6
    # Cycle 8: age becomes 9, decay, score = 0.5
    # Cycle 9: age becomes 10, decay, score = 0.4
    # Total: 6 decay cycles (cycles 4-9)
    # Expected: 1.0 - 6*0.1 = 0.4
    expected_score = 0.4
    assert abs(entities[0]['relevance_score'] - expected_score) < 0.01, \
        f"Expected score ~{expected_score}, got {entities[0]['relevance_score']}"
    assert abs(entities[1]['relevance_score'] - expected_score) < 0.01, \
        f"Expected score ~{expected_score}, got {entities[1]['relevance_score']}"
    print(f"  [PASS] Relevance scores decayed correctly: {entities[0]['relevance_score']:.2f}")
    
    # Update original entities from dictionaries
    agent.update_from_dict(entities[0])
    world.update_from_dict(entities[1])
    
    assert agent.age == 10, "Agent age should be updated"
    assert abs(agent.relevance_score - 0.4) < 0.01, "Agent score should be updated"
    print(f"  [PASS] update_from_dict() works: {agent}")
    
    print("  PASSED\n")


def test_state_sovereignty():
    """Verify entities own their state."""
    print("Test 7: State Sovereignty")
    
    agent = KernelAgent('AAAAATACA')
    world = KernelWorld('GAAGCTGGA')
    
    # Verify entities own their attributes
    assert hasattr(agent, 'id'), "Agent should own id"
    assert hasattr(agent, 'genotype'), "Agent should own genotype"
    assert hasattr(agent, 'relevance_score'), "Agent should own relevance_score"
    assert hasattr(agent, 'age'), "Agent should own age"
    assert hasattr(agent, 'phenotype'), "Agent should own phenotype"
    print("  [PASS] Agent owns its state")
    
    assert hasattr(world, 'id'), "World should own id"
    assert hasattr(world, 'genotype'), "World should own genotype"
    assert hasattr(world, 'relevance_score'), "World should own relevance_score"
    assert hasattr(world, 'age'), "World should own age"
    assert hasattr(world, 'physics_rules'), "World should own physics_rules"
    print("  [PASS] World owns its state")
    
    # Verify state can be modified
    agent.relevance_score = 0.7
    agent.age = 15
    assert agent.relevance_score == 0.7, "State should be mutable"
    assert agent.age == 15, "State should be mutable"
    print("  [PASS] Entity state is mutable")
    
    print("  PASSED\n")


def test_round_trip_conversion():
    """Test round-trip conversion preserves data."""
    print("Test 8: Round-trip Conversion")
    
    translator = CodonTranslator()
    
    # Create and develop agent
    agent1 = KernelAgent('AAAAATACA', agent_id='test-agent')
    phenotype = agent1.develop(translator)
    agent1.age = 7
    agent1.relevance_score = 0.75
    
    # Convert to dict and back
    agent_dict = agent1.to_dict()
    agent2 = KernelAgent.from_dict(agent_dict, agent1.genotype, phenotype)
    
    # Verify all data preserved
    assert agent2.id == agent1.id, "ID should match"
    assert agent2.genotype == agent1.genotype, "Genotype should match"
    assert agent2.age == agent1.age, "Age should match"
    assert agent2.relevance_score == agent1.relevance_score, "Relevance should match"
    assert agent2.phenotype == agent1.phenotype, "Phenotype should match"
    print("  [PASS] Agent round-trip preserves all data")
    
    # Same for world
    world1 = KernelWorld('GAAGCTGGA', world_id='test-world')
    physics = world1.develop_physics(translator)
    world1.age = 12
    world1.relevance_score = 0.65
    
    world_dict = world1.to_dict()
    world2 = KernelWorld.from_dict(world_dict, world1.genotype, physics)
    
    assert world2.id == world1.id, "ID should match"
    assert world2.genotype == world1.genotype, "Genotype should match"
    assert world2.age == world1.age, "Age should match"
    assert world2.relevance_score == world1.relevance_score, "Relevance should match"
    assert world2.physics_rules == world1.physics_rules, "Physics should match"
    print("  [PASS] World round-trip preserves all data")
    
    print("  PASSED\n")


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("KernelAgent and KernelWorld Test Suite")
    print("Testing Phase 1.3: Foundational Entity Classes")
    print("=" * 60)
    print()
    
    tests = [
        test_kernel_agent_creation,
        test_kernel_world_creation,
        test_phenotype_development,
        test_physics_development,
        test_dictionary_conversion,
        test_ais_integration,
        test_state_sovereignty,
        test_round_trip_conversion,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}\n")
            failed += 1
    
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n[SUCCESS] ALL TESTS PASSED!")
        print("\nKernel Entities Verification Summary:")
        print("  - KernelAgent and KernelWorld created successfully")
        print("  - Entities own their state (id, genotype, relevance_score, age)")
        print("  - CodonTranslator integration works (develop/develop_physics)")
        print("  - AIS integration verified (10-cycle simulation)")
        print("  - Dictionary conversion preserves data integrity")
        print("\nPhase 1.3 (Foundational Entity Classes) is COMPLETE!")
        return 0
    else:
        print(f"\n[FAILED] {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
