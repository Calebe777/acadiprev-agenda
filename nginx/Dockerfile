# Estágio 1: Build do Frontend React (Vite)
FROM node:20-alpine as build-stage
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Estágio 2: Nginx servindo o Frontend e fazendo proxy para a API
FROM nginx:alpine
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/nginx.conf
