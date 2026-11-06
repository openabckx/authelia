# syntax=docker/dockerfile:1
# Adapted from upstream Dockerfile.dev and cmd/authelia-scripts/cmd/build.go.
# Build from the repository root: docker build -f abckx/Dockerfile .
FROM node:26-alpine@sha256:c6ad9e9c1d80f6eb607c26b4b0a132ff7a2344fad1c78ea3baa2a7d4c8de6d94 AS frontend
WORKDIR /src/web
RUN npm install --global pnpm@12.18.0
COPY web/ ./
RUN pnpm install --frozen-lockfile --ignore-scripts && pnpm build

FROM golang:1.27.3-bookworm@sha256:d9b6a1beb9474adc2a1ce842573639b44b2a0dd49b6669f51d3821baf9ec37c9 AS backend
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
COPY --from=frontend /src/internal/server/public_html/ internal/server/public_html/
# Vite copies public/api symlinks; embed real API files as upstream does.
RUN rm -rf internal/server/public_html/api && cp -R api internal/server/public_html/api
ARG VERSION=4.39.28-abckx-dev
ARG REVISION=unknown
RUN CGO_ENABLED=1 CGO_CPPFLAGS="-D_FORTIFY_SOURCE=2 -fstack-protector-strong" \
    CGO_LDFLAGS="-Wl,-z,relro,-z,now" go build -trimpath -buildmode=pie \
    -ldflags "-linkmode=external -s -w -X github.com/authelia/authelia/v4/internal/utils.BuildTag=${VERSION} -X 'github.com/authelia/authelia/v4/internal/utils.BuildState=tagged clean' -X github.com/authelia/authelia/v4/internal/utils.BuildCommit=${REVISION}" \
    -o /app/authelia ./cmd/authelia

FROM authelia/base:latest@sha256:375dd7dc21deef3f903da085f1ee22894c88f41fe5ca6b7eebdaaf6445d562ef
WORKDIR /app
ENV PATH="/app:${PATH}" \
    X_AUTHELIA_CONFIG="/config/configuration.yml" \
    AUTHELIA_SERVER_ASSET_PATH="/abckx/assets/"
COPY --from=backend /app/authelia ./
COPY LICENSE entrypoint.sh healthcheck.sh ./
COPY --chmod=666 .healthcheck.env ./
COPY abckx/assets/ /abckx/assets/
RUN mkdir -p /config && chown 1000:1000 /config
USER 1000:1000
EXPOSE 9091
ENTRYPOINT ["/app/entrypoint.sh"]
HEALTHCHECK --interval=30s --timeout=3s --start-period=1m CMD /app/healthcheck.sh
LABEL org.opencontainers.image.licenses="Apache-2.0"
