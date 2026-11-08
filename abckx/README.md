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
and compiled portal assets in the login HTML. It authenticates only a temporary,
randomly generated fixture user to check the Settings app bar.
The same probe accepts `--binary /path/to/authelia` for local source builds.
Set `EXPECTED_VERSION` when testing a non-default `VERSION` build argument.

The image defaults to UID/GID `1000:1000`. Make bind-mounted configuration
readable and storage/notifier directories writable by that identity. The image
does not repair host volume ownership at startup. A deployment can set its own
non-root UID/GID with the container runtime's `user` option.

## Portal accent (#15)

Set a quoted opaque six-digit hex color in Compose, then restart:

```yaml
environment:
  AUTHELIA_BRANDING_PRIMARY_COLOR: '#e91e63'
```

The YAML equivalent is `branding.primary_color: '#e91e63'`. Short hex, alpha,
color names and CSS expressions are rejected at startup. Unset or empty preserves
upstream colors, including grey. The runtime nonce-authorized stylesheet changes
buttons, links, focus rings and the Settings app bar in light/dark/grey/oled.
White or near-black foreground is selected for at least WCAG AA 4.5:1 contrast
on the accent. Arbitrary accent text against page backgrounds still needs an
operator accessibility check; not every color is readable on every background.
No frontend rebuild is needed after installing an image with this feature.
Rollback: remove the variable/YAML value and restart; duration NOT MEASURED.

The existing image smoke now authenticates a disposable generated test user and
checks computed accent colors at 390×844 across all four themes, without relaxing
CSP or mocking API responses. Docker execution remains in image CI.

## Local portal background (#16)

The image ships no wallpaper. Mount your company's official `background.png`
into `/abckx/assets/` and enable the flag below. Unset/false or an absent file
keeps the upstream plain background. No generated brand artwork is shipped.
The official company logo remains on the login card.

```yaml
environment:
  AUTHELIA_BRANDING_BACKGROUND_IMAGE: 'true'
  AUTHELIA_BRANDING_BACKGROUND_OPACITY: '0.25'
  AUTHELIA_BRANDING_BACKGROUND_BLUR: '0'
volumes:
  - ./company-background.png:/abckx/assets/background.png:ro
```

Use a readable official company PNG file, never a remote URL. Without the mount,
the portal stays plain. The mount adds one file; official logo/favicon remain.
A custom `AUTHELIA_SERVER_ASSET_PATH` directory must contain `background.png`.
If that file is absent at startup, the portal stays plain without an image request.
Restart after changing the mount or settings. Missing files do not block login.

YAML equivalents: `branding.background_image`, `branding.background_opacity`,
`branding.background_blur`. Opacity is image visibility over the upstream theme
(0..1 inclusive, default 0.25); blur is pixels (0..20 inclusive, default 0).
Invalid or non-finite numbers refuse startup. Zero opacity is not an unset value.
The fixed same-origin image URL uses the existing base URL and asset middleware.
The existing nonce-authorized style also gives login-stage cards an opaque theme
background; image opacity/blur never apply to card content. No CSP change.

The smoke runs the image's plain default, mounted neutral fixture, mounted
override, missing and disabled cases. The neutral test PNG lives in
`abckx/testdata/`, which is not copied into the runtime image. Chromium
checks loaded dimensions, computed image/blur/opacity and opaque cards in all
four themes. It requires AA card text contrast in light/dark/oled; inherited grey
measures 4.39:1 and is not repaired here. Authentication, Settings and console
checks still cover every theme. Custom accent text needs the operator contrast
check described above.
Rollback: set `AUTHELIA_BRANDING_BACKGROUND_IMAGE: 'false'` and restart, or restore
the previous image digest. Rollback duration and production rendering: NOT MEASURED.

## Notification branding (#14)

The image ships `abckx/templates/` through `AUTHELIA_NOTIFIER_TEMPLATE_PATH`.
These six operator-owned overrides use inline styles and a light 600px table
card, retaining security fields and revocation URLs. Explicit template maps
translate the documented runtime titles, event fragments and detail keys/values.
User-provided descriptions and unknown future strings remain unchanged. Keep
these maps current when upstream adds notification events. Buttons use PT-BR labels.

