# Fork patch inventory

Rules: [fork-standard](https://github.com/inteligenciaavancada/inventario/blob/main/tech/fork-standard/SKILL.md).
Scope: every changed path outside `abckx/` in `git diff --name-only --no-renames origin/master...HEAD`.
This includes fork-only additions outside our directory. No glob or directory row grants coverage.
For renames, retain the removed path and add the destination. Retain deleted paths while the diff contains them.

Run `python3 abckx/check_patch_manifest.py --base origin/master` from a full-history checkout.
CI checks the candidate HEAD (including the PR merge result), not the old `abckx` tip.
The three-dot comparison inventories fork changes since the common ancestor, as required by #22.
Mirror-only updates are not fork patches; this check does not prove the fork has incorporated the latest mirror release.
Missing history, missing manifest and unlisted paths fail closed. Coverage is not approval of a patch's design.
`abckx/` owns image/assets, notification overrides, scripts and their tests; those files do not need rows here.
No LICENSE or NOTICE changes are allowed.

## Exact-path inventory

Issue/PR numbers refer to [openabckx/authelia](https://github.com/openabckx/authelia).
Tests name executable suites or manual documentation checks. N/A means no runtime hook, not untested product code.

| File | Hook / change | Why | Issue/PR | Covering test |
|---|---|---|---|---|
| `.github/workflows/abckx-ci.yml` | Fork-only full Go/web validation and manifest gate | Validate fork PRs without upstream services | #3/#5, #18/#26, #22 | `abckx/test_ci.py`, `abckx/test_patch_manifest.py` |
| `.github/workflows/abckx-image.yml` | Fork-only source image and browser smoke workflow | Publish traceable branded images | #3/#5, #7/#8 | `abckx/test_ci.py`, `abckx/image-smoke.py`, `abckx/browser-smoke.mjs` |
| `.github/workflows/abckx-upstream.yml` | Fork-only reviewed release-sync workflow | Keep mirror current and surface conflicts | #17/#23 | `abckx/test_upstream_sync.py` |
| `.github/workflows/codeql-analysis.yml` | Repository guard on analyze job | Leave upstream-only automation inactive here | #3/#5 | `abckx/test_ci.py` |
| `.github/workflows/contributors.yml` | Repository guard on card job | Avoid fork-side upstream card writes | #3/#5 | `abckx/test_ci.py` |
| `.github/workflows/pr-commentary.yml` | Repository guard on comment job | Avoid upstream-only fork commentary | #3/#5 | `abckx/test_ci.py` |
| `.github/workflows/pr-labels.yml` | Repository guard on label job | Keep upstream labels out of fork routine | #3/#5 | `abckx/test_ci.py` |
| `.github/workflows/scorecard.yml` | Repository guard on analysis job | Leave upstream-only scorecard inactive | #3/#5 | `abckx/test_ci.py` |
| `AGENTS.md` | Fork-only agent entry point | Route rules and identify author/reviewer | #22 | Manual English, links and identities review; manifest gate |
| `CHANGELOG-abckx.md` | Fork-only operator change history | Explain image/config impact | #1/#4 through #22 | Manual issue/impact/rollback review; manifest gate |
| `README.md` | Fork entry point prepended; upstream README preserved | Route image users to operations | #25/#28, #22 | Manual links/source review; upstream suffix comparison |
| `examples/templates/notifications/no-preview/Event.html` | Generated conditional footer markup | Keep example consistent with source component | #1/#4 | `internal/templates/branding_test.go` (embedded counterpart); manual example parity |
| `examples/templates/notifications/no-preview/IdentityVerificationJWT.html` | Generated conditional footer markup | Keep example consistent with source component | #1/#4 | `internal/templates/branding_test.go` (embedded counterpart); manual example parity |
| `examples/templates/notifications/no-preview/IdentityVerificationOTC.html` | Generated conditional footer markup | Keep example consistent with source component | #1/#4 | `internal/templates/branding_test.go` (embedded counterpart); manual example parity |
| `internal/configuration/branding_background_test.go` | Fork-only env/config regression tests | Verify background settings decode | #16/#21 | `go test ./internal/configuration` |
| `internal/configuration/branding_test.go` | Fork-only env/config regression tests | Verify footer values and unset/empty distinction | #1/#4 | `go test ./internal/configuration` |
| `internal/configuration/schema/branding.go` | Fork-only branding type, defaults and accent CSS | Isolate branding state and color computation | #1/#4, #15/#20 | `internal/configuration/schema/branding_color_test.go`, `internal/server/branding_test.go` |
| `internal/configuration/schema/branding_background.go` | Fork-only background validation/CSS | Isolate opt-in local wallpaper behavior | #16/#21 | `internal/configuration/schema/branding_background_test.go` |
| `internal/configuration/schema/branding_background_test.go` | Fork-only schema regression tests | Cover bounds and CSS output | #16/#21 | `go test ./internal/configuration/schema` |
| `internal/configuration/schema/branding_color_test.go` | Fork-only accent regression tests | Cover hex validation and foreground contrast | #15/#20 | `go test ./internal/configuration/schema` |
| `internal/configuration/schema/configuration.go` | Branding field and gofmt alignment | Decode fork config in upstream root schema | #1/#4 | `internal/configuration/branding_test.go`, `internal/configuration/branding_background_test.go` |
| `internal/configuration/schema/keys.go` | Six branding key entries | Permit runtime env/YAML options | #1/#4, #15/#20, #16/#21 | `internal/configuration/branding_test.go`, `internal/configuration/branding_background_test.go` |
| `internal/configuration/validator/branding_color_test.go` | Fork-only validation tests | Reject invalid accent values | #15/#20 | `go test ./internal/configuration/validator` |
| `internal/configuration/validator/branding_test.go` | Fork-only validation tests | Reject unsafe footer URLs | #1/#4 | `go test ./internal/configuration/validator` |
| `internal/configuration/validator/configuration.go` | Inline branding validation, NOT thin | Reject unsafe URL/color/background options | #1/#4, #15/#20, #16/#21 | `internal/configuration/validator/branding_test.go`, `internal/configuration/validator/branding_color_test.go`; schema background tests |
| `internal/middlewares/util.go` | Pass Branding into template config | Wire runtime footer to notifications | #1/#4 | `internal/templates/branding_test.go`, `abckx/notifications_test.go` |
| `internal/server/branding_background_test.go` | Fork-only runtime background tests | Verify local file enable/disable and nonce | #16/#21 | `go test ./internal/server` |
| `internal/server/branding_color_test.go` | Fork-only runtime accent tests | Verify nonce CSS and common data | #15/#20 | `go test ./internal/server` |
| `internal/server/branding_test.go` | Fork-only footer runtime tests | Verify escaping, hidden and default states | #1/#4 | `go test ./internal/server` |
| `internal/server/handlers.go` | Two AssetOverride routes for background.png | Serve local wallpaper without remote CSP changes | #16/#21 | `abckx/image-smoke.py`, `abckx/browser-smoke.mjs` |
| `internal/server/template.go` | Branding data wiring plus inline file/CSS logic, NOT thin | Inject safe runtime footer/accent/background | #1/#4, #15/#20, #16/#21 | `internal/server/branding_test.go`, `internal/server/branding_color_test.go`, `internal/server/branding_background_test.go` |
| `internal/templates/branding_test.go` | Fork-only notification footer regressions | Cover default/custom/hidden and HTML escaping | #1/#4 | `go test ./internal/templates` |
| `internal/templates/embed/notification/Event.html` | Generated conditional footer markup | Runtime notification footer | #1/#4 | `internal/templates/branding_test.go`, `abckx/notifications_test.go` |
| `internal/templates/embed/notification/Event.txt` | Conditional branding footer | Match text mail with HTML footer | #1/#4 | `internal/templates/branding_test.go`, `abckx/notifications_test.go` |
| `internal/templates/embed/notification/IdentityVerificationJWT.html` | Generated conditional footer markup | Runtime verification footer | #1/#4 | `internal/templates/branding_test.go`, `abckx/notifications_test.go` |
| `internal/templates/embed/notification/IdentityVerificationJWT.txt` | Conditional branding footer | Match text verification with HTML footer | #1/#4 | `internal/templates/branding_test.go`, `abckx/notifications_test.go` |
| `internal/templates/embed/notification/IdentityVerificationOTC.html` | Generated conditional footer markup | Runtime verification footer | #1/#4 | `internal/templates/branding_test.go`, `abckx/notifications_test.go` |
| `internal/templates/embed/notification/IdentityVerificationOTC.txt` | Conditional branding footer | Match text verification with HTML footer | #1/#4 | `internal/templates/branding_test.go`, `abckx/notifications_test.go` |
| `internal/templates/funcs.go` | Default branding template function | Parse notifications with upstream defaults | #1/#4 | `internal/templates/branding_test.go` |
| `internal/templates/provider.go` | Inline branding function binding loop, NOT thin | Bind config to three parsed notification pairs | #1/#4 | `internal/templates/branding_test.go`, `abckx/notifications_test.go` |
| `internal/templates/src/components/Brand.tsx` | Inline conditional Go-template footer markup, NOT thin | Generate default/custom/hidden email footers | #1/#4 | `internal/templates/branding_test.go` (generated output); manual source/output parity |
| `internal/templates/types.go` | Branding field in notification Config | Pass config without changing notifier behavior | #1/#4 | `internal/templates/branding_test.go` |
| `web/index.html` | BrandingStyle call and three escaped body attributes | Pass runtime presentation to portal | #1/#4, #15/#20, #16/#21 | `internal/server/branding_test.go`, `internal/server/branding_color_test.go`, `abckx/browser-smoke.mjs` |
| `web/src/components/Brand.test.tsx` | Fork footer cases added to existing test | Guard hidden/custom/plain/linked footer and privacy link | #1/#4 | `pnpm --dir web test` |
| `web/src/components/Brand.tsx` | Inline component rewrite, NOT thin | Runtime footer, privacy preservation, safe links | #1/#4 | `web/src/components/Brand.test.tsx`, `abckx/browser-smoke.mjs` |
| `internal/notification/smtp_notifier.go` | One subject translation call | Opt-in PT-BR SMTP title substitution | #27 | `internal/notification/subject_abckx_test.go` |
| `internal/notification/subject_abckx.go` | Fork-only optional title map | Isolate localization from core event logic | #27 | `internal/notification/subject_abckx_test.go` |
| `internal/notification/subject_abckx_test.go` | Fork-only MIME regression tests | Verify opt-in/default subjects and multipart UTF-8/CRLF | #27 | `go test ./internal/notification` |

## Existing non-thin patches: follow-up scope

Do not refactor these in #22 (docs/CI only). Neo-dev owns follow-up scheduling:

- Extract branding validation from `internal/configuration/validator/configuration.go` into a fork-owned helper with one upstream call.
- Extract file-existence checks and BrandingStyle from `internal/server/template.go` into a fork-owned file; retain only fields and thin calls.
- Extract notification function binding from `internal/templates/provider.go` into a fork-owned helper with one upstream call.
- Extract conditional footer rendering from `web/src/components/Brand.tsx` and `internal/templates/src/components/Brand.tsx` into fork-owned components.
- Generated HTML examples and embedded templates contain multi-line/serialized footer replacements, not one-call source hooks. Keep regeneration tied to the source footer extraction.
- `internal/configuration/schema/configuration.go` has gofmt alignment changes caused by its field addition; avoid further unrelated reformatting.

Fork-only workflows/docs/tests are additions, not upstream logic rewrites. The README prefix is documentation, not a runtime hook.
The manifest does not move PT-BR mail copy into core: the six localized overrides stay under `abckx/templates/` (#14/#19).
