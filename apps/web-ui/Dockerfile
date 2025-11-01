# Hotpass Web UI - Docker Image
# Multi-stage build for production-ready React app

FROM node:20-alpine AS builder

ARG PREFECT_API_URL=http://localhost:4200/api
ARG OPENLINEAGE_URL=http://localhost:5000/api/v1

ENV PREFECT_API_URL=${PREFECT_API_URL}
ENV OPENLINEAGE_URL=${OPENLINEAGE_URL}
ENV VITE_PREFECT_API_URL=${PREFECT_API_URL}
ENV VITE_MARQUEZ_API_URL=${OPENLINEAGE_URL}

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

COPY ../../deploy/docker/bin/health-banner.sh /docker-entrypoint.d/10-health-banner.sh

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
