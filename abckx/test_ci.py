"""Fork build contracts; run with python3 -m unittest discover -s abckx."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ImageContract(unittest.TestCase):
    def test_only_production_env_template_is_restored_after_env_exclusion(self):
        patterns = (ROOT / "abckx/Dockerfile.dockerignore").read_text().splitlines()
        exceptions = [p for p in patterns if p.startswith("!") and "/.env" in p]
        self.assertEqual(["!web/.env.production"], exceptions)
        self.assertGreater(patterns.index("!web/.env.production"), patterns.index("**/.env.*"))

    def test_generated_bundle_is_checked_and_browser_smoke_is_mandatory(self):
        recipe = (ROOT / "abckx/Dockerfile").read_text()
        self.assertIn("grep -rF '%VITE_BASEPATH%'", recipe)
        workflow = (ROOT / ".github/workflows/abckx-image.yml").read_text()
        self.assertIn("playwright install --with-deps chromium", workflow)
        smoke = (ROOT / "abckx/image-smoke.py").read_text()
        self.assertIn('"browser-smoke.mjs"', smoke)

    def test_image_builds_both_sources_as_nonroot(self):
        recipe = (ROOT / "abckx/Dockerfile").read_text()
        self.assertIn("pnpm build", recipe)
        self.assertIn("./cmd/authelia", recipe)
        self.assertIn("BuildTag", recipe)
        self.assertRegex(recipe, r"(?m)^USER [1-9][0-9]*:[1-9][0-9]*$")
        self.assertNotRegex(recipe, r"(?m)^FROM authelia/authelia:")
        self.assertNotIn("-tags dev", recipe)

    def test_context_includes_source_but_excludes_host_artifacts(self):
        ignore = ROOT / "abckx/Dockerfile.dockerignore"
        self.assertTrue(ignore.exists(), "root .dockerignore excludes source")
        patterns = ignore.read_text().splitlines()
        for required in ("!web/**", "!internal/**", "!cmd/**", "!go.mod", "!go.sum"):
            self.assertIn(required, patterns)
        for excluded in ("**/node_modules", "**/.env", "**/.env.*", "**/coverage"):
            self.assertIn(excluded, patterns)


class WorkflowContract(unittest.TestCase):
    def test_image_uses_owner_and_safe_pr_validation(self):
        workflow = (ROOT / ".github/workflows/abckx-image.yml").read_text()
        self.assertIn("github.repository_owner", workflow)
        self.assertNotIn("abckxopen", workflow)
        for required in ("branches: [abckx]", "abckx-v*", "pull_request:",
                         "context: .", "load: true", "image-smoke.py",
                         "github.event_name != 'pull_request'"):
            self.assertIn(required, workflow)
        for action in re.findall(r"uses: (\S+)", workflow):
            self.assertRegex(action, r"@[0-9a-f]{40}$")

    def test_version_has_one_source_for_metadata_and_binary(self):
        workflow = (ROOT / ".github/workflows/abckx-image.yml").read_text()
        self.assertIn("type=raw,value=${{ steps.version.outputs.version }}", workflow)
        self.assertNotIn("type=sha", workflow)
        self.assertIn("VERSION=${{ steps.version.outputs.version }}", workflow)

    def test_pr_build_typecheck_and_test_gate_exists(self):
        path = ROOT / ".github/workflows/abckx-ci.yml"
        self.assertTrue(path.exists(), "fork PRs need their own validation")
        workflow = path.read_text()
        for required in ("pull_request:", "branches: [abckx]", "go build",
                         "pnpm build", "tsc --noEmit", "pnpm test", "go test"):
            self.assertIn(required, workflow)
        self.assertNotIn("continue-on-error", workflow)
        for action in re.findall(r"uses: (\S+)", workflow):
            self.assertRegex(action, r"@[0-9a-f]{40}$")

    def test_upstream_automation_is_guarded(self):
        for name in ("codeql-analysis", "contributors", "pr-commentary", "pr-labels", "scorecard"):
            with self.subTest(workflow=name):
                text = (ROOT / f".github/workflows/{name}.yml").read_text()
                self.assertIn("if: github.repository == 'authelia/authelia'", text)


if __name__ == "__main__":
    unittest.main()
