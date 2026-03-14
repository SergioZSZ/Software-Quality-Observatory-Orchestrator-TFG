FROM alpine:3.22 AS alpine
FROM n8nio/n8n:latest

USER root

# Copy apk binary + required libraries into the n8n image
COPY --from=alpine /sbin/apk /sbin/apk
COPY --from=alpine /lib/ld-musl-*.so.1 /lib/
COPY --from=alpine /usr/lib/libapk.so* /usr/lib/

# instalar docker CLI para poder hacer docker run desde n8n
RUN apk add --no-cache docker-cli

# instalar python si quieres ejecutar scripts desde n8n
RUN apk add --no-cache python3 py3-pip py3-virtualenv

# añadir usuario node al grupo docker
RUN addgroup -g 116 docker && addgroup node docker

USER node

