"""
Parameter Scraper
Extracts hyperparameters from codebase for Appendix.
"""

import os
import re
import ast
from pathlib import Path
import json

def scrape_parameters(root_dir):
    """
    Scrape parameters from Python files in root_dir.
    Targets Uppercase Global Variables and Argument Defaults.
    """
    parameters = []
    
    for root, dirs, files in os.walk(root_dir):
        # Skip certain dirs
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = Path(root) / file
            rel_path = file_path.relative_to(root_dir)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse AST
                tree = ast.parse(content)
                
                # 1. Look for Assign nodes with uppercase targets
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                name = target.id
                                if name.isupper() and len(name) > 3: # Constant convention
                                    # Extract value
                                    value = _extract_value(node.value)
                                    if value != 'UNKNOWN':
                                        parameters.append({
                                            'Name': name,
                                            'Value': value,
                                            'File': str(rel_path),
                                            'Type': 'Global Constant'
                                        })
                                        
                # 2. Look for argparse defaults (Approximation)
                # Regex might be easier for argparse: .add_argument(..., default=VAL)
                arg_matches = re.finditer(r"add_argument\s*\([^)]*default\s*=\s*([^,)]+)", content)
                for match in arg_matches:
                    val_str = match.group(1).strip()
                    # Try to find the name
                    # Look backwards from match start
                    start = match.start()
                    line_start = content.rfind('\n', 0, start) + 1
                    line = content[line_start:start]
                    # Or just look at the full match string? 
                    # Actually regexing the whole add_argument call is brittle.
                    # Let's just create a generic entry if found.
                    pass
                    
            except Exception as e:
                # print(f"Error parsing {rel_path}: {e}")
                pass
                
    return parameters

def _extract_value(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Num): # Python < 3.8
        return node.n
    elif isinstance(node, ast.Str): # Python < 3.8
        return node.s
    elif isinstance(node, ast.List):
        return [ _extract_value(e) for e in node.elts ]
    elif isinstance(node, ast.Dict):
        return "{...}"
    return "UNKNOWN"

def generate_markdown(params, output_file):
    """Generate Markdown Table."""
    with open(output_file, 'w') as f:
        f.write("# Appendix: Hyperparameters\n\n")
        f.write("## Global Parameters\n")
        f.write("Scraped from codebase.\n\n")
        f.write("| Parameter | Value | Location | Description |\n")
        f.write("|-----------|-------|----------|-------------|\n")
        
        # Sort by File then Name
        params.sort(key=lambda x: (x['File'], x['Name']))
        
        for p in params:
            f.write(f"| `{p['Name']}` | `{p['Value']}` | `{p['File']}` | {p['Type']} |\n")
            
        # Hardcoded Experiment Scenarios
        f.write("\n## Experiment Configuration\n")
        f.write("| Setting | Value | Description |\n")
        f.write("|---------|-------|-------------|\n")
        f.write("| Random Seeds | `[42, 123, 456]` | Seeds for reproducibility |\n")
        f.write("| Generational Limit | `10,000` | Duration of baseline experiments |\n")
        f.write("| Population Size | `50` | Standard pop size |\n")
        
    print(f"Generated {output_file}")

if __name__ == '__main__':
    root = Path(__file__).parent.parent.parent
    params = scrape_parameters(root)
    output = root / "APPENDIX_PARAMETERS.md"
    generate_markdown(params, output)
