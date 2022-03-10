FROM nginx:1.21-alpine AS base

COPY ./client/dist/. /data

FROM base AS staging
COPY ./deploy/local/nginx.conf /etc/nginx/nginx.conf
