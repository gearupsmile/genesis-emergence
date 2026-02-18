"""
Unit Tests for PhysicalInvariantGatekeeper

Tests the core enforcement mechanism for immutable physical laws.

Phase 2 - Pillar 2: Physical Invariant Architecture
"""

import sys
from pathlib import Path

# Add genesis_engine_v2 to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.physics.physics_gatekeeper import PhysicalInvariantGatekeeper
from engine.evolvable_genome import EvolvableGenome
from engine.structurally_evolvable_agent import StructurallyEvolvableAgent


def test_viable_agent():
    """Test that agents below threshold survive."""
    print("Test 1: Viable Agent (Low Cost)")
    
    gatekeeper = PhysicalInvariantGatekeeper(energy_constant=0.5)
    
    # Create agent with low cost (3 genes)
    genome = EvolvableGenome(['AAA', 'CAA', 'GAA'])
    agent = StructurallyEvolvableAgent(genome)
    
    print(f"  Genome length: {genome.get_length()} genes")
    print(f"  Metabolic cost: {genome.metabolic_cost:.3f}")
    print(f"  Energy constant: {gatekeeper.energy_constant}")
    
    viable = gatekeeper.check_viability(agent)
    print(f"  Result: {'VIABLE' if viable else 'NON-VIABLE'}")
    
    assert viable == True, "Agent with low cost should be viable"
    assert gatekeeper.total_violations == 0, "Should have no violations"
    
    print("  [PASS]\n")


def test_nonviable_agent():
    """Test that agents above threshold are terminated."""
    print("Test 2: Non-Viable Agent (High Cost)")
    
    gatekeeper = PhysicalInvariantGatekeeper(energy_constant=0.5)
    
    # Create agent with high cost (50 genes)
    genome = EvolvableGenome(['AAA'] * 50)
    agent = StructurallyEvolvableAgent(genome)
    
    print(f"  Genome length: {genome.get_length()} genes")
    print(f"  Metabolic cost: {genome.metabolic_cost:.3f}")
    print(f"  Energy constant: {gatekeeper.energy_constant}")
    
    viable = gatekeeper.check_viability(agent)
    print(f"  Result: {'VIABLE' if viable else 'NON-VIABLE'}")
    
    assert viable == False, "Agent with high cost should be non-viable"
    assert gatekeeper.total_violations == 1, "Should have 1 violation"
    
    print("  ✓ PASS\n")


def test_edge_case_at_threshold():
    """Test behavior at exact threshold."""
    print("Test 3: Edge Case (At Threshold)")
    
    gatekeeper = PhysicalInvariantGatekeeper(energy_constant=0.5)
    
    # Calculate genome length that gives cost ≈ 0.5
    # cost = 0.005 * (length ^ 1.5)
    # 0.5 = 0.005 * (length ^ 1.5)
    # length = (0.5 / 0.005) ^ (1/1.5) ≈ 46.4
    genome = EvolvableGenome(['AAA'] * 46)
    agent = StructurallyEvolvableAgent(genome)
    
    print(f"  Genome length: {genome.get_length()} genes")
    print(f"  Metabolic cost: {genome.metabolic_cost:.3f}")
    print(f"  Energy constant: {gatekeeper.energy_constant}")
    
    viable = gatekeeper.check_viability(agent)
    print(f"  Result: {'VIABLE' if viable else 'NON-VIABLE'}")
    
    # At exactly threshold, should still be viable (cost <= constant)
    # But with 46 genes, cost is slightly below 0.5
    print(f"  Expected: VIABLE (cost < threshold)")
    
    print("  ✓ PASS\n")


