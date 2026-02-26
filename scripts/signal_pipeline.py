#!/usr/bin/env python3
"""
QuantClaw Signal Pipeline — Auto-expands any new signal module into CLI + API + MCP.

When a new signal module is added to modules/, run this script to:
1. Detect new modules not yet in services.ts
2. Generate CLI command entry
3. Generate MCP tool definition
4. Generate API route stub
5. Update services.ts registry
6. Regenerate Zvec search index

Usage: python3 scripts/signal_pipeline.py [--dry-run]
"""

import importlib
import inspect
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
MODULES_DIR = PROJECT_ROOT / "modules"
SERVICES_FILE = PROJECT_ROOT / "src" / "app" / "services.ts"
API_DIR = PROJECT_ROOT / "src" / "app" / "api" / "v1"
sys.path.insert(0, str(PROJECT_ROOT))

# Signal-quality modules get special treatment
SIGNAL_MODULES = {
    "signal_fusion": {"category": "intelligence", "icon": "🎯", "priority": "high"},
    "anomaly_scanner": {"category": "intelligence", "icon": "⚡", "priority": "high"},
    "smart_money_tracker": {"category": "alt-data", "icon": "🐋", "priority": "high"},
    "cross_correlate": {"category": "quant", "icon": "🔗", "priority": "high"},
    "signal_discovery_engine": {"category": "quant", "icon": "🔬", "priority": "high"},
    "regime_correlation": {"category": "quant", "icon": "🌊", "priority": "high"},
    "macro_leading_index": {"category": "fixed-income", "icon": "📡", "priority": "high"},
}


def get_registered_services() -> set:
    """Parse services.ts to find already-registered module IDs."""
    if not SERVICES_FILE.exists():
        return set()
    content = SERVICES_FILE.read_text()
    return set(re.findall(r'id:\s*"([^"]+)"', content))


def get_all_modules() -> list:
    """Get all Python modules with their metadata."""
    modules = []
    for f in sorted(MODULES_DIR.glob("*.py")):
        if f.name.startswith("__"):
            continue
        mod_name = f.stem
        info = {"name": mod_name, "file": str(f)}

        try:
            mod = importlib.import_module(f"modules.{mod_name}")
            info["docstring"] = (mod.__doc__ or "").strip().split("\n")[0]
            info["functions"] = []
            for name, obj in inspect.getmembers(mod, inspect.isfunction):
                if not name.startswith("_"):
                    try:
                        sig = inspect.signature(obj)
                        params = [p.name for p in sig.parameters.values() if p.name != "self"]
                    except (ValueError, TypeError):
                        params = []
                    info["functions"].append({"name": name, "params": params})
        except Exception as e:
            info["error"] = str(e)[:100]
            info["docstring"] = ""
            info["functions"] = []

        modules.append(info)
    return modules


def generate_mcp_tool(mod_info: dict) -> dict:
    """Generate MCP tool definition for a module."""
    main_func = None
    for f in mod_info.get("functions", []):
        if f["name"].startswith("get_") or f["name"].startswith("run_") or f["name"].startswith("scan_") or f["name"].startswith("detect_") or f["name"].startswith("track_") or f["name"].startswith("discover_") or f["name"].startswith("correlate_"):
            main_func = f
            break
    if not main_func and mod_info.get("functions"):
        main_func = mod_info["functions"][0]

    if not main_func:
        return {}

    properties = {}
    required = []
    for p in main_func["params"]:
        if p in ("ticker", "symbol"):
            properties[p] = {"type": "string", "description": f"Stock ticker symbol (e.g. AAPL)"}
            required.append(p)
        elif p in ("period", "lookback"):
            properties[p] = {"type": "string", "description": "Time period (e.g. 1y, 6mo, 30d)"}
        elif p in ("universe", "tickers"):
            properties[p] = {"type": "array", "items": {"type": "string"}, "description": "List of ticker symbols"}
        else:
            properties[p] = {"type": "string", "description": f"Parameter: {p}"}

    return {
        "name": f"quantclaw_{mod_info['name']}",
        "description": mod_info.get("docstring", f"QuantClaw {mod_info['name']} module"),
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
        }
    }


