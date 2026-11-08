#!/usr/bin/env python3
"""Build a self-contained HTML graph of Claude Code memories.

Reads <config>/projects/*/memory/*.md (config = $CLAUDE_CONFIG_DIR or ~/.claude),
groups memory dirs into workspaces, resolves [[links]] between memories, and writes
one HTML file with no external dependencies.
"""
import argparse, datetime, json, os, pathlib, re

HERE = pathlib.Path(__file__).resolve().parent
# Folders people keep repos in; stripped so "~/Projects/acme-api" groups as "acme".
CONTAINERS = {"projects", "developer", "dev", "code", "src", "repos", "git", "github",
              "workspace", "workspaces", "work", "documents", "sites"}


def encode(path):
    """Claude Code names a project dir after its cwd with every non-alphanumeric char as '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def project_label(dirname, home_enc):
    """'-Users-ana-Projects-acme-api' -> 'acme-api'; the home dir itself -> 'home'."""
    if dirname == home_enc:
        return "home"
    label = dirname[len(home_enc) + 1:] if dirname.startswith(home_enc + "-") else dirname.lstrip("-")
    head, _, rest = label.partition("-")
    if head.lower() in CONTAINERS and rest:
        label = rest
    return label or "home"


def workspaces(labels):
    """Group labels under the shortest other label that prefixes them on a '-' boundary.

    ['acme', 'acme-api', 'acme-web', 'blog'] -> acme: acme, acme-api, acme-web; blog: blog.
    Dashes in folder names are ambiguous, so this only groups when the parent dir exists too.
    """
    out = {}
    for l in labels:
        parents = [p for p in labels if p != l and l.startswith(p + "-")]
        out[l] = min(parents, key=len) if parents else l
    return out


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^\s*([A-Za-z_]+):\s*(.*)$", line)  # also catches keys nested under metadata:
        if mm and mm.group(2).strip():
            fm.setdefault(mm.group(1), mm.group(2).strip().strip('"\''))
    return fm, m.group(2)


def build(root, home, bodies=True):
    home_enc = encode(home)
    raw = []
    for d in sorted(os.listdir(root)):
        mdir = root / d / "memory"
        # skip temp/scratch session dirs
        if not mdir.is_dir() or d.startswith(("-private-", "-tmp-", "-var-folders-")):
            continue
        files = [f for f in sorted(mdir.glob("*.md")) if f.name != "MEMORY.md"]
        if files:
            raw.append((project_label(d, home_enc), files))

    ws = workspaces([p for p, _ in raw])
    nodes, by_name, by_stem = [], {}, {}
    for proj, files in raw:
        for f in files:
            text = f.read_text(errors="replace")
            fm, body = frontmatter(text)
            n = {"id": f"{proj}/{f.stem}", "project": proj, "workspace": ws[proj],
                 "file": str(f).replace(str(home), "~", 1),
                 "name": fm.get("name", f.stem), "desc": fm.get("description", ""),
                 "type": fm.get("type", "unknown"),
                 "date": datetime.date.fromtimestamp(f.stat().st_mtime).isoformat(),
                 "size": len(text), "links": re.findall(r"\[\[([^\]|#]+)", body)}
            if bodies:
                n["body"] = body.strip()[:20000]  # cap: one runaway file shouldn't bloat the page
            nodes.append(n)
            by_name.setdefault(n["name"].lower(), []).append(n)
            by_stem.setdefault(f.stem.lower(), []).append(n)

    def resolve(target, src):
        t = target.strip().lower()
        cands = by_name.get(t, []) + by_stem.get(t, []) + by_stem.get(t.replace("-", "_"), [])
        same = [c for c in cands if c["project"] == src["project"]]
        return (same or cands or [None])[0]

    edges, dangling = [], 0
    for n in nodes:
        for l in n.pop("links"):
            t = resolve(l, n)
            if t is None:
                dangling += 1
            elif t["id"] != n["id"]:
                edges.append({"s": n["id"], "t": t["id"]})

    ids = {n["id"] for n in nodes}
    assert len(ids) == len(nodes), "duplicate node ids"
    assert all(e["s"] in ids and e["t"] in ids for e in edges), "edge to unknown node"
    return {"nodes": nodes, "edges": edges, "dangling": dangling,
            "built": datetime.date.today().isoformat()}


def main():
    config = pathlib.Path(os.environ.get("CLAUDE_CONFIG_DIR", pathlib.Path.home() / ".claude"))
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", nargs="?", default="memory-graph.html", help="output HTML path")
    ap.add_argument("--root", default=str(config / "projects"), help="Claude projects dir")
    ap.add_argument("--home", default=str(pathlib.Path.home()), help="home dir used to shorten labels")
    ap.add_argument("--no-bodies", action="store_true",
                    help="leave out memory text (names and descriptions only), e.g. for a graph you'll share")
    a = ap.parse_args()

    data = build(pathlib.Path(a.root).expanduser(), pathlib.Path(a.home).expanduser(), bodies=not a.no_bodies)
    out = pathlib.Path(a.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    # '</' would end the inline <script> early if a description contained '</script>'
    payload = json.dumps(data).replace("</", "<\\/")
    out.write_text((HERE / "template.html").read_text().replace("/*__DATA__*/null", payload))
    print(f"{len(data['nodes'])} memories, {len(data['edges'])} links, {data['dangling']} dangling, "
          f"{len({n['project'] for n in data['nodes']})} projects, "
          f"{len({n['workspace'] for n in data['nodes']})} workspaces -> {out}")


if __name__ == "__main__":
    main()
