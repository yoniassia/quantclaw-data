#!/usr/bin/env python3
"""3-layer validation pipeline for QuantClaw Data modules — inspired by pinescript-ai.
Layer 1: Static regex checks (fast)
Layer 2: AST parse + import check
Layer 3: Function signature validation

Usage: python3 scripts/validate_module.py modules/my_module.py
       python3 scripts/validate_module.py --all  (validate all)
"""
import ast, sys, os, re, importlib

def validate_static(path: str) -> list:
    """Layer 1: Static regex checks"""
    issues = []
    with open(path) as f:
        src = f.read()
    
    if not src.strip():
        issues.append("CRITICAL: Empty file")
        return issues
    
    # Must have docstring
    if not re.search(r'^"""', src, re.MULTILINE) and not re.search(r"^'''", src, re.MULTILINE):
        issues.append("WARN: No module docstring")
    
    # Must have at least 2 functions
    func_count = len(re.findall(r'^def \w+', src, re.MULTILINE))
    if func_count < 2:
        issues.append(f"WARN: Only {func_count} functions (minimum 2)")
    
    # Check for common bugs
    if '.toFixed(' in src:
        issues.append("WARN: JavaScript .toFixed() found in Python file")
    if 'print(' in src and 'def main' not in src:
        issues.append("INFO: print() statements (ok for debugging)")
    
    return issues

def validate_ast(path: str) -> list:
    """Layer 2: AST parse + structure check"""
    issues = []
    with open(path) as f:
        src = f.read()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        issues.append(f"CRITICAL: SyntaxError line {e.lineno}: {e.msg}")
        return issues
    
    # Check all functions have return
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
            if not has_return and node.name not in ('main', 'run'):
                issues.append(f"WARN: {node.name}() has no return statement")
    
    return issues

def validate_import(module_name: str) -> list:
    """Layer 3: Actually try importing"""
    issues = []
    try:
        mod = importlib.import_module(f"modules.{module_name}")
        # Check it has callable functions
        funcs = [x for x in dir(mod) if not x.startswith('_') and callable(getattr(mod, x))
                 and x not in ('Dict','List','Optional','Tuple','Set','Any','Union')]
        if len(funcs) < 2:
            issues.append(f"WARN: Only {len(funcs)} callable exports")
    except Exception as e:
        issues.append(f"CRITICAL: Import failed — {type(e).__name__}: {str(e)[:200]}")
    return issues

def validate(path: str, do_import=True) -> dict:
    name = os.path.basename(path).replace('.py', '')
    result = {"module": name, "layers": {}, "pass": True}
    
    l1 = validate_static(path)
    result["layers"]["static"] = l1
    
    l2 = validate_ast(path)
    result["layers"]["ast"] = l2
    
    if do_import:
        l3 = validate_import(name)
        result["layers"]["import"] = l3
    
    all_issues = l1 + l2 + (result["layers"].get("import", []))
    result["pass"] = not any("CRITICAL" in i for i in all_issues)
    result["warnings"] = sum(1 for i in all_issues if "WARN" in i)
    result["criticals"] = sum(1 for i in all_issues if "CRITICAL" in i)
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/validate_module.py modules/my_module.py [--all]")
        sys.exit(1)
    
    if sys.argv[1] == "--all":
        passed = failed = 0
        for f in sorted(os.listdir("modules")):
            if not f.endswith('.py') or f.startswith('_'): continue
            r = validate(f"modules/{f}", do_import=False)  # skip import for speed
            status = "✅" if r["pass"] else "❌"
            if not r["pass"]:
                failed += 1
                print(f"{status} {r['module']}: {r['criticals']} critical, {r['warnings']} warn")
                for layer, issues in r["layers"].items():
                    for i in issues:
                        if "CRITICAL" in i: print(f"   {i}")
            else:
                passed += 1
        print(f"\n{passed} passed, {failed} failed out of {passed+failed}")
    else:
        r = validate(sys.argv[1])
        status = "✅ PASS" if r["pass"] else "❌ FAIL"
        print(f"{status}: {r['module']}")
        for layer, issues in r["layers"].items():
            if issues:
                print(f"  [{layer}]")
                for i in issues: print(f"    {i}")
