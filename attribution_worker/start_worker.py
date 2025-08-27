#!/usr/bin/env python3
import os
import subprocess
import sys

def create_missing_directories():
    """Create missing index directories to prevent startup failures."""
    base_path = "/mnt/infinigram-array"
    
    # List of all possible index directories
    index_dirs = [
        "v4_pileval_llama",
        "olmoe-mix-0924-dclm", 
        "olmoe-mix-0924-nodclm",
        "v4-olmoe-0125-1b-7b-anneal-adapt",
        "v4-olmo-2-1124-13b-anneal-adapt",
        "v4-olmo-2-0325-32b-anneal-adapt",
        "v4-tulu-3-8b-adapt-llama",
        "v4-tulu-3-70b-adapt-llama", 
        "v4-tulu-3-405b-adapt-llama",
        "v4-tulu-3-8b-adapt",
        "v4-tulu-3-70b-adapt",
        "v4-tulu-3-405b-adapt"
    ]
    
    # Create base directory if it doesn't exist
    os.makedirs(base_path, exist_ok=True)
    
    # Create all index directories
    for index_dir in index_dirs:
        full_path = os.path.join(base_path, index_dir)
        os.makedirs(full_path, exist_ok=True)
        print(f"Created directory: {full_path}")

if __name__ == "__main__":
    print("Creating missing index directories...")
    create_missing_directories()
    print("Starting attribution worker...")
    
    # Start the original worker command
    subprocess.run(["saq", "--web", "attribution_worker.worker_settings"], check=True) 