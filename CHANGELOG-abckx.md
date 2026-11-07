# abckx changelog

## [unreleased]

### Local portal background (#16)

- Rebuild to receive the bundled original purple PNG wallpaper. Enable with
  `AUTHELIA_BRANDING_BACKGROUND_IMAGE=true`; unset/false preserves upstream.
- Mount a PNG over `/abckx/assets/background.png` to use company artwork.
  Missing files keep the plain background. No remote URL or CSP relaxation.
- `AUTHELIA_BRANDING_BACKGROUND_OPACITY` (0..1, default 0.25) and
  `AUTHELIA_BRANDING_BACKGROUND_BLUR` (0..20 px, default 0) are runtime settings.
  Invalid values refuse startup. Login-stage cards keep an opaque theme surface.
- Image smoke exercises default/override/missing/disabled backgrounds and all
  themes. Rollback: disable the flag and restart or restore the previous digest.
  Production rendering and rollback duration: NOT MEASURED.

### Runtime portal accent (#15)

- Set `AUTHELIA_BRANDING_PRIMARY_COLOR` / `branding.primary_color` to a quoted
  `#RRGGBB` value. Invalid values refuse startup; empty/unset keeps upstream themes.
- One nonce-authorized runtime style sets primary, focus ring and automatic AA
  foreground for buttons/links/Settings in light/dark/grey/oled. No core behavior
  or dependencies change. Operators still check accent-text/background contrast.
- Rebuild the image once to install the feature; later color changes need only a
  restart. Rollback: unset the variable/YAML value and restart (NOT MEASURED).
- Image Playwright smoke verifies computed colors and real Settings login at
  390×844 with unchanged CSP and a clean browser console.

### Branded security notifications (#14)

- Ship six PT-BR notification overrides with the upstream table/Outlook layout,
  security warnings, revocation links and runtime footer controls. No core change.
- The image defaults `AUTHELIA_NOTIFIER_TEMPLATE_PATH` to `/abckx/templates/`.
  Rebuild the image. Operators can override that path for their own templates.
- Set `ABCKX_EMAIL_LOGO_URL` to an absolute HTTPS logo URL. Unset/empty shows a
  text header only. Set `ABCKX_EMAIL_ENV_BANNER` for a visible environment band
  and first plain-text line; unset/empty omits it. Neither has a hardcoded host.
- Runtime titles/subjects, event fragments and detail keys remain in the core's
  language. Static prose is Brazilian Portuguese. Sent mail cannot be recalled.
- Rollback: restore the previous image digest, or use an upstream/custom template
  directory. Mail-client compatibility and rollback duration: NOT MEASURED.

### Official portal logo and favicon (#6)

- Ship the official iAvançada PNG and multi-resolution favicon through the
  existing `abckx/assets/` overlay. Rebuild the image to receive these defaults;
  operator-provided `AUTHELIA_SERVER_ASSET_PATH` directories still take precedence.
- Preserve upstream portal themes and all core/authentication behavior. Custom
  colors are excluded by the scope decision and tracked upstream in #11862/#8839.
- Pin the official source digests in offline regression tests and document
  source provenance and rollback in `abckx/assets/README.md`.

## [nao lancado]

### Image frontend regression (#7)

- Include only the public `web/.env.production` template after the environment
  exclusions. Keep local and deployment `.env` files outside the build context.
- Reject generated portal output containing `%VITE_BASEPATH%` during image build.
- Run pinned Playwright/Chromium against the actual image before publication.
  Require visible username/password fields, no browser errors or Router basename
  warnings, and no unresolved basename placeholder in served bundles.
- Operators must rebuild the image; no runtime configuration change is required.
  Image publication remains conditional on the complete smoke passing.

### Fork CI and source-built image (#3)

- Build the portal and Go binary from the fork source with upstream build stages
  and hardening flags. Keep the pinned upstream runtime base and asset overlay.
- Run as UID/GID 1000 by default. Bind-mounted storage must be writable by that
  identity; startup does not change host ownership.
- Derive the GHCR owner from the repository owner. Pin workflow actions by SHA.
  Build and smoke-test PR images without publication. Publish the tested image
  only for `abckx` pushes and `abckx-v*` tags, with the build version in the binary.
- Add fork PR typecheck, complete portal tests, Go branding-package tests and
  source builds. Add build-contract regression tests and a real-runtime HTML
  smoke with temporary local configuration.
- Guard upstream-only CodeQL, contributors, commentary, labels and scorecard
  jobs. Keep both SLSA files unchanged per the PO scope decision. No core changes.
- Tag, release and shared-dev validation remain resident-owned. Image smoke is
  configured in Actions because the local workstation has no Docker daemon.


### Runtime footer branding (#1)

- Add `branding.text` / `AUTHELIA_BRANDING_TEXT` and `branding.url` /
  `AUTHELIA_BRANDING_URL` to the normal runtime configuration pipeline.
- Unset text preserves the upstream footer and its translated portal wording.
  Explicitly empty text hides the branding. Custom nonempty text without a URL
  is plain text. A URL must be absolute HTTPS, with a hostname and no credentials;
  invalid configuration prevents startup. Set text when overriding the URL.
- Portal layouts share `Brand`; server-rendered HTML carries escaped configuration
  attributes. All three built-in notification types support custom branding in
  both HTML and plain text. Custom notification templates remain operator-owned;
  they can access the `branding` template function.
- Privacy policy links remain visible when branding is hidden. Product names in
  page titles, manifest metadata and privacy consent wording are not footer
  branding and are unchanged. `LICENSE` and `NOTICE` are unchanged.

Example Compose environment (requires a binary/image built from this branch;
changing these values afterwards needs only a restart, not a frontend rebuild):

```yaml
environment:
  AUTHELIA_BRANDING_TEXT: 'Desenvolvido por abckx'
  AUTHELIA_BRANDING_URL: 'https://abckx.com.br'
```

To hide the footer, set `AUTHELIA_BRANDING_TEXT: ''`. To restore upstream
behavior, remove both variables and any `branding` YAML overrides, then restart.
Already delivered notification emails cannot be changed by a rollback.

Validation: targeted config/env, URL validation, server escaping and notification
tests pass; portal Brand tests pass (9/9). Full web units pass on baseline
(1588 tests) and feature (1593 tests). All 36 canonical Go unit packages complete
on both revisions with identical failures in `TestNewOAuth2DeviceCodeSessionFromRequest`
and `TestWebAuthnCredential`, pre-existing and unrelated; no new failure appears.
Builds, typecheck and local HTML/notification smoke pass. Docker/browser integration
suites and production deployment are not part of this local validation.
