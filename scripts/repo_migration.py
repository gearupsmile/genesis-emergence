import os
import shutil
from pathlib import Path

def setup_directories(root_dir):
    dirs = ['docs', 'tests', 'experiments', 'archive', 'scripts']
    for d in dirs:
        (root_dir / d).mkdir(exist_ok=True)

def safe_move(src, dest):
    if not src.exists():
        return
    try:
        # If destination is a directory, append the source filename
        if dest.is_dir():
            dest_path = dest / src.name
        else:
            dest_path = dest
            
        if dest_path.exists():
            print(f"Skipping {src.name} -> {dest_path} (Already exists)")
            return
            
        shutil.move(str(src), str(dest_path))
        print(f"Moved {src.name} -> {dest}")
    except Exception as e:
        print(f"Failed to move {src.name}: {e}")

def main():
    root_dir = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    print(f"Migrating repository at: {root_dir}")
    
    setup_directories(root_dir)
    
    # 1. Move root markdown documentation to docs/
    docs_dir = root_dir / 'docs'
    for md_file in root_dir.glob('*.md'):
        if md_file.name.lower() != 'readme.md':
            safe_move(md_file, docs_dir)
            
    # 2. Archive scattered evaluation data, notebooks, output logs, old backups
    archive_dir = root_dir / 'archive'
    archive_targets = [
        'genesis-backup-pre-v3-2026-02-18',
        'checkpoints',
        'runs',
        'results',
        'data',
        'output',
        'artifact_analysis_output',
        'artifacts',
        'notebooks',
        'discovery',
        'verification',
        'expert_coevolution_metrics.json',
        'mock_paper.aux',
        'mock_paper.log',
        'mock_paper.pdf',
    ]
    for target in archive_targets:
        safe_move(root_dir / target, archive_dir)

    # 3. Consolidate stray tests and logic to tests/
    test_dir = root_dir / 'tests'
    safe_move(root_dir / 'debug', test_dir / 'debug')
    safe_move(root_dir / 'debug_fitness_issue.py', test_dir / 'debug_fitness_issue.py')
    
    # 4. Consolidate v1, v2, v3 tests if they are not already in their place.
    # We will assume they are mostly contained in genesis_engine_v* for now safely,
    # as cross-version tests would break if blindly moved up to root without path refactoring.
    
    print("\n--- Repository Migration Complete ---\n")
    print("Listing current root structure:")
    for child in root_dir.iterdir():
        if not child.name.startswith('.') and not child.name == '__pycache__':
            print(f" - {child.name}/" if child.is_dir() else f" - {child.name}")

if __name__ == '__main__':
    main()
