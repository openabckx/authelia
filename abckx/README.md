# Authelia · versão abckx

Nossa versão do Authelia, **sem alterar o core**:

- `master` acompanha o upstream (`authelia/authelia`), sem commits nossos.
- O branch `abckx` só acrescenta `abckx/` e o workflow `abckx-image`.
- A imagem é a oficial (pinada por digest) + `abckx/assets` via `server.asset_path`.

## Publicar uma versão

Tag `abckx-v<versão do authelia>-<rev>`, ex.: `abckx-v4.39.28-1`.
O workflow gera `ghcr.io/abckxopen/authelia:4.39.28-1` e `:latest`.

## Atualizar o Authelia

Troque `AUTHELIA_VERSION` e o digest no `abckx/Dockerfile` e publique uma tag nova.
