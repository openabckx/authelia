"""Release sync orchestration. Git writes are fast-forward only; never merge a PR."""
import argparse
import json
import os
import pathlib
import re
import subprocess
from collections.abc import Callable


def api(method: str, endpoint: str, **fields):
    command = ["gh", "api", "--method", method, endpoint]
    if method == "GET":
        command += ["--paginate", "--slurp"]
    result = subprocess.run(command + (["--input", "-"] if fields else []),
                            input=json.dumps(fields) if fields else None,
                            text=True, check=True, capture_output=True)
    value = json.loads(result.stdout)
    if method == "GET":
        return ([item for page in value for item in page]
                if all(isinstance(page, list) for page in value) else value[0])
    return value


class Sync:
    def __init__(self, root: pathlib.Path, repository: str, request: Callable = api):
        self.root = root
        self.repository = repository
        self.request = request

    def git(self, *args: str) -> str:
        return subprocess.check_output(["git", "-C", str(self.root), *args],
                                       text=True, stderr=subprocess.STDOUT).strip()

    def push(self, source: str, target: str) -> None:
        # Token stays in the environment, not a URL, stored credential or argv.
        helper = ('!f() { if [ "$1" = get ]; then printf "%s\\n" '
                  '"username=x-access-token" "password=$GH_TOKEN"; fi; }; f')
        self.git("-c", "credential.helper=", "-c", f"credential.helper={helper}",
                 "push", "origin", f"{source}:refs/heads/{target}")
        expected = self.git("rev-parse", source)
        actual = self.git("ls-remote", "origin", f"refs/heads/{target}").split()[0]
        if actual != expected:
            raise RuntimeError(f"Push readback mismatch: {target}")

    def ancestor(self, old: str, new: str) -> bool:
        result = subprocess.run(["git", "-C", str(self.root), "merge-base",
                                 "--is-ancestor", old, new], check=False)
        if result.returncode not in (0, 1):
            raise RuntimeError("Cannot compare upstream ancestry")
        return result.returncode == 0

    def report(self, tag: str, reason: str, files: str, run: str = "") -> None:
        title = f"upstream {tag} {reason}"
        endpoint = f"repos/{self.repository}/issues"
        issues = self.request("GET", endpoint + "?state=open&labels=upstream-conflict&per_page=100")
        body = f"Owner: neo-dev. Manual review required.\n\n{run}\n\nAffected files:\n```text\n{files}\n```\n"
        existing = next((issue for issue in issues if issue["title"] == title), None)
        if existing is not None:
            if existing["body"] != body:
                self.request("PATCH", f"{endpoint}/{existing['number']}", body=body)
                saved = self.request("GET", f"{endpoint}/{existing['number']}")
                if saved["body"] != body:
                    raise RuntimeError("Conflict update readback mismatch")
            return
        # Creating the same label is unnecessary when it already exists.
        labels = self.request("GET", f"repos/{self.repository}/labels?per_page=100")
        if not any(label["name"] == "upstream-conflict" for label in labels):
            self.request("POST", f"repos/{self.repository}/labels",
                         name="upstream-conflict", color="d73a4a",
                         description="Upstream sync needs owner intervention")
        created = self.request("POST", endpoint, title=title,
                               labels=["upstream-conflict"],
                               body=body)
        if isinstance(created, dict) and "number" in created:
            saved = self.request("GET", f"{endpoint}/{created['number']}")
            if saved["title"] != title or "upstream-conflict" not in {label["name"] for label in saved["labels"]}:
                raise RuntimeError("Conflict issue readback mismatch")

    def prepare(self, tag: str) -> dict[str, str]:
        if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
            raise ValueError("Only stable upstream vX.Y.Z releases are supported")
        base, release, master = "origin/abckx", f"refs/tags/{tag}", "upstream/master"
        common = self.git("merge-base", base, release)
        workflow_files = set(self.git("diff", "--name-only", common, release,
                                      "--", ".github/workflows").splitlines())
        workflow_files.update(self.git("diff", "--name-only", "origin/master", master,
                                       "--", ".github/workflows").splitlines())
        if workflow_files:
            self.report(tag, "changes workflows: manual sync", "\n".join(sorted(workflow_files)))
            return {}
        if not self.ancestor("origin/master", master):
            self.report(tag, "master diverged: manual sync", "master (non-fast-forward)")
            return {}
        if self.ancestor(release, base):
            self.push(master, "master")
            return {}
        branch = f"upstream/{tag}"
        refs = self.git("for-each-ref", "--format=%(refname)", f"refs/remotes/origin/{branch}")
        self.git("checkout", "-B", branch, f"origin/{branch}" if refs else base)
        for target in (base, release):
            try:
                self.git("merge", "--no-edit", target)
            except subprocess.CalledProcessError:
                files = self.git("diff", "--name-only", "--diff-filter=U")
                if not files:
                    raise
                self.git("merge", "--abort")
                self.report(tag, "merge conflict", files)
                return {}
        workflows = self.git("diff", "--name-only", base, "HEAD", "--", ".github/workflows")
        if workflows:
            self.report(tag, "changes workflows: manual sync", workflows)
            return {}
        self.push(master, "master")
        self.push("HEAD", branch)
        return {"tag": tag, "branch": branch, "sha": self.git("rev-parse", "HEAD"),
                "files": self.git("diff", "--name-only", base, "HEAD")}

    def finish(self, state: dict[str, str], result: str, run: str) -> None:
        if not state:
            return
        if result != "success":
            self.report(state["tag"], "CI failed", state["files"], run)
            return
        remote = self.git("ls-remote", "origin", f"refs/heads/{state['branch']}").split()
        if not remote or remote[0] != state["sha"]:
            self.report(state["tag"], "candidate changed: retry sync", state["files"], run)
            return
        endpoint = f"repos/{self.repository}/pulls"
        pulls = self.request("GET", endpoint + "?state=open&base=abckx&per_page=100")
        for pr in pulls:
            head = pr["head"]
            if head["ref"] == state["branch"] and (head["repo"] or {}).get("full_name") == self.repository:
                if head["sha"] != state["sha"]:
                    raise RuntimeError("Existing sync PR does not match validated candidate")
                return
        pr = self.request("POST", endpoint, base="abckx", head=state["branch"], draft=False,
                          title=f"chore(upstream): sync to {state['tag']}",
                          body=f"Merge upstream {state['tag']} into abckx.\n\nFork CI passed for `{state['sha']}`: {run}\n\nGMUD: preserve fork customizations through a merge. Risk: upstream behavior changes. Rollback: revert the sync merge. Owner: neo-dev reviews and merges; no automatic deployment.\n")
        if isinstance(pr, dict) and "number" in pr:
            saved = self.request("GET", f"{endpoint}/{pr['number']}")
            if saved["head"]["sha"] != state["sha"] or saved["base"]["ref"] != "abckx":
                raise RuntimeError("Sync PR readback mismatch")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "finish"))
    args = parser.parse_args()
    root = pathlib.Path.cwd()
    runner = Sync(root, os.environ["GITHUB_REPOSITORY"])
    if args.mode == "prepare":
        release = subprocess.check_output(["gh", "api", "repos/authelia/authelia/releases/latest",
                                           "--jq", ".tag_name"], text=True).strip()
        if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", release):
            raise ValueError("Invalid latest stable release tag")
        runner.git("fetch", "https://github.com/authelia/authelia.git",
                   "master:refs/remotes/upstream/master",
                   f"refs/tags/{release}:refs/tags/{release}")
        state = runner.prepare(release)
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write(f"state={json.dumps(state)}\nsha={state.get('sha', '')}\n")
    else:
        runner.finish(json.loads(os.environ["SYNC_STATE"]), os.environ["CI_RESULT"],
                      f"{os.environ['GITHUB_SERVER_URL']}/{runner.repository}/actions/runs/{os.environ['GITHUB_RUN_ID']}")


if __name__ == "__main__":
    main()
