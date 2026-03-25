import re

with open('src/app/roadmap.ts', 'r') as f:
    content = f.read()

# Count phases by status
pattern = r'\{ id: (\d+),.*?status: "([^"]+)"'
status_counts = {"done": 0, "next": 0, "planned": 0}

for match in re.finditer(pattern, content):
    phase_id = int(match.group(1))
    status = match.group(2)
    status_counts[status] += 1

total = sum(status_counts.values())
print(f"📊 QUANTCLAW-DATA COMPLETION STATUS")
print(f"{'='*50}")
print(f"✅ Done:     {status_counts['done']:3d}")
print(f"🚧 Next:     {status_counts['next']:3d}")
print(f"📋 Planned:  {status_counts['planned']:3d}")
print(f"{'='*50}")
print(f"   TOTAL:    {total:3d} phases")

if status_counts['planned'] == 0 and status_counts['next'] == 0:
    print(f"\n🎉 ALL {total} PHASES COMPLETE!")
else:
    print(f"\n{status_counts['planned'] + status_counts['next']} phases remaining")
