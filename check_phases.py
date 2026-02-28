#!/usr/bin/env python3
"""Check roadmap phases against actual module files."""

import re
from pathlib import Path

def name_to_snake(name: str) -> str:
    """Convert phase name to expected module filename."""
    # Remove special chars and convert to snake_case
    s = name.lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[-\s]+', '_', s)
    return s

# Get existing modules
modules_dir = Path('modules')
existing = {f.stem for f in modules_dir.glob('*.py')}

# Parse roadmap (simplified - just extract phase names)
roadmap_path = Path('src/app/roadmap.ts')
content = roadmap_path.read_text()

# Extract phase names
phases = []
for line in content.split('\n'):
    if 'name:' in line and 'description:' in line:
        # Extract name
        match = re.search(r'name:\s*"([^"]+)"', line)
        if match:
            phases.append(match.group(1))

print(f"Total phases in roadmap: {len(phases)}")
print(f"Total module files: {len(existing)}")

# Check each phase
missing = []
for phase in phases:
    expected = name_to_snake(phase)
    if expected not in existing:
        missing.append(phase)

print(f"\nMissing modules: {len(missing)}")
if missing:
    print("\nFirst 20 missing:")
    for i, name in enumerate(missing[:20], 1):
        print(f"{i}. {name} -> {name_to_snake(name)}.py")
