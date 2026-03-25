#!/usr/bin/env python3
"""Check which phases are marked done but missing modules."""
import os
import re

# Parse roadmap.ts to extract phase names and IDs
roadmap_file = "src/app/roadmap.ts"
modules_dir = "modules"

phases = []
with open(roadmap_file) as f:
    content = f.read()
    # Extract phase entries
    pattern = r'\{ id: (\d+), name: "([^"]+)", description: "[^"]*", status: "done"'
    matches = re.findall(pattern, content)
    phases = [(int(id_), name) for id_, name in matches]

# Get existing module files
existing_modules = set(os.listdir(modules_dir))

# Check for missing modules
missing = []
for phase_id, phase_name in phases:
    # Try to find a matching module file
    # Convert phase name to snake_case
    snake_name = re.sub(r'[^\w\s]', '', phase_name).lower().replace(' ', '_')
    possible_names = [
        f"{snake_name}.py",
        f"{snake_name}_tracker.py",
        f"{snake_name}_monitor.py",
        f"{snake_name}_data.py",
    ]
    
    # Check common abbreviations/variations
    variations = [
        snake_name.replace('_and_', '_'),
        snake_name.replace('united_states_', 'us_'),
        snake_name.replace('_database', ''),
        snake_name.replace('_tracker', ''),
        snake_name.replace('_monitor', ''),
        snake_name.replace('_data', ''),
    ]
    
    for var in variations:
        possible_names.extend([f"{var}.py", f"{var}_tracker.py", f"{var}_monitor.py"])
    
    found = any(name in existing_modules for name in possible_names)
    
    if not found:
        missing.append((phase_id, phase_name, snake_name))

print(f"Total phases marked done: {len(phases)}")
print(f"Missing modules: {len(missing)}\n")

if missing:
    print("Missing phases (first 20):")
    for phase_id, name, snake in missing[:20]:
        print(f"  #{phase_id}: {name} -> {snake}.py")
    if len(missing) > 20:
        print(f"  ... and {len(missing) - 20} more")
