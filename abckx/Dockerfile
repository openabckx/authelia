# Authelia da abckx: a imagem OFICIAL, sem tocar no core, com os nossos assets por cima.
# O core vem pinado por digest; a personalizacao (logo, favicon, textos do portal) mora em abckx/assets
# e entra pelo mecanismo nativo do Authelia (server.asset_path).
ARG AUTHELIA_VERSION=4.39.28
FROM authelia/authelia:${AUTHELIA_VERSION}@sha256:bd97cff4fcbf715b5ff1f9ae286afbe6033afce385302520b0368122d43a6f54

COPY abckx/assets/ /abckx/assets/
ENV AUTHELIA_SERVER_ASSET_PATH=/abckx/assets/

LABEL org.opencontainers.image.source="https://github.com/abckxopen/authelia" \
      org.opencontainers.image.description="Authelia oficial + personalizacao abckx (login e 2FA), sem alterar o core" \
      org.opencontainers.image.licenses="Apache-2.0"