SMTP subject localization is separately opt-in: set `ABCKX_EMAIL_SUBJECT_PT_BR=true`
and restart. Only `{title}` is translated; the configured prefix is preserved.
Unset/false retains upstream behavior. Filesystem subjects remain upstream text.
The one-line SMTP hook and fork-owned helper are inventoried in `PATCHES.md`.
Upstream localization requests: [#11742](https://github.com/authelia/authelia/issues/11742)
and [#12333](https://github.com/authelia/authelia/issues/12333). No general i18n engine
or event/authentication changes are included in this fork.

- `ABCKX_EMAIL_LOGO_URL`: absolute HTTPS image URL, normally the login host's
  `/static/media/logo.png`. Empty/unset means no image, only the iAvançada header.
- `ABCKX_EMAIL_ENV_BANNER`: environment text, e.g. `srv-DEV-04`. Empty/unset means
  no band. Nonempty values appear above the HTML header and on the first TXT line.
- `AUTHELIA_BRANDING_TEXT` / `AUTHELIA_BRANDING_URL`: existing footer controls.
  Unset text uses the iAvançada footer; explicitly empty text hides the footer.
- Override `AUTHELIA_NOTIFIER_TEMPLATE_PATH` with another complete template
  directory to replace the overlay. Restore the previous image digest to roll back.
  Already sent emails cannot be recalled. Rollback duration: NOT MEASURED.

Templates are UTF-8 with CRLF, including on Linux. Run `go test ./abckx` from
repo root. Set `ABCKX_PTBR_PREVIEW_DIR` to an absolute output directory to render
four PT-BR HTML previews (three types plus password changed) through the real provider.
The older `ABCKX_EMAIL_PREVIEW_DIR` probe remains available for unknown-string fixtures.
The committed `previews/` files use example.com links and a sample code, never real credentials.
Mailbox-client rendering and spam placement remain tester-owned after image deployment.

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

## Upstream release sync (#17)

`abckx-upstream` runs daily at 04:23 UTC and through **Run workflow** on `abckx`.
**Activation prerequisite:** an org admin must make `abckx` the default branch;
GitHub schedules and manual-dispatch discovery use the default branch. Neo-dev
owns this setting and must allow GitHub Actions to create pull requests. Until
then, the schedule is not active. Never install fork automation onto `master`.

The workflow fetches `authelia/authelia` master and the latest stable `vX.Y.Z`
release. It fast-forwards the pure `master` mirror, without rewriting history,
and merges a new release into `upstream/vX.Y.Z` from `abckx`. Existing candidates
are updated by merge only. An already-integrated release creates no candidate.
The reusable `abckx-ci` validates the exact candidate SHA with read-only access.
A green result opens one `chore(upstream): sync to vX.Y.Z` PR against `abckx`;
neo-dev reviews and merges. No automatic release, tag, image or deployment.

`GITHUB_TOKEN` pushes/PRs do not trigger ordinary push/pull_request workflows.
The explicit reusable CI call is therefore mandatory, not a reliance on PR events.
Its coverage is the full fork CI described below. An owner may need to trigger additional required PR checks under
the repository's policy before merge; the automation never bypasses that policy.

If upstream changes `.github/workflows/**` in either the release or the master
mirror, or the actual candidate would change workflow files, **no branch is
pushed**. A labeled `upstream-conflict` issue titled
`upstream vX.Y.Z changes workflows: manual sync` lists the files. This is the
approved token-only exception: neo-dev performs manual sync with its own approved
workflow-write identity. Do not add a PAT/App secret or silently omit those files.
A diverged mirror, merge conflicts or red/cancelled CI also open an issue with the
affected files and, for CI failures, the run link. Repeated failures reuse the
issue and refresh changed diagnostics. Fix the cause and run the workflow again.
Scratch branches are retained for diagnosis and reused, not force-pushed. A stale
CI result cannot open a new PR after the candidate branch has moved.

Only preparation gets `contents: write`; preparation/final reporting get
`issues: write`; only final reporting gets `pull-requests: write`. All other
permissions are disabled; validation gets only `contents: read`. All actions are
SHA-pinned. The token is passed through an ephemeral credential helper, never a
remote URL or stored credential. Concurrent sync runs are serialized.

Local regression tests use real disposable Git repositories and mocked GitHub API
boundaries: `python3 -m unittest discover -s abckx -v`. No local test writes to
GitHub. Validate YAML with `actionlint`. First live acceptance: after admin
activation, neo-dev runs **Run workflow**, checks mirror SHA and either the sync
PR plus its candidate-specific CI link or the manual-sync issue/file list, then
runs again to confirm no duplicate. Live activation/token permissions remain
NOT MEASURED until that run. Rollback: disable `abckx-upstream` or revert #17;
close an unwanted sync PR and remove its scratch branch only after diagnosis.
Already mirrored upstream commits remain upstream commits. No running service is
changed. Rollback duration: NOT MEASURED.

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

## Required PR validation (#18)

Every PR against `abckx`, push to `abckx`, and reusable sync candidate runs
`abckx-ci`. Branding must not break authentication outside the branding packages.
The unit commands follow upstream's
[`cmd/authelia-scripts/cmd/unittest.go`](https://github.com/authelia/authelia/blob/master/cmd/authelia-scripts/cmd/unittest.go):

```sh
set -o pipefail
packages=$(go list ./... | grep -v suites)
set +e
TZ=UTC go test -coverprofile=coverage.txt -covermode=atomic -race -json -count=1 $packages > go-tests.jsonl 2>&1
status=$?
set -e
python3 abckx/check_go_results.py go-tests.jsonl abckx/known-upstream-failures.txt "$status"
cd web && CI=true pnpm test
```

The Go command includes all fork packages and upstream units, with Buildkite's
race detector and atomic coverage. Only upstream's `suites` integration corpus is
excluded; no individual test is skipped. JSON output and an uncached run support
an exact failure ratchet approved in [#18](https://github.com/openabckx/authelia/issues/18#issuecomment-6715821327).
`abckx/known-upstream-failures.txt` records each package/leaf test, reason and
observed upstream commit. Six timezone-related subtests reproduce on clean
upstream master `aafb20467142d57f2445f0f0ef62c2643055700d` with Go 1.27.3 and
`TZ=UTC`; the latest stable release is v4.39.28, but that tag was not tested.
The gate fails on any other leaf failure, package/build/race/panic failure,
malformed/incomplete output, or a listed test that passes, skips or disappears.
Parents fail when a child fails, but new failing siblings are not allowed.
Remove entries when upstream fixes them; never widen the list to hide fork regressions.
Raw JSON remains in the Actions log. A ready-to-file upstream report is in PR #26;
neo-dev routes it, rather than patching core here. Related closed upstream
[PR #12154](https://github.com/authelia/authelia/pull/12154) describes the hardcoded
CheckedAt assumption. Run Go units
before Vite overwrites the tracked server test placeholders. The full web suite
includes coverage. Fork Python contracts, `tsc --noEmit`, `pnpm build`, and the Go
binary build also run. The separate image workflow retains real browser smoke.

`setup-go` caches modules/build output keyed by `go.sum`; a pinned cache action
stores pnpm's content-addressed store keyed by OS, pnpm major and the web lockfile.
Installation remains frozen and script-free. The job retains a 25-minute budget
and always writes its result and **Required for merge** scope to the workflow
summary. Neo-dev owns repository required-check settings; a summary does not
configure branch protection. Inherited failures remain visible; only the exact
approved list is tolerated, and any stale entry fails the job.
Live cold/warm CI duration and cache savings: NOT MEASURED.
For local worktrees whose basename is not `authelia`, set
`BUILDKITE_PIPELINE_SLUG` to that basename for the Go command. Upstream's
`TestShouldExecCommandOnAutheliaRootPath` explicitly supports this override;
CI already checks out into `authelia`, so needs no override. Stop the local
runtime probe before Go units: `TestAddressOutputValues` binds port 9091 and
panics after a failed bind when the smoke binary still owns that port.
Rollback: revert the #18 workflow change; no runtime/image configuration changes.
