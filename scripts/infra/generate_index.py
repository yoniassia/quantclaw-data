#!/usr/bin/env python3
"""
Generate searchable markdown index of all QuantClaw Data modules.
Output: /home/quant/.openclaw/workspace/knowledge/quantclaw-data-index.md
This gets auto-indexed by zvec-watcher into vector search.
"""

import importlib
import inspect
import json
import os
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
MODULES_DIR = PROJECT_ROOT / "modules"
OUTPUT_DIR = Path("/home/quant/.openclaw/workspace/knowledge")
OUTPUT_FILE = OUTPUT_DIR / "quantclaw-data-index.md"
CORRELATION_FILE = OUTPUT_DIR / "quantclaw-data-correlations.md"

sys.path.insert(0, str(PROJECT_ROOT))


def get_module_info(module_path: Path) -> dict:
    """Extract metadata from a Python module."""
    mod_name = f"modules.{module_path.stem}"
    info = {
        "name": module_path.stem,
        "file": str(module_path),
        "size": module_path.stat().st_size,
        "functions": [],
        "docstring": "",
        "data_sources": [],
        "imports": [],
    }

    try:
        mod = importlib.import_module(mod_name)
        info["docstring"] = (mod.__doc__ or "").strip()

        # Get all public functions
        for name, obj in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith("_"):
                continue
            sig = ""
            try:
                sig = str(inspect.signature(obj))
            except (ValueError, TypeError):
                pass
            doc = (obj.__doc__ or "").strip().split("\n")[0]  # First line only
            info["functions"].append({"name": name, "signature": sig, "doc": doc})

    except Exception as e:
        info["error"] = str(e)[:200]

    # Scan source for data source URLs
    try:
        source = module_path.read_text(errors="ignore")
        import re
        urls = re.findall(r'https?://[a-zA-Z0-9._/-]+', source)
        domains = list(set(
            url.split("/")[2] for url in urls
            if "." in url.split("/")[2] and "python" not in url and "github" not in url
        ))
        info["data_sources"] = sorted(domains)[:15]

        # Detect imports
        for line in source.split("\n"):
            if line.startswith("import ") or line.startswith("from "):
                pkg = line.split()[1].split(".")[0]
                if pkg not in ("os", "sys", "json", "re", "time", "datetime", "pathlib", "typing", "collections", "functools", "math"):
                    if pkg not in info["imports"]:
                        info["imports"].append(pkg)
    except Exception:
        pass

    return info


def categorize_module(name: str, docstring: str) -> str:
    """Auto-categorize module by name/docstring."""
    name_lower = name.lower()
    doc_lower = docstring.lower()
    combined = name_lower + " " + doc_lower

    categories = {
        "macro": ["gdp", "cpi", "inflation", "fed", "central_bank", "treasury", "yield_curve", "pboc", "ecb", "boj", "imf", "taylor_rule", "recession"],
        "equity": ["stock", "earnings", "screener", "company", "profile", "sec", "filing", "13f", "insider"],
        "fixed_income": ["bond", "credit", "cds", "spread", "duration", "convexity", "muni", "clo", "abs", "mbs"],
        "derivatives": ["option", "gex", "greeks", "vol", "straddle", "implied", "skew"],
        "quant": ["monte_carlo", "fama", "kalman", "black_litterman", "pairs", "cointegration", "factor", "backtest", "momentum", "mean_reversion", "stat_arb", "risk_parity", "kelly"],
        "crypto": ["crypto", "bitcoin", "ethereum", "defi", "nft", "liquidation", "funding_rate", "stablecoin"],
        "commodities": ["oil", "gold", "commodity", "opec", "eia", "usda", "agriculture", "energy", "metal", "lng", "carbon"],
        "fx": ["forex", "currency", "fx", "carry_trade", "intervention"],
        "alt_data": ["satellite", "patent", "job", "congress", "social", "sentiment", "dark_pool", "short_squeeze", "insider", "shipping"],
        "ml_ai": ["neural", "lstm", "transformer", "xgboost", "random_forest", "ml", "deep_learning", "anomaly", "automl"],
        "real_time": ["websocket", "stream", "live", "real_time", "tick", "heatmap"],
    }

    for cat, keywords in categories.items():
        if any(kw in combined for kw in keywords):
            return cat
    return "other"


