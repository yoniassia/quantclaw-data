#!/usr/bin/env python3
"""Strip markdown code fences from stdin, output clean content."""
import sys, re, json

raw = sys.stdin.read()

try:
    r = json.loads(raw)
    text = r.get("choices", [{}])[0].get("message", {}).get("content", "")
except (json.JSONDecodeError, KeyError):
    text = raw

text = text.strip()
text = re.sub(r"^```(?:python|json)?\s*\n?", "", text)
text = re.sub(r"\n?```\s*$", "", text)
print(text.strip())
