"""Generate a fictional memory set for demos, screenshots and the live demo page.

Writes demo/projects/<encoded-dir>/memory/*.md as if a developer "Ana" (home /Users/ana)
had used Claude Code across a few workspaces. Deterministic; safe to regenerate.

    python3 demo/make_demo.py && python3 build.py --root demo/projects --home /Users/ana demo/index.html
"""
import pathlib, random, shutil

ROOT = pathlib.Path(__file__).resolve().parent / "projects"
HOME = "-Users-ana"
rnd = random.Random(42)

# workspace dir suffix -> (topic words, memories per type)
PROJECTS = {
    "": ("home", ["Prefers short answers", "Works in Lisbon, UTC+0", "Uses pnpm everywhere",
                  "Commit messages in imperative mood", "Never push to main", "Asks for tests first"]),
    "-Projects-acme": ("acme", ["Acme is a B2B invoicing product", "Pricing page owned by marketing",
                                "Quarterly roadmap lives in Linear", "Design tokens come from Figma"]),
    "-Projects-acme-api": ("acme-api", ["Postgres 16 with row-level security", "Money stored in integer cents",
                                        "Webhooks retried with exponential backoff", "Rate limit is 100 req/min per key",
                                        "Auth uses short-lived JWTs", "Never log customer emails",
                                        "Migrations must be reversible", "Staging resets every Sunday"]),
    "-Projects-acme-web": ("acme-web", ["Next.js app router", "Tailwind with house tokens only",
                                        "Forms validated with zod", "Empty states need an illustration",
                                        "Dark mode is required for every screen", "Dates shown in the user's timezone"]),
    "-Projects-orbit": ("orbit", ["Orbit is a habit-tracking iOS app", "SwiftUI, iOS 17 minimum",
                                  "Streak logic is timezone-sensitive", "Notifications capped at 2 per day",
                                  "Widgets refresh every 30 min"]),
    "-Projects-orbit-sync": ("orbit-sync", ["CloudKit for sync", "Conflict rule: last write wins per field",
                                            "Offline queue persisted to disk"]),
    "-Projects-blog": ("blog", ["Posts written in MDX", "One post per month", "Code samples must run",
                                "Prefer diagrams over walls of text"]),
    "-Projects-dotfiles": ("dotfiles", ["zsh with starship prompt", "Neovim config in Lua", "Homebrew Brewfile is the source of truth"]),
}
TYPES = ["project", "feedback", "reference", "user"]


def slug(s):
    return "".join(c if c.isalnum() else "-" for c in s.lower()).strip("-")[:48]


def main():
    shutil.rmtree(ROOT, ignore_errors=True)
    names = []
    for suffix, (proj, facts) in PROJECTS.items():
        d = ROOT / (HOME + suffix) / "memory"
        d.mkdir(parents=True)
        for i, fact in enumerate(facts):
            t = "user" if proj == "home" and i < 2 else "feedback" if ("Never" in fact or "Prefer" in fact or "must" in fact) else rnd.choice(TYPES[:3])
            names.append((d, slug(fact), fact, t, proj))
    all_slugs = [n[1] for n in names]
    for d, s, fact, t, proj in names:
        # 1-3 links, biased toward the same workspace, so the graph has local clusters and a few bridges
        same = [x[1] for x in names if x[4].split("-")[0] == proj.split("-")[0] and x[1] != s]
        links = rnd.sample(same, min(len(same), rnd.randint(1, 2))) + ([rnd.choice(all_slugs)] if rnd.random() < .35 else [])
        body = (f"{fact}.\n\n**Why:** came up while working on {proj}; Ana confirmed it.\n\n"
                f"**How to apply:** follow this whenever touching {proj}.\n\n"
                + "Related: " + ", ".join(f"[[{l}]]" for l in dict.fromkeys(links) if l != s) + "\n")
        (d / f"{s}.md").write_text(
            f"---\nname: {s}\ndescription: {fact}\nmetadata:\n  type: {t}\n---\n\n{body}", encoding="utf-8")
        (d.parent / "memory" / "MEMORY.md").open("a", encoding="utf-8").write(f"- [{fact}]({s}.md)\n")
    print(f"{len(names)} demo memories in {len(PROJECTS)} projects -> {ROOT}")


if __name__ == "__main__":
    main()
