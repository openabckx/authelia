"""Exercise sync decisions against real Git repositories, without network writes."""
import importlib.util
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("upstream_sync", ROOT / "abckx/upstream_sync.py")
assert SPEC is not None and SPEC.loader is not None
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.upstream = self.root / "upstream"
        self.upstream.mkdir()
        self.git(self.upstream, "init", "-b", "master")
        self.git(self.upstream, "config", "user.name", "Fixture")
        self.git(self.upstream, "config", "user.email", "fixture@example.com")
        self.commit(self.upstream, "app.txt", "base\n")
        self.git(self.upstream, "tag", "v1.0.0")
        self.origin = self.root / "origin.git"
        self.git(self.root, "clone", "--bare", str(self.upstream), str(self.origin))
        self.repo = self.root / "fork"
        self.git(self.root, "clone", str(self.origin), str(self.repo))
        self.git(self.repo, "config", "user.name", "Fixture")
        self.git(self.repo, "config", "user.email", "fixture@example.com")
        self.git(self.repo, "checkout", "-b", "abckx")
        self.commit(self.repo, "brand.txt", "fork\n")
        self.git(self.repo, "push", "origin", "abckx")
        self.git(self.repo, "remote", "add", "upstream", str(self.upstream))
        self.api = Mock()
        self.api.return_value = []
        self.runner = sync.Sync(self.repo, "openabckx/authelia", self.api)

    @staticmethod
    def git(repo, *args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True,
                                       stderr=subprocess.STDOUT).strip()

    def commit(self, repo, name, text):
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        self.git(repo, "add", name)
        self.git(repo, "commit", "-m", "fixture")

    def release(self, name="app.txt", text="upstream\n"):
        self.commit(self.upstream, name, text)
        self.git(self.upstream, "tag", "v1.1.0")
        self.git(self.repo, "fetch", "upstream", "master:refs/remotes/upstream/master",
                 "refs/tags/v1.1.0:refs/tags/v1.1.0")

    def test_clean_release_merges_and_mirrors_then_repeat_reuses_branch(self):
        self.release()
        first = self.runner.prepare("v1.1.0")
        self.assertEqual("upstream/v1.1.0", first["branch"])
        self.assertEqual("fork", (self.repo / "brand.txt").read_text().strip())
        self.assertEqual("upstream", (self.repo / "app.txt").read_text().strip())
        self.assertEqual(self.git(self.upstream, "rev-parse", "HEAD"),
                         self.git(self.origin, "rev-parse", "master"))
        self.git(self.repo, "fetch", "origin")
        second = self.runner.prepare("v1.1.0")
        self.assertEqual(first["sha"], second["sha"])

    def test_current_release_does_not_create_scratch_branch(self):
        self.git(self.repo, "fetch", "upstream", "master:refs/remotes/upstream/master")
        self.assertEqual({}, self.runner.prepare("v1.0.0"))
        self.assertEqual([], self.api.call_args_list)

    def test_conflict_reports_file_without_pushing_scratch(self):
        self.commit(self.repo, "app.txt", "fork version\n")
        self.git(self.repo, "push", "origin", "abckx")
        self.release()
        self.assertEqual({}, self.runner.prepare("v1.1.0"))
        calls = str(self.api.call_args_list)
        self.assertIn("app.txt", calls)
        self.assertIn("upstream-conflict", calls)
        self.assertEqual("", self.git(self.origin, "for-each-ref", "refs/heads/upstream/"))

    def test_workflow_change_stops_all_pushes_and_lists_file(self):
        before = self.git(self.origin, "rev-parse", "master")
        self.release(".github/workflows/upstream.yml", "name: upstream\n")
        self.assertEqual({}, self.runner.prepare("v1.1.0"))
        self.assertEqual(before, self.git(self.origin, "rev-parse", "master"))
        self.assertIn("changes workflows: manual sync", str(self.api.call_args_list))
        self.assertIn(".github/workflows/upstream.yml", str(self.api.call_args_list))

    def test_master_only_workflow_change_is_also_blocked(self):
        self.release()
        self.commit(self.upstream, ".github/workflows/next.yml", "name: next\n")
        self.git(self.repo, "fetch", "upstream", "master:refs/remotes/upstream/master")
        self.assertEqual({}, self.runner.prepare("v1.1.0"))
        self.assertIn(".github/workflows/next.yml", str(self.api.call_args_list))

    def test_existing_conflict_issue_is_not_duplicated(self):
        body = "Owner: neo-dev. Manual review required.\n\n\n\nAffected files:\n```text\n.github/workflows/upstream.yml\n```\n"
        self.api.return_value = [{"title": "upstream v1.1.0 changes workflows: manual sync", "body": body, "number": 7}]
        self.release(".github/workflows/upstream.yml", "name: upstream\n")
        self.runner.prepare("v1.1.0")
        self.assertFalse(any(c.args[0] == "POST" for c in self.api.call_args_list))

    def test_red_ci_opens_issue_not_pr_and_green_opens_one_pr(self):
        self.release()
        state = self.runner.prepare("v1.1.0")
        self.api.reset_mock()
        self.runner.finish(state, "failure", "https://example.com/run")
        self.assertIn("CI failed", str(self.api.call_args_list))
        self.assertNotIn("/pulls", str(self.api.call_args_list))
        self.api.reset_mock()
        self.runner.finish(state, "success", "https://example.com/run")
        posts = [c for c in self.api.call_args_list if c.args[0] == "POST"]
        self.assertEqual(1, len(posts))
        self.assertEqual("abckx", posts[0].kwargs["base"])
        self.assertEqual("upstream/v1.1.0", posts[0].kwargs["head"])
        self.api.reset_mock()
        self.api.return_value = [{"head": {"ref": state["branch"], "sha": state["sha"], "repo": {"full_name": "openabckx/authelia"}}}]
        self.runner.finish(state, "success", "https://example.com/run")
        self.assertFalse(any(c.args[0] == "POST" for c in self.api.call_args_list))

    def test_stale_ci_state_cannot_open_pr(self):
        self.release()
        state = self.runner.prepare("v1.1.0")
        self.commit(self.repo, "later.txt", "not validated\n")
        self.git(self.repo, "push", "origin", state["branch"])
        self.runner.finish(state, "success", "https://example.com/old-run")
        self.assertIn("candidate changed", str(self.api.call_args_list))
        self.assertFalse(any(c.args[1].endswith("/pulls") for c in self.api.call_args_list))

    def test_foreign_fork_branch_does_not_suppress_sync_pr(self):
        self.release()
        state = self.runner.prepare("v1.1.0")
        self.api.return_value = [{"head": {"ref": state["branch"], "repo": {"full_name": "other/authelia"}}}]
        self.runner.finish(state, "success", "https://example.com/run")
        self.assertTrue(any(c.args[0] == "POST" and c.args[1].endswith("/pulls")
                            for c in self.api.call_args_list))

    def test_existing_candidate_workflows_stop_before_master_push(self):
        self.git(self.repo, "checkout", "-b", "upstream/v1.1.0")
        self.commit(self.repo, ".github/workflows/extra.yml", "name: candidate\n")
        self.git(self.repo, "push", "origin", "upstream/v1.1.0")
        self.git(self.repo, "fetch", "origin")
        before = self.git(self.origin, "rev-parse", "master")
        self.release()
        self.assertEqual({}, self.runner.prepare("v1.1.0"))
        self.assertEqual(before, self.git(self.origin, "rev-parse", "master"))
        self.assertIn(".github/workflows/extra.yml", str(self.api.call_args_list))

    def test_retried_conflict_updates_diagnostics_without_duplicate(self):
        body = "Owner: neo-dev. Manual review required.\n\nnew-run\n\nAffected files:\n```text\nnew.txt\n```\n"
        self.api.side_effect = [
            [{"title": "upstream v1.1.0 CI failed", "body": "old", "number": 7}],
            {"number": 7}, {"body": body},
        ]
        self.runner.report("v1.1.0", "CI failed", "new.txt", "new-run")
        self.assertEqual("PATCH", self.api.call_args_list[1].args[0])
        self.assertEqual(body, self.api.call_args_list[1].kwargs["body"])

    def test_diverged_master_is_not_force_pushed(self):
        self.git(self.repo, "checkout", "master")
        self.commit(self.repo, "mirror-only.txt", "diverged\n")
        self.git(self.repo, "push", "origin", "master")
        self.git(self.repo, "fetch", "origin")
        self.release()
        before = self.git(self.origin, "rev-parse", "master")
        self.assertEqual({}, self.runner.prepare("v1.1.0"))
        self.assertEqual(before, self.git(self.origin, "rev-parse", "master"))
        self.assertIn("master diverged", str(self.api.call_args_list))

    def test_invalid_release_tag_is_rejected_before_git(self):
        with self.assertRaises(ValueError):
            self.runner.prepare("--upload-pack=evil")
        self.assertFalse(self.api.called)


