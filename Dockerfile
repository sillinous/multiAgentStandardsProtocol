# Multi-stage build for optimized production image

# Build stage
FROM rust:1.75 as builder

# Create app directory
WORKDIR /app

# Copy manifests
COPY Cargo.toml Cargo.lock ./
COPY crates ./crates

# Build for release
RUN cargo build --release -p agentic_api

# Runtime stage
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 agentic

# Create data directory
RUN mkdir -p /app/data && chown -R agentic:agentic /app

# Set working directory
WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/agentic_api /app/agentic_api

# Copy static files if any
# COPY static /app/static

# Change ownership
RUN chown -R agentic:agentic /app

# Switch to non-root user
USER agentic

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Set environment
ENV RUST_LOG=info
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8080

# Run the application
CMD ["/app/agentic_api"]
