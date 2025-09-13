# Multi-stage Dockerfile for M32 Business Intelligence Frontend
# Supports both development and production environments

# Base stage with Node.js
FROM node:18-alpine as base

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies)
RUN npm ci

# Copy source code
COPY . .

# Development stage
FROM base as development

# Expose development port
EXPOSE 3000

# Set environment to development
ENV NODE_ENV=development

# Start development server with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

# Build stage (for production)
FROM base as builder

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine as production

# Install curl for health checks
RUN apk add --no-cache curl

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create non-root user
RUN addgroup -g 1001 -S m32user && \
    adduser -S m32user -u 1001

# Set proper permissions
RUN chown -R m32user:m32user /usr/share/nginx/html && \
    chown -R m32user:m32user /var/cache/nginx && \
    chown -R m32user:m32user /var/log/nginx && \
    chown -R m32user:m32user /etc/nginx/conf.d

# Switch to non-root user
USER m32user

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
