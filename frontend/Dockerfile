# PZIO frontend image (SAD §2.2 / §7.1.4 — React SPA served as static assets).
# Multistage: Node compiles the bundle, nginx serves it.

FROM node:24-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
# VITE_* are inlined into the bundle at build time. Leaving these empty
# (the default) builds an image with OAuth login disabled — `OAuthButtons`
# hides each provider whose client ID is empty.
ARG VITE_GOOGLE_CLIENT_ID=
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
ARG VITE_GITHUB_CLIENT_ID=
ENV VITE_GITHUB_CLIENT_ID=$VITE_GITHUB_CLIENT_ID
RUN npm run build


FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
