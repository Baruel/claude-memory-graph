"""Generate a fictional memory set for demos, screenshots and the live demo page.

Writes demo/projects/<encoded-dir>/memory/*.md as if a developer "Ana" (home /Users/ana),
who names every project after a show she's watching, had used Claude Code for a while.
Original jokes only; no quotes from the shows. Deterministic; safe to regenerate.

    python3 demo/make_demo.py && python3 build.py --root demo/projects --home /Users/ana docs/index.html
"""
import pathlib, random, shutil

ROOT = pathlib.Path(__file__).resolve().parent / "projects"
HOME = "-Users-ana"
rnd = random.Random(7)

# dir suffix -> (label, why, how, [(memory, type), ...])
PROJECTS = {
    "": ("home", "Ana said so, firmly", "every session, every repo", [
        ("Ana rewatches Attack on Titan every winter and is unreachable for a week", "user"),
        ("Zero spoilers for anything she hasn't finished, including in commit messages", "feedback"),
        ("Prefers answers short enough to read during an opening theme", "feedback"),
        ("Names every project after whatever show she is bingeing", "user"),
        ("Calls a long debugging session 'a filler arc'", "user"),
    ]),
    "-Projects-jujutsu-tech": ("jujutsu-tech", "the last outage was a special-grade curse", "before any change to the sorcery layer", [
        ("Domain Expansion is just a feature flag that takes over the whole screen", "project"),
        ("Cursed energy budget is the API rate limit, 100 per minute", "reference"),
        ("Never unseal the legacy monolith without the strongest engineer on call", "feedback"),
        ("Binding vows are SLAs: promise less, ship more", "feedback"),
        ("The cursed technique registry lives in config/techniques.yaml", "reference"),
    ]),
    "-Projects-jujutsu-tech-domain": ("jujutsu-tech-domain", "a domain clash once deadlocked prod", "whenever two domains could overlap", [
        ("Two domain expansions at once means a race condition", "project"),
        ("Simple Domain is the fallback when the feature flag service is down", "project"),
        ("Infinity is not a valid timeout value, use 30 seconds", "feedback"),
    ]),
    "-Projects-apothecary": ("apothecary", "the palace reviews every incident report", "anything that ships to the inner court", [
        ("Every dependency is taste-tested for poison before it reaches the palace", "feedback"),
        ("The apothecary trusts lab results, never rumors from the inner court", "feedback"),
        ("Herb inventory schema has a strict 'is_poisonous' column", "project"),
        ("Pharmacy notes live in docs/remedies/, one file per ailment", "reference"),
    ]),
    "-Projects-apothecary-poison-api": ("apothecary-poison-api", "a mislabeled herb cost a whole sprint", "every new endpoint", [
        ("Endpoints return 'probably poison' instead of guessing, with a confidence score", "project"),
        ("Suspicious payloads go to a sandbox before anyone tastes them", "feedback"),
        ("Rate limit poison checks: even the palace has budgets", "reference"),
    ]),
    "-Projects-scout-regiment": ("scout-regiment", "the last migration breached Wall Maria", "anything beyond the walls", [
        ("Never deploy beyond the walls on a Friday", "feedback"),
        ("The walls are the firewall; the gate is the API gateway", "project"),
        ("Every expedition gets a rollback plan and a horse", "feedback"),
        ("Titan sightings are logged in the incident channel, not DMs", "reference"),
        ("Cadets get read-only access until graduation", "project"),
    ]),
    "-Projects-westeros": ("westeros", "the realm has long memories and longer winters", "anything touching the throne service", [
        ("Winter is coming means the on-call rotation starts", "project"),
        ("Never accept a merge request titled 'wedding'", "feedback"),
        ("The Night King is legacy code: nobody knows who wrote it", "project"),
        ("Ravens are the message queue, and some of them never arrive", "reference"),
        ("Every house keeps its own fork; the throne is main", "project"),
        ("Dragons are expensive GPUs: feed them, never anger them", "feedback"),
    ]),
    "-Projects-true-detective": ("true-detective", "the case files never close on their own", "every investigation", [
        ("Time is a flat circle, and so is this cron job", "project"),
        ("Bug reports are written like a long drive through Louisiana", "user"),
        ("Interview the logs separately; they tell different stories", "feedback"),
        ("Keep the evidence board in docs/case-board.md", "reference"),
    ]),
    "-Projects-dark": ("dark", "a cache once returned data from 33 years ago", "anything involving time", [
        ("Every cache key includes the year, just in case", "feedback"),
        ("The question is not where the bug is, but when", "project"),
        ("Timezones are handled by the cave, do not go in alone", "reference"),
    ]),
}


def slug(s):
    s = "".join(c if c.isalnum() else "-" for c in s.lower().replace("'", ""))
    return "-".join(filter(None, s.split("-")))[:56].strip("-")


def main():
    shutil.rmtree(ROOT, ignore_errors=True)
    mems = []
    for suffix, (label, why, how, items) in PROJECTS.items():
        d = ROOT / (HOME + suffix) / "memory"
        d.mkdir(parents=True)
        for text, t in items:
            mems.append(dict(d=d, slug=slug(text), text=text, type=t, label=label, why=why, how=how))
    family = lambda m: m["label"].split("-")[0]
    for m in mems:
        # 1-2 links inside the same universe, plus the occasional crossover episode
        same = [x["slug"] for x in mems if family(x) == family(m) and x is not m]
        links = rnd.sample(same, min(len(same), rnd.randint(1, 2)))
        if rnd.random() < .3:
            links.append(rnd.choice([x["slug"] for x in mems if family(x) != family(m)]))
        body = (f"{m['text']}.\n\n**Why:** {m['why']}.\n\n**How to apply:** {m['how']}.\n\n"
                "Related: " + ", ".join(f"[[{l}]]" for l in dict.fromkeys(links)) + "\n")
        (m["d"] / f"{m['slug']}.md").write_text(
            f"---\nname: {m['slug']}\ndescription: {m['text']}\nmetadata:\n  type: {m['type']}\n---\n\n{body}",
            encoding="utf-8")
        with (m["d"] / "MEMORY.md").open("a", encoding="utf-8") as idx:
            idx.write(f"- [{m['text']}]({m['slug']}.md)\n")
    print(f"{len(mems)} demo memories in {len(PROJECTS)} projects -> {ROOT}")


if __name__ == "__main__":
    main()
