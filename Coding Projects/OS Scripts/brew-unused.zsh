#!/usr/bin/env zsh
set -euo pipefail

: "${BREW:=brew}"

command -v "$BREW" >/dev/null 2>&1 || { print -u2 "ERROR: brew not found"; exit 1; }
command -v python3 >/dev/null 2>&1 || { print -u2 "ERROR: python3 not found"; exit 1; }

# --- fetch JSON once (fast + stable parsing) ---
# Note: --installed limits output to installed items (brew 4+). If your brew is older, remove --installed and filter in python.
formula_json="$($BREW info --json=v2 --installed --formula 2>/dev/null || true)"
cask_json="$($BREW info --json=v2 --installed --cask 2>/dev/null || true)"

python3 -c 'import sys, json, collections

def load(s):
    s = (s or "").strip()
    if not s:
        return {}
    return json.loads(s)

formula_doc = load(sys.argv[1])
cask_doc    = load(sys.argv[2])

formulae = formula_doc.get("formulae", []) or []
casks    = cask_doc.get("casks", []) or []

# --- build formula graph + install metadata ---
deps = {}  # name -> set(dependency names) [runtime deps]
installed = set()
installed_on_request = set()
installed_as_dependency = set()

for f in formulae:
    name = f.get("name")
    if not name:
        continue
    installed.add(name)
    deps[name] = set(f.get("dependencies") or [])  # runtime deps only

    inst_entries = f.get("installed") or []
    # If any installed instance says "on request", treat as user-installed root.
    if any(e.get("installed_on_request") for e in inst_entries):
        installed_on_request.add(name)
    # If any installed instance says "as dependency", track it (used for candidates).
    if any(e.get("installed_as_dependency") for e in inst_entries):
        installed_as_dependency.add(name)

# Roots: things the user installed explicitly (or that don\'t look like pure deps)
# Conservative rule: if it was ever installed_on_request -> root.
# Additionally, if it\'s installed but never marked installed_as_dependency -> also root.
roots = set(installed_on_request)
for name in installed:
    if name not in installed_as_dependency:
        roots.add(name)

# --- compute transitive closure of runtime deps from roots ---
needed = set()
stack = list(roots)
while stack:
    cur = stack.pop()
    for d in deps.get(cur, ()):
        if d in needed:
            continue
        needed.add(d)
        stack.append(d)

# Candidates for removal:
# - installed
# - installed_as_dependency (so likely pulled in automatically)
# - NOT in roots
# - NOT needed by roots (transitively)
removable = sorted([
    n for n in installed
    if (n in installed_as_dependency) and (n not in roots) and (n not in needed)
])

# Leaves (not depended on by any other installed formula; independent of on_request)
reverse = collections.defaultdict(set)
for a, ds in deps.items():
    for d in ds:
        reverse[d].add(a)
leaves = sorted([n for n in installed if not reverse.get(n)])

# Orphans/Top-level = not required by any other installed formula (reverse deps empty)
# This is basically the same as leaves, but kept separate in case you want both terms.
top_level = leaves

# --- cask -> formula deps (where declared) ---
# JSON v2: cask["depends_on"]["formula"] often exists when a formula is required.
cask_formula_deps = []
missing_cask_formula_deps = []
for c in casks:
    cname = c.get("token") or c.get("name")
    depblock = (c.get("depends_on") or {})
    fdeps = depblock.get("formula") or []
    # some brews return string vs list; normalize
    if isinstance(fdeps, str):
        fdeps = [fdeps]
    fdeps = [x for x in fdeps if isinstance(x, str) and x.strip()]
    if not fdeps:
        continue
    cask_formula_deps.append((cname, fdeps))
    for fd in fdeps:
        if fd not in installed:
            missing_cask_formula_deps.append((cname, fd))

# --- print report ---
def heading(s):
    print("\\n==> " + s)

heading(f"Installed formulae: {len(installed)}")
heading(f"Installed casks:    {len(casks)}")

heading("Roots (user-installed or not marked as dependency)")
for n in sorted(roots):
    print(n) if n else None
if not roots:
    print("(none)")

heading("Leaves (no other installed formula depends on them)")
for n in leaves:
    print(n)
if not leaves:
    print("(none)")

heading("Removable unused dependencies (computed from JSON graph)")
# This is the important list: similar intent to `brew autoremove -n`, but derived from JSON.
for n in removable:
    print(n)
if not removable:
    print("(none)")

heading("Casks that declare formula dependencies (from JSON)")
for cname, fdeps in sorted(cask_formula_deps):
    print(f"{cname}: " + ", ".join(fdeps))
if not cask_formula_deps:
    print("(none)")

heading("Casks with missing formula dependencies (likely need install)")
for cname, fd in sorted(missing_cask_formula_deps):
    print(f"{cname} -> {fd}")
if not missing_cask_formula_deps:
    print("(none)")
' "$formula_json" "$cask_json"

print "\nTip: Wenn du die Liste wirklich entfernen willst, nutze erst:"
print "  brew autoremove -n"
print "und dann (wenn\'s passt):"
print "  brew autoremove"