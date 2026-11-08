# AGENTS.md: openabckx/authelia

Customization-only fork of [Authelia](https://github.com/authelia/authelia) for our brand, theme, assets and runtime options.

| Branch | Purpose | Writer |
|---|---|---|
| `master` | Pure upstream mirror | Upstream sync only |
| `abckx` | Our default branch and PR target | Coder via reviewed PR |

## Read before work

- Load `ia-standard`, `dev-standard` and `neo-dev-coder` for the execution process.
- Load **[fork-standard](https://github.com/inteligenciaavancada/inventario/blob/main/tech/fork-standard/SKILL.md)** for fork rules. They live there, not here.
- Read [PATCHES.md](abckx/PATCHES.md) before changing an upstream path. Update its row in the same PR.
- Use [the operations manual](abckx/OPERATIONS.md) for deployment and [build/validation instructions](abckx/README.md) for local checks.
- Record image-operator impact in [CHANGELOG-abckx.md](CHANGELOG-abckx.md).

## Roles and work isolation

Coder: App `neo-dev-coder` (id `5124602`; legacy login `neo-dev-iavancada[bot]`).
Reviewer/merger: `neo-dev-review`. The writer never approves or merges.

Use one worktree and branch `coder/<issue>-<slug>` per issue, from `origin/abckx`.
Never write code in the shared clone. Update branches with merge, never rebase or force-push.
Commit trailer: `Coder: hermes-coder/authelia`.
Neo-dev owns releases and deployments; the tester profile verifies the dev user flow.

## Validation

Run `python3 abckx/check_patch_manifest.py --base origin/master` with full mirror history.
Run `python3 -m unittest discover -s abckx -v` for fork contracts.
Follow the build instructions for full Go/web tests, typecheck, source builds and runtime evidence.
Write internal documentation, comments, commits and PRs in English.
