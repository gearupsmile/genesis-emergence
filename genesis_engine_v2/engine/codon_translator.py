"""
CodonTranslator - Core Genetic Architecture for Genesis Engine v2

This module implements the foundational genetic translation system that maps
triplet genetic codes (codons) to phenotypic instructions. A critical feature
is degeneracy - multiple different codons map to the same instruction to ensure
mutational robustness, similar to biological genetic codes.

Phase 1.1: Foundational Genetic Architecture
"""


class CodonTranslator:
    """
    Translates triplet genetic codes (codons) to phenotypic instructions.
    
    Features:
    - Degeneracy: Multiple codons map to the same instruction for mutational robustness
    - Separate tables for agent behaviors and world/environment parameters
    - Extensible design for future genetic complexity
    """
    
    def __init__(self):
        """
        Initialize the CodonTranslator with degenerate codon tables.
        
        Degeneracy ensures that single-point mutations don't always change
        the phenotype, providing evolutionary stability while allowing for
        gradual adaptation.
        """
        
        # Agent behavior table - maps codons to agent actions/traits
        # Note: Multiple codons map to the same instruction (degeneracy)
        self.agent_table = {
            # Movement instructions (4 codons -> 2 instructions)
            'AAA': 'move_forward',
            'AAT': 'move_forward',      # Degenerate with AAA
            'ACA': 'turn_left',
            'ACT': 'turn_left',          # Degenerate with ACA
            
            # Energy management (4 codons -> 2 instructions)
            'AGA': 'consume_energy',
            'AGT': 'consume_energy',     # Degenerate with AGA
            'ATA': 'store_energy',
            'ATT': 'store_energy',       # Degenerate with ATA
            
            # Reproduction (2 codons -> 1 instruction)
            'CAA': 'reproduce',
            'CAT': 'reproduce',          # Degenerate with CAA
            
            # Sensing (2 codons -> 1 instruction)
            'CCA': 'sense_environment',
            'CCT': 'sense_environment',  # Degenerate with CCA
        }
        
        # World/environment table - maps codons to world parameters
        # Note: Multiple codons map to the same instruction (degeneracy)
        self.world_table = {
            # Resource distribution (4 codons -> 2 instructions)
            'GAA': 'increase_resources',
            'GAT': 'increase_resources',     # Degenerate with GAA
            'GCA': 'decrease_resources',
            'GCT': 'decrease_resources',     # Degenerate with GCA
            
            # Environmental conditions (4 codons -> 2 instructions)
            'GGA': 'raise_temperature',
            'GGT': 'raise_temperature',      # Degenerate with GGA
            'GTA': 'lower_temperature',
            'GTT': 'lower_temperature',      # Degenerate with GTA
            
            # Spatial parameters (2 codons -> 1 instruction)
            'TAA': 'expand_space',
            'TAT': 'expand_space',           # Degenerate with TAA
            
            # Mutation rate (2 codons -> 1 instruction)
            'TCA': 'increase_mutation',
            'TCT': 'increase_mutation',      # Degenerate with TCA
        }
    
    def translate_agent(self, codon):
        """
        Translate a codon using the agent behavior table.
        
        Args:
            codon (str): A three-character genetic code (e.g., 'AAA')
            
        Returns:
            str: The phenotypic instruction, or None if codon is invalid
            
        Example:
            >>> translator = CodonTranslator()
            >>> translator.translate_agent('AAA')
            'move_forward'
            >>> translator.translate_agent('AAT')  # Degenerate codon
            'move_forward'
        """
        if not self._validate_codon(codon):
            return None
        return self.agent_table.get(codon.upper())
    
    def translate_world(self, codon):
        """
        Translate a codon using the world/environment table.
        
        Args:
            codon (str): A three-character genetic code (e.g., 'GAA')
            
        Returns:
            str: The phenotypic instruction, or None if codon is invalid
            
        Example:
            >>> translator = CodonTranslator()
            >>> translator.translate_world('GAA')
            'increase_resources'
            >>> translator.translate_world('GAT')  # Degenerate codon
            'increase_resources'
        """
        if not self._validate_codon(codon):
            return None
        return self.world_table.get(codon.upper())
    
    def translate_sequence(self, sequence, table_type='agent'):
        """
        Translate a sequence of codons (DNA-like string).
        
        Args:
            sequence (str): A string of nucleotides (length must be multiple of 3)
            table_type (str): Either 'agent' or 'world' to select translation table
            
        Returns:
            list: List of translated instructions, or None if sequence is invalid
            
        Example:
            >>> translator = CodonTranslator()
            >>> translator.translate_sequence('AAAAATACA', 'agent')
            ['move_forward', 'move_forward', 'turn_left']
        """
        if not sequence or len(sequence) % 3 != 0:
            return None
        
        # Split sequence into codons
        codons = [sequence[i:i+3] for i in range(0, len(sequence), 3)]
        
        # Select translation method
        translate_func = self.translate_agent if table_type == 'agent' else self.translate_world
        
        # Translate each codon
        instructions = []
        for codon in codons:
            instruction = translate_func(codon)
            if instruction is None:
                return None  # Invalid codon found
            instructions.append(instruction)
        
        return instructions
    
    def _validate_codon(self, codon):
        """
        Validate that a codon is properly formatted.
        
        Args:
            codon (str): The codon to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(codon, str):
            return False
        if len(codon) != 3:
            return False
        # Check that all characters are valid nucleotides
        valid_nucleotides = set('ACGT')
        return all(c.upper() in valid_nucleotides for c in codon)
    
    def get_degenerate_codons(self, instruction, table_type='agent'):
        """
        Get all codons that map to a given instruction (demonstrates degeneracy).
        
        Args:
            instruction (str): The phenotypic instruction
            table_type (str): Either 'agent' or 'world'
            
        Returns:
            list: List of all codons that produce this instruction
            
        Example:
            >>> translator = CodonTranslator()
            >>> translator.get_degenerate_codons('move_forward', 'agent')
            ['AAA', 'AAT']
        """
        table = self.agent_table if table_type == 'agent' else self.world_table
        return [codon for codon, instr in table.items() if instr == instruction]
    
    def get_degeneracy_stats(self):
        """
        Calculate degeneracy statistics for both tables.
        
        Returns:
            dict: Statistics about degeneracy in the codon tables
        """
        def calc_stats(table):
            instruction_counts = {}
            for instruction in table.values():
                instruction_counts[instruction] = instruction_counts.get(instruction, 0) + 1
            
            total_codons = len(table)
            unique_instructions = len(instruction_counts)
            avg_degeneracy = total_codons / unique_instructions if unique_instructions > 0 else 0
            
            return {
                'total_codons': total_codons,
                'unique_instructions': unique_instructions,
                'average_degeneracy': avg_degeneracy,
                'instruction_counts': instruction_counts
            }
        
        return {
            'agent_table': calc_stats(self.agent_table),
            'world_table': calc_stats(self.world_table)
        }


if __name__ == '__main__':
    # Quick demonstration
    translator = CodonTranslator()
    
    print("=== CodonTranslator Demonstration ===\n")
    
    # Demonstrate degeneracy
    print("Degeneracy Example (Agent Table):")
    print(f"  'AAA' -> {translator.translate_agent('AAA')}")
    print(f"  'AAT' -> {translator.translate_agent('AAT')} (degenerate)")
    print()
    
    print("Degeneracy Example (World Table):")
    print(f"  'GAA' -> {translator.translate_world('GAA')}")
    print(f"  'GAT' -> {translator.translate_world('GAT')} (degenerate)")
    print()
    
    # Show all degenerate codons for an instruction
    print("All codons for 'move_forward':")
    print(f"  {translator.get_degenerate_codons('move_forward', 'agent')}")
    print()
    
    # Translate a sequence
    print("Sequence Translation:")
    sequence = 'AAAAATACA'
    result = translator.translate_sequence(sequence, 'agent')
    print(f"  Sequence: {sequence}")
    print(f"  Codons: {[sequence[i:i+3] for i in range(0, len(sequence), 3)]}")
    print(f"  Instructions: {result}")
    print()
    
    # Show degeneracy statistics
    print("Degeneracy Statistics:")
    stats = translator.get_degeneracy_stats()
    for table_name, table_stats in stats.items():
        print(f"\n  {table_name}:")
        print(f"    Total codons: {table_stats['total_codons']}")
        print(f"    Unique instructions: {table_stats['unique_instructions']}")
        print(f"    Average degeneracy: {table_stats['average_degeneracy']:.2f}")
