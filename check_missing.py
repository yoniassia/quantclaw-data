import re

# Read roadmap.ts
with open('src/app/roadmap.ts', 'r') as f:
    content = f.read()

# Extract all phases
phases = []
pattern = r'\{ id: (\d+), name: "([^"]+)".*?status: "([^"]+)"'
for match in re.finditer(pattern, content):
    phase_id = int(match.group(1))
    name = match.group(2)
    status = match.group(3)
    
    # Convert name to snake_case module name
    module_name = re.sub(r'[^\w\s-]', '', name.lower())
    module_name = re.sub(r'[-\s]+', '_', module_name)
    
    phases.append({
        'id': phase_id,
        'name': name,
        'status': status,
        'module': module_name
    })

# Get existing module files
import os
existing = set(f.replace('.py', '') for f in os.listdir('modules') if f.endswith('.py'))

# Find missing
missing = []
for p in phases:
    if p['status'] == 'done' and p['module'] not in existing:
        missing.append(p)

print(f"Total phases: {len(phases)}")
print(f"Marked as done: {len([p for p in phases if p['status'] == 'done'])}")
print(f"Existing modules: {len(existing)}")
print(f"\nMissing modules ({len(missing)}):")
for m in sorted(missing, key=lambda x: x['id'])[:10]:  # Show first 10
    print(f"  Phase {m['id']}: {m['name']} -> {m['module']}.py")
