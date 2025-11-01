# Production Deployment Guide

This guide covers deploying the License Compliance Checker (LCC) to a production environment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Options](#deployment-options)
- [Configuration](#configuration)
- [Security](#security)
- [Monitoring](#monitoring)
- [Backup & Recovery](#backup--recovery)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 2GB
- Disk: 20GB SSD
- OS: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)

**Recommended:**
- CPU: 4 cores
- RAM: 4GB
- Disk: 50GB SSD
- OS: Ubuntu 22.04 LTS

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Git
- OpenSSL (for generating secrets)

### Network Requirements

- Ports 80, 443 (HTTP/HTTPS)
- Port 8000 (API - can be internal)
- Port 3000 (Dashboard - can be internal)
- Outbound internet access for package registries

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/license-compliance-checker.git
cd license-compliance-checker
```

### 2. Generate Secrets

```bash
# Generate secret keys
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 32  # For JWT_SECRET_KEY
openssl rand -hex 16  # For REDIS_PASSWORD
openssl rand -hex 16  # For POSTGRES_PASSWORD
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values
nano .env  # or vim, code, etc.
```

**Critical values to change:**
- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `ADMIN_PASSWORD`
- `CORS_ORIGINS` (set to your domain)

### 4. Deploy

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 5. Verify Deployment

```bash
# Check API health
curl http://localhost:8000/health

# Check dashboard
curl http://localhost:3000

# Create admin user (if not auto-created)
docker-compose -f docker-compose.prod.yml exec api \
  lcc auth create-user admin password123 --role admin
```

---

## Deployment Options

### Option 1: Docker Compose (Recommended)

Best for: Single server, small to medium deployments

```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Pros:**
- Easy to deploy
- All services orchestrated
- Good for most use cases

**Cons:**
- Limited scaling
- Single point of failure

### Option 2: Docker Swarm

Best for: Multi-server, high availability

```bash
docker swarm init
docker stack deploy -c docker-compose.prod.yml lcc
```

**Pros:**
- High availability
- Built-in load balancing
- Easy scaling

**Cons:**
- More complex setup
- Requires multiple servers

### Option 3: Kubernetes

Best for: Large scale, enterprise deployments

See `k8s/` directory for manifests.

```bash
kubectl apply -f k8s/
```

**Pros:**
- Maximum scalability
- Advanced orchestration
- Industry standard

**Cons:**
- Complex setup
- Requires K8s expertise

### Option 4: Managed Services

Best for: Minimal operations overhead

- **AWS**: ECS/Fargate + RDS + ElastiCache
- **GCP**: Cloud Run + Cloud SQL + Memorystore
- **Azure**: Container Instances + Azure Database + Redis Cache

---

## Configuration

### Environment Variables

See [.env.example](.env.example) for all available variables.

#### Essential Variables

```bash
# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>

# Database
POSTGRES_PASSWORD=<strong-password>

# Redis
REDIS_PASSWORD=<strong-password>

# Admin
ADMIN_PASSWORD=<strong-password>

# CORS
CORS_ORIGINS=https://yourdomain.com
```

### Database Configuration

#### PostgreSQL (Recommended for Production)

```bash
# In .env
POSTGRES_DB=lcc
POSTGRES_USER=lcc
POSTGRES_PASSWORD=<secure-password>
```

**Connection string:**
```
postgresql://lcc:password@postgres:5432/lcc
```

#### SQLite (Alternative for Small Deployments)

```bash
# In .env
LCC_DB_PATH=/var/lib/lcc/lcc.db
```

### Cache Configuration

#### Redis (Recommended)

```bash
REDIS_URL=redis://:password@redis:6379/0
REDIS_PASSWORD=<secure-password>
```

#### In-Memory Cache (Development Only)

```bash
# No configuration needed, but not persistent
```

### Policy Configuration

```bash
LCC_POLICY_DIR=/var/lib/lcc/policies
LCC_DEFAULT_POLICY=permissive
```

---

## Security

### SSL/TLS Configuration

#### 1. Generate Certificates

**Option A: Let's Encrypt (Recommended)**

```bash
# Install certbot
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com

# Certificates will be in:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

**Option B: Self-Signed (Development/Testing)**

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem
```

#### 2. Configure Nginx

See `nginx/conf.d/ssl.conf` for SSL configuration.

### Firewall Configuration

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (if needed)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

### Security Headers

Nginx is configured with:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security`
- `Content-Security-Policy`

### Rate Limiting

```bash
# In .env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000
```

### Authentication

#### JWT Configuration

```bash
JWT_EXPIRATION_MINUTES=60
JWT_REFRESH_EXPIRATION_DAYS=30
JWT_ALGORITHM=HS256
```

#### Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

---

## Monitoring

### Health Checks

**API Health:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{"status": "ok", "version": "1.0.0"}
```

### Prometheus Metrics

Enable monitoring stack:

```bash
docker-compose -f docker-compose.prod.yml --profile monitoring up -d
```

**Access:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

### Log Aggregation

Logs are stored in JSON format:

```bash
# View API logs
docker-compose logs -f api

# View all logs
docker-compose logs -f

# Export logs
docker-compose logs --no-color > logs/export.log
```

### Key Metrics to Monitor

- **Request Rate**: requests/second
- **Error Rate**: errors/requests
- **Response Time**: p50, p95, p99
- **CPU Usage**: <80%
- **Memory Usage**: <80%
- **Disk Usage**: <90%
- **Database Connections**: <max_connections

### Alerts

Configure alerts for:
- Service down
- High error rate (>5%)
- High response time (>1s p95)
- High resource usage (>90%)
- Failed health checks

---

## Backup & Recovery

### Automated Backups

```bash
# Enable backups in .env
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
```

### Manual Backup

#### Database Backup

**PostgreSQL:**
```bash
docker-compose exec postgres pg_dump -U lcc lcc > backup/lcc_$(date +%Y%m%d).sql
```

**SQLite:**
```bash
docker-compose exec api sqlite3 /var/lib/lcc/lcc.db ".backup backup/lcc_$(date +%Y%m%d).db"
```

#### Full Backup

```bash
# Backup script
./scripts/backup.sh

# What's backed up:
# - Database
# - Policies
# - Cache
# - Logs
# - Configuration
```

### Restore

#### Database Restore

**PostgreSQL:**
```bash
docker-compose exec -T postgres psql -U lcc lcc < backup/lcc_20241031.sql
```

**SQLite:**
```bash
docker-compose exec api sqlite3 /var/lib/lcc/lcc.db ".restore backup/lcc_20241031.db"
```

#### Full Restore

```bash
./scripts/restore.sh backup/lcc_20241031.tar.gz
```

### Disaster Recovery Plan

1. **Data Loss Prevention:**
   - Daily automated backups
   - Offsite backup storage
   - Backup verification

2. **Recovery Time Objective (RTO):** < 1 hour
3. **Recovery Point Objective (RPO):** < 24 hours

---

## Scaling

### Horizontal Scaling

#### API Scaling

```bash
docker-compose -f docker-compose.prod.yml up -d --scale api=3
```

#### Load Balancer Configuration

Nginx automatically distributes load across API instances.

### Vertical Scaling

```bash
# Increase resource limits in .env
API_CPU_LIMIT=4.0
API_MEMORY_LIMIT=2G
```

### Database Scaling

#### PostgreSQL Optimization

```sql
-- Tune PostgreSQL
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET wal_buffers = '16MB';
SELECT pg_reload_conf();
```

#### Connection Pooling

Use PgBouncer for connection pooling:

```yaml
services:
  pgbouncer:
    image: pgbouncer/pgbouncer
    environment:
      DATABASES_HOST: postgres
      DATABASES_PORT: 5432
      DATABASES_USER: lcc
      DATABASES_PASSWORD: ${POSTGRES_PASSWORD}
      PGBOUNCER_POOL_MODE: transaction
      PGBOUNCER_MAX_CLIENT_CONN: 1000
      PGBOUNCER_DEFAULT_POOL_SIZE: 25
```

### Cache Scaling

#### Redis Cluster

For high availability, use Redis Cluster:

```bash
# See redis-cluster.yml for configuration
docker-compose -f redis-cluster.yml up -d
```

---

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs api

# Check configuration
docker-compose -f docker-compose.prod.yml config

# Validate environment
docker-compose -f docker-compose.prod.yml exec api env
```

#### 2. Database Connection Errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U lcc -d lcc -c "SELECT 1"

# Check credentials
echo $POSTGRES_PASSWORD
```

#### 3. High Memory Usage

```bash
# Check container stats
docker stats

# Adjust limits
# Edit API_MEMORY_LIMIT in .env
docker-compose -f docker-compose.prod.yml up -d
```

#### 4. Slow API Response

```bash
# Check database performance
docker-compose exec postgres pg_stat_statements

# Check cache hit rate
docker-compose exec redis redis-cli INFO stats

# Enable query logging
DEBUG_SQL=true
```

### Debug Mode

**⚠️ DO NOT enable in production!**

```bash
# Temporarily enable debug mode
docker-compose -f docker-compose.prod.yml exec api \
  env DEBUG=true lcc server
```

### Support

- **Documentation**: https://docs.lcc.dev
- **GitHub Issues**: https://github.com/your-org/lcc/issues
- **Email**: support@lcc.dev

---

## Checklist

### Pre-Deployment

- [ ] System requirements met
- [ ] Docker installed and configured
- [ ] Environment variables configured
- [ ] Secrets generated and stored securely
- [ ] SSL certificates obtained
- [ ] Firewall configured
- [ ] Backup strategy defined

### Post-Deployment

- [ ] Services started successfully
- [ ] Health checks passing
- [ ] Admin user created
- [ ] Dashboard accessible
- [ ] API endpoints responding
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] Alerts configured
- [ ] Documentation reviewed

### Security Checklist

- [ ] Default passwords changed
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] SSL/TLS configured
- [ ] Security headers enabled
- [ ] Firewall rules applied
- [ ] Logs being collected
- [ ] Secrets properly managed

---

## Next Steps

1. [Configure policies](./POLICY_GUIDE.md)
2. [Set up CI/CD integration](./CI_CD.md)
3. [Configure notifications](./NOTIFICATIONS.md)
4. [Review troubleshooting guide](./TROUBLESHOOTING.md)

---

**Last Updated:** 2024-10-31
**Version:** 1.0.0
