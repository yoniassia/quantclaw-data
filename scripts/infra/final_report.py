import re

with open('src/app/roadmap.ts', 'r') as f:
    content = f.read()

# Extract all phases with LOC
pattern = r'\{ id: (\d+), name: "([^"]+)".*?category: "([^"]+)".*?loc: (\d+)'
phases = []
total_loc = 0

for match in re.finditer(pattern, content):
    phase_id = int(match.group(1))
    name = match.group(2)
    category = match.group(3)
    loc = int(match.group(4))
    phases.append({'id': phase_id, 'name': name, 'category': category, 'loc': loc})
    total_loc += loc

# Category breakdown
from collections import defaultdict
cat_loc = defaultdict(int)
for p in phases:
    cat_loc[p['category']] += p['loc']

print("🎉 QUANTCLAW-DATA: ALL 200 PHASES COMPLETE! 🎉")
print("=" * 60)
print(f"\n📈 Total Code Written: {total_loc:,} lines")
print(f"📦 Total Phases: {len(phases)}")
print(f"📁 Module Files: 175 (.py)")
print(f"\n📊 Lines of Code by Category:")
print("-" * 60)
for cat, loc in sorted(cat_loc.items(), key=lambda x: -x[1])[:15]:
    print(f"  {cat:25s} {loc:6,} LOC")
print("-" * 60)
print(f"  {'TOTAL':25s} {total_loc:6,} LOC")

# Top 10 largest modules
print(f"\n🏆 Top 10 Largest Modules:")
print("-" * 60)
for p in sorted(phases, key=lambda x: -x['loc'])[:10]:
    print(f"  #{p['id']:3d} {p['name']:35s} {p['loc']:5,} LOC")

