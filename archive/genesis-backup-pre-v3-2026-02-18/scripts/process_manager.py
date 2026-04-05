"""
Process Management Script for Genesis Experiments

Functions to manage running processes, cleanup checkpoints, and verify system readiness.
"""

import psutil
import os
import shutil
from pathlib import Path
from datetime import datetime
import signal


def find_genesis_processes():
    """
    Find all Python processes running genesis-related code.
    
    Returns:
        List of dicts with process info (pid, name, cmdline, cpu_percent, memory_mb)
    """
    genesis_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('genesis' in str(arg).lower() or 'run_' in str(arg).lower() 
                              for arg in cmdline):
                memory_mb = proc.info['memory_info'].rss / (1024 * 1024) if proc.info['memory_info'] else 0
                
                genesis_processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cmdline': ' '.join(cmdline) if cmdline else '',
                    'cpu_percent': proc.info['cpu_percent'],
                    'memory_mb': memory_mb
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return genesis_processes


def terminate_process(pid: int, timeout: int = 10) -> bool:
    """
    Gracefully terminate a process with SIGTERM.
    
    Args:
        pid: Process ID to terminate
        timeout: Seconds to wait before forcing kill
        
    Returns:
        True if successfully terminated, False otherwise
    """
    try:
        proc = psutil.Process(pid)
        
        print(f"Terminating process {pid}: {proc.name()}")
        
        # Try graceful termination first
        proc.terminate()
        
        # Wait for process to terminate
        try:
            proc.wait(timeout=timeout)
            print(f"  Process {pid} terminated gracefully")
            return True
        except psutil.TimeoutExpired:
            print(f"  Process {pid} did not terminate, forcing kill...")
            proc.kill()
            proc.wait(timeout=5)
            print(f"  Process {pid} killed")
            return True
            
    except psutil.NoSuchProcess:
        print(f"  Process {pid} not found")
        return False
    except psutil.AccessDenied:
        print(f"  Access denied to process {pid}")
        return False
    except Exception as e:
        print(f"  Error terminating process {pid}: {e}")
        return False


def cleanup_checkpoints(checkpoint_dir: str = "checkpoints", archive_dir: str = "archive"):
    """
    Archive old checkpoint files to archive/ directory.
    
    Args:
        checkpoint_dir: Directory containing checkpoints
        archive_dir: Directory to move checkpoints to
    """
    checkpoint_path = Path(checkpoint_dir)
    archive_path = Path(archive_dir)
    
    if not checkpoint_path.exists():
        print(f"Checkpoint directory not found: {checkpoint_dir}")
        return
    
    # Create archive directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_subdir = archive_path / f"checkpoints_{timestamp}"
    archive_subdir.mkdir(parents=True, exist_ok=True)
    
    # Move checkpoint files
    checkpoint_files = list(checkpoint_path.glob("*.pkl"))
    
    if not checkpoint_files:
        print("No checkpoint files to archive")
        return
    
    print(f"Archiving {len(checkpoint_files)} checkpoint files...")
    
    for checkpoint_file in checkpoint_files:
        dest = archive_subdir / checkpoint_file.name
        shutil.move(str(checkpoint_file), str(dest))
        print(f"  Moved: {checkpoint_file.name}")
    
    print(f"Checkpoints archived to: {archive_subdir}")


def verify_system_readiness():
    """
    Check disk space, memory, and dependencies for running experiments.
    
    Returns:
        Dict with readiness status and warnings
    """
    status = {
        'ready': True,
        'warnings': [],
        'disk_space_gb': 0,
        'memory_available_gb': 0,
        'cpu_count': 0
    }
    
    # Check disk space
    disk = psutil.disk_usage('.')
    disk_free_gb = disk.free / (1024**3)
    status['disk_space_gb'] = disk_free_gb
    
    if disk_free_gb < 1.0:
        status['ready'] = False
        status['warnings'].append(f"Low disk space: {disk_free_gb:.2f} GB (need at least 1 GB)")
    elif disk_free_gb < 5.0:
        status['warnings'].append(f"Disk space low: {disk_free_gb:.2f} GB (recommended: 5+ GB)")
    
    # Check memory
    memory = psutil.virtual_memory()
    memory_available_gb = memory.available / (1024**3)
    status['memory_available_gb'] = memory_available_gb
    
    if memory_available_gb < 0.5:
        status['ready'] = False
        status['warnings'].append(f"Low memory: {memory_available_gb:.2f} GB (need at least 0.5 GB)")
    elif memory_available_gb < 2.0:
        status['warnings'].append(f"Memory limited: {memory_available_gb:.2f} GB (recommended: 2+ GB)")
    
    # Check CPU
    cpu_count = psutil.cpu_count()
    status['cpu_count'] = cpu_count
    
    # Check dependencies
    try:
        import numpy
        import matplotlib
        import scipy
    except ImportError as e:
        status['ready'] = False
        status['warnings'].append(f"Missing dependency: {e}")
    
    return status


def print_system_status():
    """Print comprehensive system status."""
    print("=" * 70)
    print("GENESIS SYSTEM STATUS")
    print("=" * 70)
    print()
    
    # Running processes
    print("Running Genesis Processes:")
    processes = find_genesis_processes()
    if processes:
        for proc in processes:
            print(f"  PID {proc['pid']}: {proc['name']}")
            print(f"    Command: {proc['cmdline'][:80]}...")
            print(f"    CPU: {proc['cpu_percent']:.1f}%, Memory: {proc['memory_mb']:.1f} MB")
    else:
        print("  No genesis processes running")
    print()
    
    # System readiness
    print("System Readiness:")
    status = verify_system_readiness()
    print(f"  Ready: {'YES' if status['ready'] else 'NO'}")
    print(f"  Disk Space: {status['disk_space_gb']:.2f} GB")
    print(f"  Memory Available: {status['memory_available_gb']:.2f} GB")
    print(f"  CPU Cores: {status['cpu_count']}")
    
    if status['warnings']:
        print("\n  Warnings:")
        for warning in status['warnings']:
            print(f"    - {warning}")
    print()
    
    print("=" * 70)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python process_manager.py status          - Show system status")
        print("  python process_manager.py list            - List genesis processes")
        print("  python process_manager.py kill <pid>      - Terminate process")
        print("  python process_manager.py cleanup         - Archive checkpoints")
        print("  python process_manager.py verify          - Check system readiness")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        print_system_status()
    
    elif command == 'list':
        processes = find_genesis_processes()
        if processes:
            print(f"Found {len(processes)} genesis process(es):")
            for proc in processes:
                print(f"  PID {proc['pid']}: {proc['cmdline'][:60]}...")
        else:
            print("No genesis processes running")
    
    elif command == 'kill':
        if len(sys.argv) < 3:
            print("Usage: python process_manager.py kill <pid>")
            sys.exit(1)
        pid = int(sys.argv[2])
        terminate_process(pid)
    
    elif command == 'cleanup':
        cleanup_checkpoints()
    
    elif command == 'verify':
        status = verify_system_readiness()
        print(f"System Ready: {'YES' if status['ready'] else 'NO'}")
        print(f"Disk: {status['disk_space_gb']:.2f} GB")
        print(f"Memory: {status['memory_available_gb']:.2f} GB")
        print(f"CPUs: {status['cpu_count']}")
        if status['warnings']:
            print("\nWarnings:")
            for w in status['warnings']:
                print(f"  - {w}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
