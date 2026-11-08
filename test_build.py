"""Run: python3 -I test_build.py  (stdlib only)."""
import pathlib, sys, tempfile, unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build


def mem(root, project_dir, stem, body, name=None, type_="project"):
    d = root / project_dir / "memory"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{stem}.md").write_text(
        f"---\nname: {name or stem}\ndescription: about {stem}\nmetadata:\n  type: {type_}\n---\n{body}\n")


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        home = "-Users-ana"
        mem(self.root, home, "prefs", "likes [[api-auth]] and [[nowhere]]", type_="user")
        mem(self.root, f"{home}-Projects-acme", "vision", "see [[api-auth]]")
        mem(self.root, f"{home}-Projects-acme-api", "auth", "token rules", name="api-auth")
        mem(self.root, f"{home}-Projects-blog", "drafts", "x", type_="feedback")
        mem(self.root, "-private-tmp-scratch", "junk", "ignored")
        (self.root / f"{home}-Projects-acme" / "memory" / "MEMORY.md").write_text("- index")
        self.data = build.build(self.root, pathlib.Path("/Users/ana"))
        self.by_id = {n["id"]: n for n in self.data["nodes"]}

    def tearDown(self):
        self.tmp.cleanup()

    def test_labels_and_workspaces(self):
        self.assertEqual(set(self.by_id), {"home/prefs", "acme/vision", "acme-api/auth", "blog/drafts"})
        self.assertEqual(self.by_id["acme-api/auth"]["workspace"], "acme")
        self.assertEqual(self.by_id["blog/drafts"]["workspace"], "blog")

    def test_links_and_types(self):
        edges = {(e["s"], e["t"]) for e in self.data["edges"]}
        self.assertEqual(edges, {("home/prefs", "acme-api/auth"), ("acme/vision", "acme-api/auth")})
        self.assertEqual(self.data["dangling"], 1)
        self.assertEqual(self.by_id["home/prefs"]["type"], "user")  # nested under metadata:

    def test_bodies_included_unless_disabled(self):
        self.assertEqual(self.by_id["acme-api/auth"]["body"], "token rules")
        lean = build.build(self.root, pathlib.Path("/Users/ana"), bodies=False)
        self.assertTrue(all("body" not in n for n in lean["nodes"]))

    def test_non_ascii_and_windows_temp(self):
        mem(self.root, "C--Users-ana-Projects-café", "notas", "ação ◆ 🧠")
        mem(self.root, "C--Users-ana-AppData-Local-Temp-xyz", "junk", "ignored")
        data = build.build(self.root, pathlib.Path("C:\\Users\\ana"))
        by = {n["id"]: n for n in data["nodes"]}
        self.assertEqual(by["café/notas"]["body"], "ação ◆ 🧠")
        self.assertFalse(any(i.endswith("/junk") for i in by))

    def test_unrelated_prefix_not_grouped(self):
        self.assertEqual(build.workspaces(["acme", "acmecorp", "acme-web"]),
                         {"acme": "acme", "acmecorp": "acmecorp", "acme-web": "acme"})


if __name__ == "__main__":
    unittest.main()
