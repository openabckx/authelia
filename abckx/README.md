# Authelia fork image

`master` mirrors upstream. `abckx` carries the fork's branding and image workflow.
The image builds the checked-out `web/` and `cmd/authelia` sources. It does not
reuse the upstream application binary. The stages and hardening flags follow
upstream `Dockerfile.dev` and `cmd/authelia-scripts/cmd/build.go`, without dev tags
or coverage instrumentation. Runtime assets still use `server.asset_path`.

## Build and validate

Run from the repository root (the Dockerfile-specific ignore overrides the
upstream root ignore, which only admits prebuilt binaries):

```sh
docker build -f abckx/Dockerfile -t authelia-smoke:local .
python3 abckx/image-smoke.py --image authelia-smoke:local
python3 -m unittest discover -s abckx -v
```

The smoke starts the actual container with temporary SQLite/notifier storage,
checks its non-root UID and version, and verifies escaped branding attributes
and compiled portal assets in the login HTML. It does not authenticate a user.
The same probe accepts `--binary /path/to/authelia` for local source builds.
Set `EXPECTED_VERSION` when testing a non-default `VERSION` build argument.

The image defaults to UID/GID `1000:1000`. Make bind-mounted configuration
readable and storage/notifier directories writable by that identity. The image
does not repair host volume ownership at startup. A deployment can set its own
non-root UID/GID with the container runtime's `user` option.

## Publication and rollback

PRs against `abckx` build and smoke-test without registry login or publication.
Pushes to `abckx` publish an `abckx-<sha>` image after the same smoke. Tags named
`abckx-v<upstream-version>-<revision>` publish the version and `latest` tags.
For example, `abckx-v4.39.28-2` maps to `4.39.28-2`. The workflow derives the
lowercase GHCR owner from `github.repository_owner`, not a fixed organization.
Publication pushes the tested local image, rather than rebuilding after smoke.

Only the resident creates tags/releases and deploys. Preserve the previous
image digest for deployment rollback. Reverting this PR restores the previous
build workflow; it does not change an already published image or running service.

## Upstream workflow decisions (#3)

- `codeql-analysis`: guard upstream-only scheduled/master scanning. The fork's
  build validation lives in `abckx-ci`; this does not claim equivalent security scanning.
- `contributors`: guard upstream-only roster generation and bot commits.
- `pr-commentary`: guard upstream App secrets and Buildkite/DockerHub messages.
- `pr-labels`: guard upstream label and release-milestone policy.
- `scorecard`: guard upstream master/security-dashboard publication.
- `slsa-provenance`: retain unchanged. It only runs through `workflow_call` from
  the upstream release workflow and requires upstream Buildkite/DockerHub secrets.
- `slsa`: retain unchanged per the PO decision. Its upstream `v*` tag trigger
  does not match `abckx-v*`. The inherited invalid reusable-workflow reference
  is owned upstream and is explicitly outside this change.

`abckx-ci` checks the complete portal, builds both components, and tests the Go
configuration/server/template packages that implement the fork branding. The
canonical wider Go suite excludes `internal/suites`; its known model test
failures remain upstream debt, not exclusions added to the test code.
