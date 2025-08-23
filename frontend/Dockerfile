# Multi-stage Dockerfile for Financial Planning Frontend
# Built with security, performance, and production best practices

# ============================================================================
# Dependencies Stage - Install and cache dependencies
# ============================================================================
FROM node:18-alpine as dependencies

# Set working directory
WORKDIR /app

# Install security updates and necessary packages
RUN apk update && apk add --no-cache \
    dumb-init \
    && rm -rf /var/cache/apk/*

# Copy package files
COPY package*.json ./

# Install dependencies with npm ci for reproducible builds
RUN npm ci --only=production --no-audit --no-fund \
    && npm cache clean --force

# ============================================================================
# Build Stage - Build the application
# ============================================================================
FROM node:18-alpine as builder

WORKDIR /app

# Install build dependencies
RUN apk update && apk add --no-cache \
    git \
    python3 \
    make \
    g++ \
    && rm -rf /var/cache/apk/*

# Copy package files and install all dependencies (including devDependencies)
COPY package*.json ./
RUN npm ci --no-audit --no-fund

# Copy source code
COPY . .

# Build the application
ENV NODE_ENV=production
ENV GENERATE_SOURCEMAP=false
RUN npm run build

# ============================================================================
# Production Stage - Serve the application with nginx
# ============================================================================
FROM nginx:1.25-alpine as production

# Install security updates
RUN apk update && apk upgrade && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Copy built application from builder stage
COPY --from=builder --chown=nextjs:nodejs /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY --chown=root:root nginx.conf /etc/nginx/nginx.conf

# Create necessary directories and set permissions
RUN mkdir -p /var/cache/nginx/client_temp \
    /var/cache/nginx/proxy_temp \
    /var/cache/nginx/fastcgi_temp \
    /var/cache/nginx/uwsgi_temp \
    /var/cache/nginx/scgi_temp \
    && chown -R nextjs:nodejs /var/cache/nginx \
    && chown -R nextjs:nodejs /var/log/nginx \
    && chown -R nextjs:nodejs /etc/nginx/conf.d \
    && touch /var/run/nginx.pid \
    && chown -R nextjs:nodejs /var/run/nginx.pid

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Security labels
LABEL security.non-root=true \
      security.no-new-privileges=true

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# ============================================================================
# Development Stage - For local development with hot reload
# ============================================================================
FROM node:18-alpine as development

WORKDIR /app

# Install development dependencies
RUN apk update && apk add --no-cache \
    git \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 -G nodejs

# Copy package files
COPY --chown=nextjs:nodejs package*.json ./

# Install all dependencies
RUN npm install --no-audit --no-fund

# Copy source code
COPY --chown=nextjs:nodejs . .

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Development command with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]