import os
import re
from pathlib import Path

def parse_env_file(env_file_path):
    """Parse .env.example file and return a list of environment variables."""
    env_vars = []
    with open(env_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                var_name = line.split('=')[0].strip()
                env_vars.append(var_name)
    return env_vars

def search_var_in_file(file_path, var_name):
    """Search for environment variable usage in a file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        # Look for common patterns of env var usage
        patterns = [
            rf"os\.environ\.get\(['\"]?{var_name}['\"]?",  # os.environ.get('VAR')
            rf"os\.getenv\(['\"]?{var_name}['\"]?",        # os.getenv('VAR')
            rf"environ\[['\"]?{var_name}['\"]?",           # environ['VAR']
            rf"os\.environ\[['\"]?{var_name}['\"]?",       # os.environ['VAR']
            rf"settings\.{var_name.lower()}",              # settings.var_name
            rf"config\.{var_name.lower()}"                 # config.var_name
        ]
        for pattern in patterns:
            if re.search(pattern, content):
                return True
    return False

def find_hardcoded_values(file_path, env_vars):
    """Find potential hardcoded values that should be environment variables."""
    hardcoded = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        # Common patterns that might indicate hardcoded values
        patterns = {
            'host': r'["\'](?:localhost|127\.0\.0\.1|0\.0\.0\.0)["\']',
            'port': r'port\s*=\s*\d{4}',
            'url': r'["\']https?://[^"\'\s]+["\']',
            'path': r'["\']\/[^"\'\s]+["\']'
        }
        for key, pattern in patterns.items():
            matches = re.finditer(pattern, content)
            for match in matches:
                hardcoded.append((key, match.group(), file_path))
    return hardcoded

def main():
    # Get repository root directory
    repo_root = Path(__file__).parent.parent
    env_example_path = repo_root / '.env.example'
    
    # Parse environment variables
    env_vars = parse_env_file(env_example_path)
    
    print(f"\n=== Checking {len(env_vars)} Environment Variables ===\n")
    
    # Track results
    unused_vars = []
    used_vars = {}
    all_hardcoded = []
    
    # Search through all Python files
    for python_file in repo_root.rglob('*.py'):
        if 'venv' in str(python_file) or 'test_env_vars.py' in str(python_file):
            continue
            
        # Check each env var
        for var in env_vars:
            if search_var_in_file(python_file, var):
                if var not in used_vars:
                    used_vars[var] = []
                used_vars[var].append(python_file)
                
        # Check for hardcoded values
        hardcoded = find_hardcoded_values(python_file, env_vars)
        if hardcoded:
            all_hardcoded.extend(hardcoded)
    
    # Find unused variables
    unused_vars = [var for var in env_vars if var not in used_vars]
    
    # Report results
    print("\n=== Environment Variable Usage ===")
    print("\nUsed Variables:")
    for var, files in used_vars.items():
        print(f"\n{var}:")
        for file in files:
            print(f"  - {file.relative_to(repo_root)}")
    
    print("\nUnused Variables:")
    for var in unused_vars:
        print(f"  - {var}")
    
    print("\n=== Potential Hardcoded Values ===")
    for type_, value, file in all_hardcoded:
        print(f"\nType: {type_}")
        print(f"Value: {value}")
        print(f"File: {file.relative_to(repo_root)}")
    
    # Summary
    print("\n=== Summary ===")
    print(f"Total env variables: {len(env_vars)}")
    print(f"Used variables: {len(used_vars)}")
    print(f"Unused variables: {len(unused_vars)}")
    print(f"Potential hardcoded values: {len(all_hardcoded)}")

if __name__ == "__main__":
    main()
