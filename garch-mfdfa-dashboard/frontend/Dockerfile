# --- Build stage: compile the Svelte app to static files ---
FROM node:18-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ .
# Raise V8's heap limit: on low-RAM hosts Node auto-caps old-space ~460 MB,
# which OOMs while Rollup bundles the large Plotly graph. Needs backing memory
# (add swap on free-tier EC2).
ENV NODE_OPTIONS=--max-old-space-size=2048
RUN npm run build

# --- Serve stage: static files behind nginx, which also proxies /api ---
FROM nginx:alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
