# abckx changelog

## [nao lancado]

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
