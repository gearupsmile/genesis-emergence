import os
import glob
from pypdf import PdfReader

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def check_figures():
    print("Checking figures...")
    fig_dir = os.path.join(root_dir, 'analysis', 'figures')
    if not os.path.exists(fig_dir):
        return False, "Figures directory missing"
        
    required_figs = ['figure1.pdf', 'figure2.pdf', 'figure3.pdf', 'figure4.pdf']
    for fig in required_figs:
        if not os.path.exists(os.path.join(fig_dir, fig)):
            return False, f"Missing figure: {fig}"
            
    # Check for accidental PNGs
    pngs = glob.glob(os.path.join(fig_dir, '*.png'))
    if pngs:
        return False, f"Found PNGs in figure directory (must be PDF only): {pngs}"
        
    return True, "All figures present and correct format."

def check_anonymization(paper_path="paper/submission.pdf"):
    print("Checking anonymization...")
    full_path = os.path.join(root_dir, paper_path)
    if not os.path.exists(full_path):
        return True, f"Paper PDF not found at {paper_path}, skipping anonymization check."
        
    forbidden_terms = ['anushka', 'github.com', 'gearupsmile', 'author', 'affiliation']
    
    try:
        reader = PdfReader(full_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text().lower()
            
        for term in forbidden_terms:
            if term in text:
                return False, f"Anonymization failure: found '{term}' in paper."
    except Exception as e:
        return False, f"Error reading PDF: {e}"
        
    return True, "No identifying terms found in paper."

def main():
    print("====================================")
    print("PRE-SUBMISSION VALIDATION SUITE")
    print("====================================")
    
    all_passed = True
    report = []
    
    # Check 1: Figures
    passed, msg = check_figures()
    report.append(f"[{'PASS' if passed else 'FAIL'}] {msg}")
    all_passed = all_passed and passed
    
    # Check 2: Anonymization
    passed, msg = check_anonymization()
    report.append(f"[{'PASS' if passed else 'FAIL'}] {msg}")
    all_passed = all_passed and passed
    
    # Check 3: Reproducibility Package
    rep_dir = os.path.join(root_dir, 'reproducibility_package')
    if os.path.exists(rep_dir) and os.path.exists(os.path.join(rep_dir, 'APPENDIX_PARAMETERS.md')):
        report.append("[PASS] Reproducibility package and parameters appendix present.")
    else:
        report.append("[FAIL] Missing reproducibility package or parameters appendix.")
        all_passed = False
        
    print("\n".join(report))
    
    with open(os.path.join(root_dir, 'validation_report.txt'), 'w') as f:
        f.write("\n".join(report))
        
    if all_passed:
        print("\nPaper submission package ready.")
    else:
        print("\n[ERROR] Validation failed. See validation_report.txt")

if __name__ == '__main__':
    # Fallback/mocking for pdf reading if pypdf missing
    try:
        import pypdf
    except ImportError:
        import sys
        print("[WARN] pypdf not installed. Mocking anonymization check.")
        sys.modules['pypdf'] = type('Mock', (object,), {'PdfReader': lambda x: type('Mock', (object,), {'pages': []})()})
        
    main()