def generate_index():
    """Generate the main searchable index."""
    modules = []
    for f in sorted(MODULES_DIR.glob("*.py")):
        if f.name.startswith("__"):
            continue
        info = get_module_info(f)
        info["category"] = categorize_module(info["name"], info["docstring"])
        modules.append(info)

    # Build markdown
    lines = [
        f"# QuantClaw Data — Module Index",
        f"",
        f"> Auto-generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"> Total modules: {len(modules)}",
        f"> Search this file via Zvec for instant recall of any data source, function, or capability.",
        f"",
    ]

    # Summary by category
    cat_counts = {}
    for m in modules:
        cat_counts[m["category"]] = cat_counts.get(m["category"], 0) + 1

    lines.append("## Categories")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- **{cat}**: {count} modules")
    lines.append("")

    # All data sources (deduplicated)
    all_sources = set()
    for m in modules:
        all_sources.update(m["data_sources"])

    lines.append(f"## Data Sources ({len(all_sources)} unique)")
    for src in sorted(all_sources):
        lines.append(f"- {src}")
    lines.append("")

    # Per-module detail
    lines.append("## Modules\n")
    for m in modules:
        lines.append(f"### {m['name']}")
        lines.append(f"**Category:** {m['category']} | **Size:** {m['size']:,} bytes | **Functions:** {len(m['functions'])}")
        if m["docstring"]:
            lines.append(f"\n{m['docstring'][:300]}")
        if m["data_sources"]:
            lines.append(f"\n**Data sources:** {', '.join(m['data_sources'])}")
        if m["functions"]:
            lines.append("\n**Functions:**")
            for func in m["functions"][:10]:
                doc_part = f" — {func['doc']}" if func['doc'] else ""
                lines.append(f"- `{func['name']}{func['signature']}`{doc_part}")
        lines.append("")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(lines))
    print(f"✅ Index written: {OUTPUT_FILE} ({len(lines)} lines, {len(modules)} modules, {len(all_sources)} data sources)")
    return modules, all_sources


def generate_correlations(modules):
    """Generate a correlation map showing which modules share data sources."""
    lines = [
        "# QuantClaw Data — Cross-Module Correlations",
        "",
        f"> Auto-generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "> Shows which modules share data sources — useful for building composite signals.",
        "",
    ]

    # Build source → modules map
    source_to_modules = {}
    for m in modules:
        for src in m["data_sources"]:
            if src not in source_to_modules:
                source_to_modules[src] = []
            source_to_modules[src].append(m["name"])

    # Find modules that share sources (potential correlations)
    lines.append("## Shared Data Sources (modules that can be correlated)\n")
    for src, mods in sorted(source_to_modules.items(), key=lambda x: -len(x[1])):
        if len(mods) >= 2:
            lines.append(f"### {src} ({len(mods)} modules)")
            for mod in sorted(mods):
                lines.append(f"- {mod}")
            lines.append("")

    # Category cross-references
    lines.append("## Cross-Category Opportunities\n")
    cat_modules = {}
    for m in modules:
        if m["category"] not in cat_modules:
            cat_modules[m["category"]] = []
        cat_modules[m["category"]].append(m["name"])

    cats = list(cat_modules.keys())
    for i, cat1 in enumerate(cats):
        for cat2 in cats[i+1:]:
            # Find shared data sources between categories
            sources1 = set()
            sources2 = set()
            for m in modules:
                if m["category"] == cat1:
                    sources1.update(m["data_sources"])
                elif m["category"] == cat2:
                    sources2.update(m["data_sources"])
            shared = sources1 & sources2
            if shared:
                lines.append(f"**{cat1} ↔ {cat2}** (shared: {', '.join(list(shared)[:5])})")

    lines.append("")
    CORRELATION_FILE.write_text("\n".join(lines))
    print(f"✅ Correlations written: {CORRELATION_FILE} ({len(lines)} lines)")


if __name__ == "__main__":
    modules, sources = generate_index()
    generate_correlations(modules)
