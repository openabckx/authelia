# Operating our Authelia image (openabckx/authelia)

The holding's standard for running this image in production: what you can customize, every setting, and how to take care
of each part. Proven on dev-04 (2026-11-07/08) before any production use. External setups (e.g. neo-stark's stark-01) are
cited as references, not rules.

Image: `ghcr.io/openabckx/authelia:<upstream version>-<our revision>` (e.g. `4.39.28-5`), built from branch `abckx`.
Base release target = upstream v4.39.28; the fork also carries upstream master commits. Check the selected image revision before upgrading. Everything not listed here behaves exactly like upstream: see https://www.authelia.com.

## 1. What differs from upstream
| area | ours | how to set it |
|---|---|---|
| footer | your exact text with optional HTTPS link, portal + emails | `AUTHELIA_BRANDING_TEXT`, `AUTHELIA_BRANDING_URL` (empty text hides it) |
| logo, favicon | iAvançada official files baked in | override: mount your `logo.png` / `favicon.ico` into `/abckx/assets/` |
| accent color | buttons, links, focus, Settings bar | `AUTHELIA_BRANDING_PRIMARY_COLOR=#RRGGBB` (invalid value = refuses to start) |
| background | image behind the login card | `AUTHELIA_BRANDING_BACKGROUND_IMAGE=true`, `_OPACITY` (0..1), `_BLUR` (0..20) + mount `background.png` |
| emails | branded PT-BR titles, body, details and buttons (code, link, event; html + txt); opt-in SMTP subjects | `ABCKX_EMAIL_LOGO_URL`, `ABCKX_EMAIL_ENV_BANNER`, `ABCKX_EMAIL_SUBJECT_PT_BR=true` |
| runtime | non-root UID/GID 1000, built from source, browser-smoked in CI | volumes must be writable by UID 1000 |

## 2. Minimal deployment

This is a deployment skeleton, not a complete configuration. Use the upstream
[configuration guide](https://www.authelia.com/configuration/prologue/introduction/)
and the repository [configuration template](../config.template.yml). Before starting:

- Create `config/configuration.yml`, with `session.redis.host: redis`, the cookie domain and HTTPS portal URL,
  file authentication at `/users/users_database.yml`, `storage.local.path: /data/db.sqlite3`, and your SMTP server/sender.
- Supply separate high-entropy files `jwt`, `session`, `storage`, `redis`, `smtp` in `./secrets/`; never commit them.
  Keep host modes restrictive and grant only the necessary container UID read access (for example, a specific ACL).
- Create `./users/users_database.yml` and an actual readable `./background.png` before Compose; otherwise bind mounts may become directories.
- Provision the `authelia_data` volume and users directory as writable by UID/GID `1000:1000`; Docker does not repair ownership.
  Provision Redis storage/secrets for the Redis image's runtime UID separately. Do not use `chmod 777`.
- The HTTPS proxy must share the container network and reach `authelia:9091`; this example publishes no host port.
- The GHCR package is public. Release `abckx-v4.39.28-5` publishes `4.39.28-5`; unreleased builds use `abckx-<sha12>`.
  If access becomes private, request access from the org admin or build from source.

```yaml
services:
  authelia:
    image: ghcr.io/openabckx/authelia:4.39.28-5
    restart: unless-stopped
    environment:
      AUTHELIA_IDENTITY_VALIDATION_RESET_PASSWORD_JWT_SECRET_FILE: /secrets/jwt
      AUTHELIA_SESSION_SECRET_FILE: /secrets/session
      AUTHELIA_STORAGE_ENCRYPTION_KEY_FILE: /secrets/storage
      AUTHELIA_SESSION_REDIS_PASSWORD_FILE: /secrets/redis
      AUTHELIA_NOTIFIER_SMTP_PASSWORD_FILE: /secrets/smtp
      AUTHELIA_BRANDING_TEXT: "Powered by Example Company"
      AUTHELIA_BRANDING_URL: https://example.com
      AUTHELIA_BRANDING_PRIMARY_COLOR: "#006D77"
      AUTHELIA_BRANDING_BACKGROUND_IMAGE: "true"
      AUTHELIA_BRANDING_BACKGROUND_OPACITY: "0.25"
      AUTHELIA_BRANDING_BACKGROUND_BLUR: "0"
      ABCKX_EMAIL_LOGO_URL: https://login.example.com/static/media/logo.png
      ABCKX_EMAIL_ENV_BANNER: ""            # e.g. "srv-DEV-04" on dev; empty in prod
    volumes:
      - ./config:/config:ro                 # configuration.yml
      - ./users:/users                      # users_database.yml, WRITABLE (password reset)
      - ./secrets:/secrets:ro               # one file per secret, readable by UID 1000
      - ./background.png:/abckx/assets/background.png:ro
      - authelia_data:/data                 # SQLite storage, owned by UID 1000
    depends_on: [redis]
  redis:
    image: redis:7.4-alpine
    command: ['sh', '-c', 'exec redis-server --appendonly yes --requirepass "$$(cat /secrets/redis)"']
    volumes: ["./secrets/redis:/secrets/redis:ro", "redis_data:/data"]
volumes: { authelia_data: {}, redis_data: {} }
```
See [LICENSE](../LICENSE) and [NOTICE](../NOTICE) (Apache-2.0).

Build from source instead of pulling (from the repository root):

```sh
docker build -f abckx/Dockerfile --build-arg VERSION=4.39.28-local --build-arg REVISION="$(git rev-parse HEAD)" -t authelia:local .
```

Then replace the Compose `image` with `authelia:local`. Put it behind a reverse proxy
(Traefik `forwardAuth` to `/api/authz/forward-auth`).

## 3. Configuration that matters in production
- **Access**: `default_policy: deny`; one rule per protected host, `policy: two_factor`, subject = a group
  (`group:<app>`) or a single user (`user:<login>`) for personal tools.
- **Authenticator name**: `totp.issuer` (and `webauthn.display_name`). Pick stable names. TOTP records keep their stored issuer; changing the configured issuer does not rewrite existing enrollments. WebAuthn credentials are scoped to the relying-party ID, not the display name.
- **Sessions**: Redis, `expiration`, `inactivity`, `remember_me` per company policy; cookie domain = the parent domain.
- **Regulation**: e.g. 5 retries / 2 min → 10 min ban.
- **Users (file backend)**: `path` on the writable mount, `watch: true`, `search.email: true` (emails must be unique), argon2.
- **Real client IP**: the proxy must forward `X-Forwarded-For` and Authelia must see it (Traefik: `forwardedHeaders.trustedIPs`
  for the private ranges the traffic comes from), otherwise emails and logs show the proxy IP.
- **CDN**: if the domain is behind Cloudflare with Web Analytics, send `Cache-Control: no-store, no-transform` on the login host,
  or Cloudflare injects a script the CSP blocks (console error on every page).

## 4. Emails
- SMTP submission (587 STARTTLS) with a password file. By default Authelia checks SMTP at startup and refuses to start on failure; `notifier.disable_startup_check` can disable that check.
- `notifier.smtp.sender: '<Brand> <mailbox@domain>'` and `subject: '[<Brand>] {title}'`. Never leave "[Authelia]".
- Deliverability checklist: SPF, DKIM (every key the server signs with must be published), DMARC; sender display name on the
  same brand as the domain; consistent PT-BR copy; real text, not image-only. A new sender lands in spam at first: test with a
  real inbox and mark "not spam".
- Templates: ours are baked in (`/abckx/templates`), selected by `notifier.template_path` / `AUTHELIA_NOTIFIER_TEMPLATE_PATH`. Titles, event fragments, known detail labels/values and buttons are PT-BR; unknown values and user descriptions are preserved. Set `ABCKX_EMAIL_SUBJECT_PT_BR=true` to translate SMTP `{title}` too, preserving the configured prefix. Unset/false retains upstream subjects; filesystem subjects stay unchanged. Rebuild for the new templates/hook, then restart after changing the opt-in.
  The "set password" email is the same for invite and forgot-password.

## 5. Users
- First user(s): seed the users file once; afterwards Authelia owns the hashes (password reset writes them).
- New user later: add the entry with a random argon2 placeholder hash, wait for the watch reload, then call
  `POST /api/reset-password/identity/start` with the username: the person gets the "set your password" email (invite).
- Apps that manage users: queue the request in the app; a separate bridge writes the file and triggers the reset; on every
  reconcile keep the hash already on disk (only name, email, groups, disabled change). Reference: neo-stark, stark-01.
- Block: `disabled: true` (open sessions last until they expire; flush Redis sessions for an immediate cut).
- Reset someone's 2FA: `authelia storage user totp delete <user>` and `authelia storage user webauthn delete <user> --all`.

## 6. Backup and restore
- Back up the SQLite storage **and** the users file, encrypted, off-site. Stop Authelia and other writers for an offline copy; include any SQLite WAL/journal files. A paused process alone does not checkpoint SQLite. Backup downtime: NOT MEASURED. Preserve the storage encryption key in the approved secret backup; the database alone cannot recover encrypted data.
- Take a backup before every deploy. Upstream upgrades may migrate the storage schema: rolling back the image then needs the
  backup restored.
- Test the restore regularly.

## 7. Upgrades
- The upstream workflow is scheduled daily at 04:23 UTC, plus manual dispatch. It requires `abckx` as default branch and Actions permission to open PRs. It validates a candidate with fork CI and opens a reviewed sync PR; conflicts, workflow changes or failed CI open `upstream-conflict` issues. The image workflow runs a real-browser smoke before publication. Neo-dev reviews and deploys to dev first. Full Go units run with the exact known-upstream-failure ratchet described in [the validation guide](README.md#required-pr-validation-18); integration suites need their separate environment.
- The holding fork-standard requires thin upstream hooks in `abckx/PATCHES.md`. That manifest is not present yet, tracked in [#22](https://github.com/openabckx/authelia/issues/22). Until it lands, inspect the fork diff and [changelog](../CHANGELOG-abckx.md) on conflicts; do not assume the hook inventory is complete.
- Security releases: same path, with priority.

## 8. Proving a deploy
Not curl. Open the login in a headless browser: the username field renders, no console errors, footer/logo/color as configured.
Then the full flow: login + TOTP → protected app → 2FA settings → logout, and one password-reset email to a real inbox.

## 9. Known traps
1. Blank page with HTTP 200: frontend built without `web/.env.production` (fixed in our Dockerfile; CI blocks it).
2. CSP console error on every page: Cloudflare Web Analytics injection (see §3 CDN).
3. Non-root image cannot read secrets: give UID 1000 read access (ACL), do not loosen modes.
4. Read-only users file: "Reset password?" shows but fails.
5. Emails show the proxy IP: forwarded headers not trusted (see §3).
6. Emails in spam: "[Authelia]" subject, mismatched sender name, mixed languages, unpublished DKIM key.

## 10. Production checklist
- [ ] Image tag pinned; backup taken; secrets generated (0600, readable by UID 1000).
- [ ] Access rules: deny by default, two_factor everywhere, right groups/users.
- [ ] Branding variables set; `ABCKX_EMAIL_ENV_BANNER` empty.
- [ ] SMTP starts OK; reset email reaches a real inbox (not spam); sender and subject branded.
- [ ] Real client IP visible in Authelia logs.
- [ ] Browser smoke + full user flow green.
- [ ] Backup of storage + users file scheduled; restore tested.
- [ ] Upstream watch active.
