"""Exercise the manifest gate against real Git history, not mocked diff output."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHECKER = ROOT / "abckx/check_patch_manifest.py"


class PatchManifestTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = pathlib.Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Fixture")
        for name in ("modified.go", "deleted.go", "renamed.go", "unchanged.go"):
            (self.repo / name).write_text("upstream\n")
        self.commit()
        self.git("branch", "mirror")
        (self.repo / "modified.go").write_text("custom\n")
        (self.repo / "deleted.go").unlink()
        self.git("mv", "renamed.go", "new name.go")
        (self.repo / "added.go").write_text("fork\n")
        (self.repo / "abckx").mkdir()
        (self.repo / "abckx/owned.py").write_text("# fork-owned\n")
        self.commit()
        self.paths = {"modified.go", "deleted.go", "renamed.go", "new name.go", "added.go"}
        self.manifest = self.repo / "abckx/PATCHES.md"

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, check=True,
                              capture_output=True, text=True)

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "fixture")

    def run_gate(self):
        return subprocess.run([sys.executable, str(CHECKER), "--base", "mirror"],
                              cwd=self.repo, capture_output=True, text=True)

    def write_manifest(self, paths):
        self.manifest.write_text("| File | Hook | Why | Issue/PR | Covering test |\n"
                                 "|---|---|---|---|---|\n" + "".join(
            f"| `{p}` | Hook | Reason | #22 | fixture |\n" for p in sorted(paths)))

    def test_all_change_types_and_fork_owned_exclusion(self):
        self.write_manifest(self.paths)
        result = self.run_gate()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("5 changed paths covered", result.stdout)

    def test_each_unlisted_path_is_reported(self):
        for path in self.paths:
            with self.subTest(path=path):
                self.write_manifest(self.paths - {path})
                result = self.run_gate()
                self.assertEqual(1, result.returncode)
                self.assertIn(path, result.stderr)

    def test_prose_and_prefix_matches_do_not_count(self):
        self.write_manifest({p + ".extra" for p in self.paths})
        with self.manifest.open("a") as stream:
            stream.write("Mentioned in prose: " + ", ".join(self.paths))
        self.assertEqual(1, self.run_gate().returncode)

    def test_missing_manifest_fails_closed(self):
        result = self.run_gate()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("PATCHES.md", result.stderr)

    def test_missing_mirror_fails_closed(self):
        self.write_manifest(self.paths)
        self.git("branch", "-D", "mirror")
        result = self.run_gate()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("mirror", result.stderr)

    def test_empty_diff_passes_with_manifest(self):
        self.write_manifest(set())
        self.git("branch", "-f", "mirror", "HEAD")
        result = self.run_gate()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("0 changed paths covered", result.stdout)

    def test_mirror_only_changes_are_not_fork_patches(self):
        fork = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("checkout", "-q", "mirror")
        (self.repo / "upstream-new.go").write_text("upstream update\n")
        self.commit()
        self.git("checkout", "-q", "--detach", fork)
        self.write_manifest(self.paths)
        result = self.run_gate()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("5 changed paths covered", result.stdout)

    def test_ci_fetches_history_and_runs_gate(self):
        workflow = (ROOT / ".github/workflows/abckx-ci.yml").read_text()
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("python3 abckx/check_patch_manifest.py --base origin/master", workflow)


if __name__ == "__main__":
    unittest.main()
