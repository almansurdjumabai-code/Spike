# SpikeClip frontend, web build: a static site served by nginx.
#
#   docker build -t spikeclip-frontend \
#     --build-arg VITE_API_BASE=https://api.example.com frontend/
#
# The backend address is baked in at build time (it is a static site), so
# build once per environment. Vercel, Netlify or Cloudflare Pages work as
# well and need no container: build command `npm run build:web`, output
# directory `dist-web`.

FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
# Electron's own binary is not needed for the web build.
ENV ELECTRON_SKIP_BINARY_DOWNLOAD=1
RUN npm ci --no-audit --no-fund
COPY . .
ARG VITE_API_BASE
ENV VITE_API_BASE=${VITE_API_BASE}
RUN npm run build:web

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist-web /usr/share/nginx/html
EXPOSE 8080