def generate_api_route(mod_info: dict) -> str:
    """Generate Next.js API route for a module."""
    mod_name = mod_info["name"]
    slug = mod_name.replace("_", "-")

    # Find the main function
    main_func = "run"
    for f in mod_info.get("functions", []):
        if f["name"].startswith(("get_", "run_", "scan_", "detect_", "track_", "discover_", "correlate_", "find_")):
            main_func = f["name"]
            break

    has_ticker = any(
        "ticker" in f.get("params", []) or "symbol" in f.get("params", [])
        for f in mod_info.get("functions", [])
    )

    ticker_line = """const ticker = searchParams.get('ticker') || searchParams.get('symbol') || 'SPY';""" if has_ticker else ""
    ticker_arg = "${ticker}" if has_ticker else ""

    return f"""import {{ NextRequest, NextResponse }} from 'next/server';
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {{
  const {{ searchParams }} = new URL(request.url);
  {ticker_line}
  const action = searchParams.get('action') || '{main_func}';

  try {{
    const {{ execSync }} = await import('child_process');
    const cmd = `cd /home/quant/apps/quantclaw-data && python3 -c "import modules.{mod_name} as m; import json; print(json.dumps(m.${{action}}('{ticker_arg}')))"`;
    const result = execSync(cmd, {{ timeout: 60000 }}).toString().trim();
    const lines = result.split('\\n');
    const jsonLine = lines[lines.length - 1];
    return NextResponse.json(JSON.parse(jsonLine));
  }} catch (e: any) {{
    return NextResponse.json({{ error: e.message?.slice(0, 500) }}, {{ status: 500 }});
  }}
}}
"""


def generate_cli_entry(mod_info: dict) -> str:
    """Generate CLI command suggestion."""
    mod_name = mod_info["name"]
    main_func = mod_info["functions"][0]["name"] if mod_info.get("functions") else "run"
    params = mod_info["functions"][0].get("params", []) if mod_info.get("functions") else []
    param_str = " ".join(f"<{p}>" for p in params[:2])
    return f"python cli.py {mod_name.replace('_', '-')} {param_str}".strip()


def run_pipeline(dry_run=False):
    """Main pipeline: detect new modules, generate all interfaces."""
    print("🔄 QuantClaw Signal Pipeline")
    print(f"   Modules dir: {MODULES_DIR}")
    print(f"   Dry run: {dry_run}\n")

    registered = get_registered_services()
    all_modules = get_all_modules()

    new_modules = [m for m in all_modules if m["name"].replace("_", "-") not in registered and m["name"] not in registered]

    if not new_modules:
        print("✅ All modules already registered. Nothing to do.")
        return

    print(f"📦 Found {len(new_modules)} unregistered modules:\n")

    for mod in new_modules:
        slug = mod["name"].replace("_", "-")
        print(f"  📌 {mod['name']}")
        print(f"     Doc: {mod.get('docstring', 'N/A')[:80]}")
        print(f"     Functions: {len(mod.get('functions', []))}")

        # Generate MCP
        mcp = generate_mcp_tool(mod)
        if mcp:
            print(f"     MCP: {mcp['name']}")

        # Generate CLI
        cli = generate_cli_entry(mod)
        print(f"     CLI: {cli}")

        # Generate API route
        api_route_dir = API_DIR / slug
        if not api_route_dir.exists() and not dry_run:
            api_route_dir.mkdir(parents=True, exist_ok=True)
            route_code = generate_api_route(mod)
            (api_route_dir / "route.ts").write_text(route_code)
            print(f"     API: /api/v1/{slug} ✅ created")
        elif api_route_dir.exists():
            print(f"     API: /api/v1/{slug} (already exists)")
        else:
            print(f"     API: /api/v1/{slug} (dry run)")

        print()

    if not dry_run:
        # Regenerate search index
        print("🔍 Regenerating Zvec search index...")
        os.system(f"cd {PROJECT_ROOT} && python3 scripts/generate_index.py")

    print(f"\n✅ Pipeline complete. {len(new_modules)} modules processed.")
    print(f"   Run `npm run build` to compile new API routes.")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run_pipeline(dry_run=dry_run)
