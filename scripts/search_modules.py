#!/usr/bin/env python3
"""BM25 search over QuantClaw Data modules — inspired by pinescript-ai RAG pattern.
Usage: python3 scripts/search_modules.py "OPEC oil compliance" [top_k]
"""
import json, re, sys

def tokenize(text):
    return re.findall(r'\w+', text.lower())

def search(query: str, top_k: int = 5):
    with open("data/search-index/bm25-full.json") as f:
        idx = json.load(f)
    
    idf = idx["idf"]
    k1, b, avgdl = idx["k1"], idx["b"], idx["avgdl"]
    q_tokens = tokenize(query)
    
    scores = []
    for i in range(idx["N"]):
        tf = idx["tf"][i]
        dl = idx["dl"][i]
        score = 0
        for t in q_tokens:
            if t not in idf: continue
            freq = tf.get(t, 0)
            if freq == 0: continue
            num = freq * (k1 + 1)
            den = freq + k1 * (1 - b + b * dl / avgdl)
            score += idf[t] * num / den
        if score > 0:
            scores.append((score, i))
    
    scores.sort(reverse=True)
    results = []
    for score, i in scores[:top_k]:
        results.append({
            "module": idx["module_ids"][i],
            "score": round(score, 3),
            "description": idx["docs"][i],
            "functions": idx["fns"][i]
        })
    return results

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "oil price OPEC"
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    results = search(query, top_k)
    if not results:
        print("No results found.")
    for r in results:
        print(f"\n🔍 {r['module']} (score: {r['score']})")
        print(f"   {r['description']}")
        print(f"   Functions: {', '.join(r['functions'][:5])}")
