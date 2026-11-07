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

The image ships an original purple geometric `background.png` (1280×720) in
`/abckx/assets/`. It is opt-in; unset/false keeps the upstream plain background.
The official company logo remains on the login card.

```yaml
environment:
  AUTHELIA_BRANDING_BACKGROUND_IMAGE: 'true'
  AUTHELIA_BRANDING_BACKGROUND_OPACITY: '0.25'
  AUTHELIA_BRANDING_BACKGROUND_BLUR: '0'
volumes:
  - ./company-background.png:/abckx/assets/background.png:ro
```

Omit the volume to use the baked-in wallpaper. Use a readable PNG file, never a
remote URL. The mount replaces one file, so the official logo/favicon remain.
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

The smoke runs default, mounted override, missing and disabled cases. Chromium
checks loaded dimensions, computed image/blur/opacity and opaque cards in all
four themes. It requires AA card text contrast in light/dark/oled; inherited grey
measures 4.39:1 and is not repaired here. Authentication, Settings and console
checks still cover every theme. Custom accent text needs the operator contrast
check described above.
Rollback: set `AUTHELIA_BRANDING_BACKGROUND_IMAGE: 'false'` and restart, or restore
the previous image digest. Rollback duration and production rendering: NOT MEASURED.

## Notification branding (#14)

The image ships `abckx/templates/` through `AUTHELIA_NOTIFIER_TEMPLATE_PATH`.
These six operator-owned overrides retain upstream table layouts, inline styles,
Outlook markup and security fields. Keep them current when upstream changes
notification data. Static copy is PT-BR; runtime titles, subjects, event fragments,
detail keys and button labels keep the language supplied by core.

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
repo root. Set `ABCKX_EMAIL_PREVIEW_DIR` to an absolute output directory to render
three safe sample HTML previews through the real provider. The committed
`previews/` files use example.com links and a sample code, never real credentials.
Mailbox-client rendering remains tester-owned after image deployment.

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