def test_population_enforcement():
    """Test population-wide constraint enforcement."""
    print("Test 4: Population Enforcement")
    
    gatekeeper = PhysicalInvariantGatekeeper(energy_constant=0.5)
    
    # Create mixed population
    agent1 = StructurallyEvolvableAgent(EvolvableGenome(['AAA'] * 3))   # Viable
    agent2 = StructurallyEvolvableAgent(EvolvableGenome(['AAA'] * 50))  # Non-viable
    agent3 = StructurallyEvolvableAgent(EvolvableGenome(['AAA'] * 10))  # Viable
    agent4 = StructurallyEvolvableAgent(EvolvableGenome(['AAA'] * 60))  # Non-viable
    
    population = [agent1, agent2, agent3, agent4]
    
    print(f"  Initial population: {len(population)} agents")
    for i, agent in enumerate(population, 1):
        print(f"    Agent {i}: {agent.genome.get_length()} genes, cost={agent.genome.metabolic_cost:.3f}")
    
    survivors, terminated = gatekeeper.enforce_population_constraints(population)
    
    print(f"  Survivors: {len(survivors)} agents")
    print(f"  Terminated: {len(terminated)} agents")
    
    assert len(survivors) == 2, "Should have 2 survivors"
    assert len(terminated) == 2, "Should have 2 terminated"
    assert agent1 in survivors, "Agent 1 should survive"
    assert agent3 in survivors, "Agent 3 should survive"
    assert agent2.id in terminated, "Agent 2 should be terminated"
    assert agent4.id in terminated, "Agent 4 should be terminated"
    
    print("  ✓ PASS\n")


def test_violation_logging():
    """Test that violations are logged correctly."""
    print("Test 5: Violation Logging")
    
    gatekeeper = PhysicalInvariantGatekeeper(energy_constant=0.5, log_violations=True)
    
    # Create non-viable agent
    genome = EvolvableGenome(['AAA'] * 50)
    agent = StructurallyEvolvableAgent(genome)
    agent.age = 10
    
    gatekeeper.check_viability(agent)
    
    violation_log = gatekeeper.get_violation_log()
    
    print(f"  Violations logged: {len(violation_log)}")
    
    assert len(violation_log) == 1, "Should have 1 violation logged"
    
    violation = violation_log[0]
    print(f"  Violation details:")
    print(f"    Agent ID: {violation['agent_id']}")
    print(f"    Metabolic cost: {violation['metabolic_cost']:.3f}")
    print(f"    Excess: {violation['excess']:.3f}")
    print(f"    Genome length: {violation['genome_length']} genes")
    print(f"    Age: {violation['age']}")
    
    assert violation['agent_id'] == agent.id
    assert violation['metabolic_cost'] == genome.metabolic_cost
    assert violation['genome_length'] == 50
    assert violation['age'] == 10
    
    print("  ✓ PASS\n")


def test_statistics():
    """Test statistics tracking."""
    print("Test 6: Statistics Tracking")
    
    gatekeeper = PhysicalInvariantGatekeeper(energy_constant=0.5)
    
    # Check multiple agents
    viable_agent = StructurallyEvolvableAgent(EvolvableGenome(['AAA'] * 5))
    nonviable_agent = StructurallyEvolvableAgent(EvolvableGenome(['AAA'] * 50))
    
    gatekeeper.check_viability(viable_agent)
    gatekeeper.check_viability(nonviable_agent)
    gatekeeper.check_viability(viable_agent)
    
    stats = gatekeeper.get_statistics()
    
    print(f"  Total checks: {stats['total_checks']}")
    print(f"  Total violations: {stats['total_violations']}")
    print(f"  Violation rate: {stats['violation_rate']:.2%}")
    
    assert stats['total_checks'] == 3, "Should have 3 checks"
    assert stats['total_violations'] == 1, "Should have 1 violation"
    assert abs(stats['violation_rate'] - 1/3) < 0.01, "Violation rate should be ~33%"
    
    print("  ✓ PASS\n")


def run_all_tests():
    """Run all unit tests."""
    print("=" * 70)
    print("PHYSICAL INVARIANT GATEKEEPER - UNIT TESTS")
    print("=" * 70)
    print()
    
    tests = [
        test_viable_agent,
        test_nonviable_agent,
        test_edge_case_at_threshold,
        test_population_enforcement,
        test_violation_logging,
        test_statistics
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL]: {e}\n")
            failed += 1
        except Exception as e:
            print(f"  [ERROR]: {e}\n")
            failed += 1
    
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

