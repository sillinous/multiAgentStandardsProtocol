# 🚀 Agentic Forge - Complete Deployment Guide

This guide walks you through deploying the Agentic Forge platform in various environments, from local development to production cloud deployment.

---

## 📋 Table of Contents

- [Quick Start (Docker)](#quick-start-docker)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Cloud Platforms](#cloud-platforms)
  - [AWS](#deploying-on-aws)
  - [Google Cloud Platform](#deploying-on-gcp)
  - [Digital Ocean](#deploying-on-digital-ocean)
  - [Azure](#deploying-on-azure)
- [Configuration](#configuration)
- [Monitoring & Logs](#monitoring--logs)
- [Troubleshooting](#troubleshooting)

---

## 🐳 Quick Start (Docker)

The **fastest** way to get the platform running!

### Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- 4GB RAM minimum
- Anthropic API key (get from https://console.anthropic.com/)

### 1. Clone Repository

```bash
git clone https://github.com/yourorg/multiAgentStandardsProtocol.git
cd multiAgentStandardsProtocol
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env  # or vim, code, etc.
```

**Minimum required**:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Start Platform

```bash
# Start with default configuration
docker-compose -f docker-compose.python.yml up -d

# Or with monitoring enabled
docker-compose -f docker-compose.python.yml --profile monitoring up -d
```

### 4. Verify Health

```bash
curl http://localhost:8080/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "features": {
    "continuous_evolution": "operational",
    "pareto_evolution": "operational"
  }
}
```

### 5. Access Dashboard

Open browser to: **http://localhost:8080/dashboard**

**🎉 Done! You now have a fully functional Agentic Forge platform running!**

---

## 💻 Local Development

For active development with hot reload.

### 1. Install Python Dependencies

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-api.txt
```

### 2. Set Environment Variables

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export LOG_LEVEL=debug
```

### 3. Run API Server

```bash
cd src
python -m uvicorn superstandard.api.server:app --reload --port 8080
```

### 4. Run Demo

```bash
# In separate terminal
python examples/complete_platform_demo.py
```

---

## 🏭 Production Deployment

Production-ready deployment with all recommended features.

### Architecture

```
┌─────────────────────────────────────────┐
│         Load Balancer (HTTPS)           │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
┌─────────┐         ┌─────────┐
│  API 1  │         │  API 2  │  (Multiple instances)
└────┬────┘         └────┬────┘
     │                   │
     └─────────┬─────────┘
               ▼
     ┌──────────────────┐
     │    PostgreSQL    │
     └──────────────────┘
               │
               ▼
     ┌──────────────────┐
     │      Redis       │
     └──────────────────┘
```

### 1. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.python
      target: production
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
    environment:
      - ENABLE_PERSISTENCE=true
      - ENABLE_REDIS=true
      - LOG_LEVEL=info
    depends_on:
      - postgres
      - redis
    restart: always

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    restart: always

volumes:
  postgres-data:
  redis-data:
```

### 2. NGINX Configuration

Create `nginx.conf`:

```nginx
upstream api_backend {
    least_conn;
    server api:8080;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Proxy to API
    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://api_backend;
    }
}
```

### 3. Deploy Production

```bash
# Set production environment
export POSTGRES_PASSWORD=$(openssl rand -hex 32)
export REDIS_PASSWORD=$(openssl rand -hex 32)

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f api
```

---

## ☁️ Cloud Platforms

### Deploying on AWS

#### Option 1: EC2 Instance

**1. Launch EC2 Instance**:
- AMI: Ubuntu 22.04 LTS
- Instance Type: t3.medium (minimum), t3.large (recommended)
- Storage: 20GB+ SSD
- Security Group: Allow ports 80, 443, 8080

**2. Connect and Setup**:

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone https://github.com/yourorg/multiAgentStandardsProtocol.git
cd multiAgentStandardsProtocol

# Configure environment
cp .env.example .env
nano .env  # Add your API keys

# Deploy
docker-compose -f docker-compose.python.yml up -d
```

**3. Configure Domain** (optional):
- Point your domain to EC2 public IP
- Install certbot for SSL:
  ```bash
  sudo apt install certbot python3-certbot-nginx
  sudo certbot --nginx -d your-domain.com
  ```

#### Option 2: ECS (Elastic Container Service)

**1. Create ECR Repository**:

```bash
aws ecr create-repository --repository-name agentic-forge
```

**2. Build and Push Image**:

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build
docker build -f Dockerfile.python -t agentic-forge .

# Tag
docker tag agentic-forge:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/agentic-forge:latest

# Push
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/agentic-forge:latest
```

**3. Create ECS Task Definition**:

Create `task-definition.json`:

```json
{
  "family": "agentic-forge",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/agentic-forge:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ANTHROPIC_API_KEY",
          "value": "your-key-here"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/agentic-forge",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "api"
        }
      }
    }
  ]
}
```

**4. Create ECS Service**:

```bash
# Create cluster
aws ecs create-cluster --cluster-name agentic-forge-cluster

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster agentic-forge-cluster \
  --service-name agentic-forge-service \
  --task-definition agentic-forge \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

### Deploying on GCP

#### Using Cloud Run (Serverless)

**1. Build and Push to Container Registry**:

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/agentic-forge -f Dockerfile.python

# Deploy to Cloud Run
gcloud run deploy agentic-forge \
  --image gcr.io/YOUR_PROJECT_ID/agentic-forge \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ANTHROPIC_API_KEY=your-key-here \
  --memory 2Gi \
  --cpu 2
```

**2. Get Service URL**:

```bash
gcloud run services describe agentic-forge --platform managed --region us-central1 --format 'value(status.url)'
```

---

### Deploying on Digital Ocean

**1. Create Droplet**:
- Image: Docker on Ubuntu 22.04
- Plan: Basic - $24/month (2 vCPU, 4GB RAM)
- Add SSH key

**2. Connect and Deploy**:

```bash
# SSH into droplet
ssh root@your-droplet-ip

# Clone repository
git clone https://github.com/yourorg/multiAgentStandardsProtocol.git
cd multiAgentStandardsProtocol

# Configure
cp .env.example .env
nano .env

# Deploy
docker-compose -f docker-compose.python.yml up -d
```

**3. Setup Domain**:
- Add A record pointing to droplet IP
- Install SSL:
  ```bash
  apt install certbot
  certbot certonly --standalone -d your-domain.com
  ```

---

### Deploying on Azure

**Using Azure Container Instances**:

```bash
# Create resource group
az group create --name agentic-forge-rg --location eastus

# Create container
az container create \
  --resource-group agentic-forge-rg \
  --name agentic-forge \
  --image YOUR_REGISTRY/agentic-forge:latest \
  --cpu 2 \
  --memory 4 \
  --dns-name-label agentic-forge \
  --ports 8080 \
  --environment-variables \
    ANTHROPIC_API_KEY=your-key-here

# Get URL
az container show \
  --resource-group agentic-forge-rg \
  --name agentic-forge \
  --query ipAddress.fqdn
```

---

## ⚙️ Configuration

### Environment Variables

See `.env.example` for all available configuration options.

**Key Variables**:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | ✅ Yes | - |
| `API_PORT` | Server port | No | 8080 |
| `LOG_LEVEL` | Logging level | No | info |
| `ENABLE_CONTINUOUS_EVOLUTION` | Enable auto-evolution | No | true |
| `ENABLE_PERSISTENCE` | Enable database | No | false |
| `REDIS_URL` | Redis connection | No | - |

### Feature Flags

Control which features are enabled:

```bash
# In .env file
ENABLE_CONTINUOUS_EVOLUTION=true
ENABLE_PARETO_EVOLUTION=true
ENABLE_BACKTESTING=true
ENABLE_ANALYTICS=true
```

---

## 📊 Monitoring & Logs

### Health Checks

```bash
# Basic health
curl http://localhost:8080/health

# Detailed health with metrics
curl http://localhost:8080/api/health
```

### Logs

```bash
# Docker logs
docker-compose -f docker-compose.python.yml logs -f api

# Last 100 lines
docker-compose -f docker-compose.python.yml logs --tail=100 api

# Specific time range
docker-compose -f docker-compose.python.yml logs --since 1h api
```

### Monitoring with Grafana

```bash
# Start with monitoring
docker-compose -f docker-compose.python.yml --profile monitoring up -d

# Access Grafana
open http://localhost:3000
# Login: admin / admin
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Port Already in Use**:
```bash
# Check what's using port 8080
lsof -i :8080

# Change port in .env
API_PORT=8081
```

**2. Out of Memory**:
```bash
# Increase Docker memory limit
docker-compose -f docker-compose.python.yml down
# Edit docker-compose.python.yml, increase memory limits
docker-compose -f docker-compose.python.yml up -d
```

**3. API Key Not Working**:
```bash
# Verify environment variable is set
docker-compose -f docker-compose.python.yml exec api env | grep ANTHROPIC

# If missing, check .env file and restart
docker-compose -f docker-compose.python.yml restart api
```

**4. Health Check Failing**:
```bash
# Check logs for errors
docker-compose -f docker-compose.python.yml logs api

# Verify server is running
curl -v http://localhost:8080/health
```

### Performance Tuning

**Increase Worker Threads**:
```bash
# In .env
WORKER_THREADS=8
MAX_CONCURRENT_TASKS=20
```

**Enable Redis Caching**:
```bash
ENABLE_REDIS=true
REDIS_URL=redis://redis:6379/0
```

**Scale Horizontally**:
```bash
# In docker-compose.prod.yml
services:
  api:
    deploy:
      replicas: 5  # Run 5 instances
```

---

## 🎯 Next Steps

After deployment:

1. **Explore Dashboard**: http://your-domain/dashboard
2. **Run Demo**: `python examples/complete_platform_demo.py`
3. **Read Guides**:
   - `COMPLETE_PLATFORM_GUIDE.md` - All features
   - `CONTINUOUS_EVOLUTION_GUIDE.md` - Auto-evolution
4. **Enable Monitoring**: Start with `--profile monitoring`
5. **Setup Backups**: Configure PostgreSQL backups
6. **Enable SSL**: Use certbot for HTTPS

---

## 📚 Additional Resources

- **Main Documentation**: `README.md`
- **Platform Guide**: `COMPLETE_PLATFORM_GUIDE.md`
- **API Reference**: http://localhost:8080/docs (when running)
- **Examples**: `examples/` directory

---

**Deployed successfully? You now have a production-ready autonomous multi-agent platform! 🚀**

Questions? Open an issue on GitHub or check the troubleshooting section above.
