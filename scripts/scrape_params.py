import os
import re

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Regex patterns to find standard configurations in our python files
patterns = {
    'Population Size': r'pop_size\s*=\s*(\d+)',
    'Generations': r'generations\s*=\s*(\d+)',
    'Mutation Rate': r'mutation_rate\s*=\s*([\d\.]+)',
    'F (Feed rate)': r'f_map\s*=\s*.*?\s+([\d\.]+)\s*,',
    'k (Kill rate)': r'k_map\s*=\s*.*?\s+([\d\.]+)\s*,',
    'Substrate Width': r'width\s*=\s*(\d+)',
    'Substrate Height': r'height\s*=\s*(\d+)',
    'Metabolic Cost (Step)': r'energy\s*-=\s*([\d\.]+)'
}

def main():
    print("Scraping parameters from codebase...")
    
    found_params = {k: set() for k in patterns.keys()}
    
    for dirpath, _, filenames in os.walk(root_dir):
        if 'venv' in dirpath or '.git' in dirpath or '__pycache__' in dirpath:
            continue
            
        for file in filenames:
            if file.endswith('.py'):
                filepath = os.path.join(dirpath, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for param, pattern in patterns.items():
                            matches = re.findall(pattern, content)
                            for match in matches:
                                found_params[param].add(match)
                except Exception:
                    pass
                    
    # Format output
    out_dir = os.path.join(root_dir, 'reproducibility_package')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'APPENDIX_PARAMETERS.md')
    
    with open(out_path, 'w') as f:
        f.write("# Appendix B: Hyperparameter Configurations\n\n")
        f.write("The following hyperparameters were automatically scraped from the final codebase used for the baseline and Genesis experiments.\n\n")
        f.write("| Parameter | Values Used |\n")
        f.write("|---|---|\n")
        
        for param, values in found_params.items():
            val_str = ", ".join(sorted(list(values))) if values else "Dynamic / Not static"
            f.write(f"| {param} | {val_str} |\n")
            
        f.write("\n\n*Note: CARP and AIS parameters are dynamically adjusted during runtime based on population viability metrics detailed in Section 3.*")
        
    print(f"Saved parameters to {out_path}")

if __name__ == '__main__':
    main()
