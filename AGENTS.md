# AGENTS.md — openabckx/authelia

Leia isto antes de mexer aqui. Curto de propósito: as regras completas moram nas skills da holding
(`inteligenciaavancada/inventario`).

## O que é este repo
Fork **de personalização** do [authelia/authelia](https://github.com/authelia/authelia) (SSO + 2FA).
Usamos a mesma base do upstream, com a nossa marca e o nosso tema, como imagem pública usada nos servidores da holding.

| branch | o que é | quem mexe |
|---|---|---|
| `master` | espelho do upstream | ninguém (só sincroniza com o upstream) |
| `abckx` | **nossa versão**: base de todo PR | coder via PR |

## Regra do fork (Founder, 06/11/2026)
1. **Aqui só entra personalização:** marca, tema, assets, textos e opções configuráveis por env. Diff mínimo e isolado, pra rebase no upstream continuar barato.
2. **Antes de codar, procure no upstream** (issues, PRs, discussions, releases). Se já existe pronto ou em andamento, use ou acompanhe; não duplique. Cite o que achou na GMUD.
3. **Core ou afim** (bug, segurança, feature útil a todos) **não entra no fork:** abre issue no upstream. Se for **crítico**, abre PR direto no upstream.
4. Manter `LICENSE` e `NOTICE` (Apache-2.0) intactos.

## Como o código funciona (o que importa pra personalizar)
- **Back (Go):** `cmd/authelia` (binário), `internal/` (servidor, config, templates). As opções que o front recebe saem do servidor injetadas no `index.html` (`internal/server/template.go`, ex.: `PrivacyPolicyURL`). Config nova = chave no schema de config + env `AUTHELIA_*` correspondente.
- **Front (React + Vite, pnpm):** `web/src`. Marca do rodapé em `web/src/components/Brand.tsx`. Telas em `web/src/views` (login, 2º fator, reset, consentimento).
- **E-mails/notificações:** `internal/templates/embed/notification/*.{html,txt}` e `internal/templates/src`.
- **Nossa imagem:** `abckx/Dockerfile` + `abckx/assets/` (sobrepostos via `server.asset_path`) e o workflow `.github/workflows/abckx-image.yml`. Tag `abckx-v<versão-upstream>-<rev>` → `ghcr.io/openabckx/authelia:<versão>-<rev>`.

## Validar localmente
```sh
cd web && pnpm install && pnpm build && cd ..
go build -o /tmp/authelia ./cmd/authelia
go test ./internal/...            # o que você mexeu
cd web && pnpm test               # idem no front
/tmp/authelia --config <config-de-teste>   # e prove com curl o HTML/JSON das telas afetadas
```

## Fluxo e papéis
issue com label `hermes` → coder (App `neo-dev-iavancada`, commits com `Coder: hermes-coder/authelia`) → PR contra `abckx`
com GMUD e evidências → revisão e merge pelo `neo-revisor-iavancada` (autor ≠ aprovador) → tag → imagem.
Labels: `hermes` (pronta), `em-andamento`, `em-revisao`, `bloqueada`.

## Skills (vestir antes de codar)
- `ia-standard` (entrada), `regras-da-casa`, `communication`, `esteira`
- `dev-standard` (como se escreve código e PR), `autor-e-aprovador` (identidades), `insecure-defaults` (nada inseguro por padrão)
- `investigate` / `review` / `qa` / `careful` (gstack) conforme a tarefa