class ApiTests(unittest.TestCase):
    @patch.object(sync.subprocess, "run")
    def test_paginated_lists_and_single_object_readback(self, run):
        run.return_value.stdout = '[[{"number":1}],[{"number":2}]]'
        self.assertEqual([{"number": 1}, {"number": 2}], sync.api("GET", "repos/o/r/issues"))
        self.assertIn("--paginate", run.call_args.args[0])
        run.return_value.stdout = '[{"number":1,"title":"saved"}]'
        self.assertEqual({"number": 1, "title": "saved"}, sync.api("GET", "repos/o/r/issues/1"))

    @patch.object(sync.subprocess, "run")
    def test_writes_use_json_input_and_failures_propagate(self, run):
        run.return_value.stdout = '{"number":1}'
        self.assertEqual({"number": 1}, sync.api("POST", "repos/o/r/pulls", draft=False, base="abckx"))
        self.assertEqual('{"draft": false, "base": "abckx"}', run.call_args.kwargs["input"])
        self.assertTrue(run.call_args.kwargs["check"])
        self.assertNotIn("--paginate", run.call_args.args[0])
        run.side_effect = subprocess.CalledProcessError(1, "gh")
        with self.assertRaises(subprocess.CalledProcessError):
            sync.api("GET", "repos/o/r/issues")


class WorkflowTests(unittest.TestCase):
    def test_schedule_and_readonly_reusable_ci_validate_exact_commit(self):
        workflow = (ROOT / ".github/workflows/abckx-upstream.yml").read_text()
        for text in ("schedule:", "workflow_dispatch:", "cancel-in-progress: false",
                     "uses: ./.github/workflows/abckx-ci.yml", "if: always()",
                     "needs.validate.result", "persist-credentials: false"):
            self.assertIn(text, workflow)
        ci = (ROOT / ".github/workflows/abckx-ci.yml").read_text()
        self.assertIn("workflow_call:", ci)
        self.assertIn("ref: ${{ inputs.ref || github.sha }}", ci)
        self.assertNotIn("secrets: inherit", workflow)


if __name__ == "__main__":
    unittest.main()
