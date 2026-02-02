# Production Deployment Checklist

This checklist ensures all critical steps are completed before deploying License Compliance Checker to production.

## Pre-Deployment Checklist

### 1. Environment Configuration

- [ ] Copy `.env.example` to `.env`
- [ ] Generate secure `SECRET_KEY` (`openssl rand -hex 32`)
- [ ] Generate secure `JWT_SECRET_KEY` (`openssl rand -hex 32`)
- [ ] Set strong `POSTGRES_PASSWORD` (min 16 characters)
- [ ] Set strong `REDIS_PASSWORD`
- [ ] Change default `ADMIN_PASSWORD` from "changeme"
- [ ] Update `ADMIN_EMAIL` to valid email
- [ ] Configure `CORS_ORIGINS` with actual domain(s)
- [ ] Set `ENVIRONMENT=production`
- [ ] Verify `DEBUG=false`
- [ ] Configure `SENTRY_DSN` for error tracking (optional)
- [ ] Set up `GITHUB_TOKEN` for repository scanning (if needed)

### 2. SSL/TLS Certificates

- [ ] Generate or obtain SSL certificates
- [ ] Place certificates in `nginx/ssl/` directory
  - [ ] `cert.pem` (public certificate)
  - [ ] `key.pem` (private key)
  - [ ] `dhparam.pem` (DH parameters)
- [ ] Set correct file permissions (600 for private keys)
- [ ] Update domain names in `nginx/conf.d/default.conf`
- [ ] Test SSL configuration: `openssl s_client -connect domain:443`
- [ ] Verify SSL Labs rating (target: A+)

### 3. DNS Configuration

- [ ] Configure A record for main domain
- [ ] Configure A record for `api.yourdomain.com` (if using subdomain)
- [ ] Configure A record for `monitoring.yourdomain.com` (optional)
- [ ] Verify DNS propagation: `dig yourdomain.com`
- [ ] Wait for DNS to fully propagate (24-48 hours)

### 4. Server Prerequisites

- [ ] Install Docker (20.10+)
- [ ] Install Docker Compose (2.0+)
- [ ] Configure firewall rules
  - [ ] Allow port 80 (HTTP)
  - [ ] Allow port 443 (HTTPS)
  - [ ] Block direct access to 5432 (PostgreSQL)
  - [ ] Block direct access to 6379 (Redis)
  - [ ] Block direct access to 8000 (API - behind nginx)
- [ ] Verify disk space (min 20GB free)
- [ ] Verify RAM (min 2GB available)
- [ ] Set up automatic security updates
- [ ] Configure system monitoring

### 5. Database Setup

- [ ] Review `scripts/init-db.sql`
- [ ] Plan database backup strategy
- [ ] Configure PostgreSQL connection pooling
- [ ] Set appropriate `shared_buffers` for PostgreSQL
- [ ] Enable PostgreSQL query logging (optional)
- [ ] Test database backup/restore process

### 6. Code & Build

- [ ] Pull latest stable release (not development branch)
- [ ] Review `CHANGELOG.md` for breaking changes
- [ ] Build Docker images:
  ```bash
  docker build -t lcc:latest .
  docker build -t lcc-dashboard:latest ./dashboard
  ```
- [ ] Tag images with version:
  ```bash
  docker tag lcc:latest lcc:1.0.0
  docker tag lcc-dashboard:latest lcc-dashboard:1.0.0
  ```
- [ ] Push images to registry (if using private registry)

### 7. Security Review

- [ ] Review all environment variables for sensitive data
- [ ] Ensure no secrets in version control
- [ ] Verify `.gitignore` includes `.env`, `*.key`, `*.pem`
- [ ] Enable rate limiting in nginx
- [ ] Review CORS configuration
- [ ] Enable security headers (HSTS, CSP, X-Frame-Options)
- [ ] Disable debug endpoints in production
- [ ] Set up intrusion detection (fail2ban, etc.)
- [ ] Plan security update schedule
- [ ] Document incident response plan

### 8. Monitoring & Logging

- [ ] Configure Prometheus data retention
- [ ] Set up Grafana dashboards
- [ ] Configure alerting rules (optional)
- [ ] Set up log aggregation (optional: ELK, Loki)
- [ ] Test health check endpoints
- [ ] Set up uptime monitoring (external service)
- [ ] Configure error tracking (Sentry)
- [ ] Document monitoring runbooks

### 9. Backup Strategy

- [ ] Test backup script: `./scripts/backup.sh`
- [ ] Schedule automated backups (cron)
- [ ] Configure backup retention policy
- [ ] Test restore procedure: `./scripts/restore.sh`
- [ ] Set up off-site backup storage (S3, etc.)
- [ ] Document backup/restore procedures
- [ ] Verify backup encryption (if required)

### 10. Testing

- [ ] Test API health endpoint: `curl https://api.yourdomain.com/health`
- [ ] Test dashboard access: `https://yourdomain.com`
- [ ] Verify authentication flow
- [ ] Test policy creation and validation
- [ ] Run a test scan
- [ ] Verify database writes
- [ ] Test cache (Redis) functionality
- [ ] Verify SSL certificate
- [ ] Load test with expected traffic
- [ ] Test failover scenarios

## Deployment Steps

### 1. Initial Deployment

```bash
# 1. Clone repository
git clone https://github.com/yourusername/license-compliance-checker.git
cd license-compliance-checker

# 2. Checkout stable version
git checkout v1.0.0

# 3. Configure environment
cp .env.example .env
nano .env

# 4. Build images (if not using registry)
docker-compose -f docker-compose.prod.yml build

# 5. Start services
docker-compose -f docker-compose.prod.yml up -d

# 6. Initialize database
docker-compose -f docker-compose.prod.yml exec postgres psql -U lcc -d lcc -f /scripts/init-db.sql

# 7. Create admin user (if not created automatically)
docker-compose -f docker-compose.prod.yml exec api lcc create-user admin --admin

# 8. Verify deployment
docker-compose -f docker-compose.prod.yml ps
curl https://api.yourdomain.com/health
```

### 2. Verify Deployment

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs --tail=100

# Verify API health
curl https://api.yourdomain.com/health

# Verify dashboard
curl -I https://yourdomain.com

# Check database connection
docker-compose -f docker-compose.prod.yml exec postgres psql -U lcc -c "SELECT 1;"

# Check Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Verify SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com | grep "Verify return code"
```

### 3. Smoke Tests

- [ ] Login to dashboard with admin credentials
- [ ] Create a test policy
- [ ] Run a test scan
- [ ] Verify scan results in dashboard
- [ ] Check monitoring dashboards (Grafana)
- [ ] Verify logs are being collected
- [ ] Test API authentication
- [ ] Verify rate limiting is working

## Post-Deployment

### Immediate (First Hour)

- [ ] Monitor logs for errors
- [ ] Check system resource usage (CPU, memory, disk)
- [ ] Verify all services are healthy
- [ ] Test critical user flows
- [ ] Update documentation with production URLs
- [ ] Notify team of successful deployment

### First Day

- [ ] Monitor application performance
- [ ] Review error rates in Sentry/logs
- [ ] Check database performance
- [ ] Verify backup job ran successfully
- [ ] Test disaster recovery procedure
- [ ] Document any issues encountered

### First Week

- [ ] Review monitoring dashboards daily
- [ ] Analyze performance metrics
- [ ] Review security logs
- [ ] Check for any security updates
- [ ] Gather user feedback
- [ ] Plan performance optimizations

### Ongoing Maintenance

- [ ] Weekly: Review logs and metrics
- [ ] Weekly: Check disk space
- [ ] Weekly: Verify backups
- [ ] Monthly: Security updates
- [ ] Monthly: Performance review
- [ ] Quarterly: Disaster recovery drill
- [ ] Quarterly: Security audit

## Rollback Plan

If issues are discovered after deployment:

```bash
# 1. Stop services
docker-compose -f docker-compose.prod.yml down

# 2. Restore from backup
./scripts/restore.sh backups/lcc_backup_YYYYMMDD_HHMMSS.tar.gz

# 3. Checkout previous stable version
git checkout v0.9.0

# 4. Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# 5. Verify rollback
curl https://api.yourdomain.com/health
```

## Emergency Contacts

Document team contacts for production issues:

- **On-Call Engineer**: [contact info]
- **DevOps Lead**: [contact info]
- **Database Admin**: [contact info]
- **Security Team**: [contact info]

## Compliance & Legal

- [ ] Review data privacy requirements (GDPR, CCPA)
- [ ] Document data retention policies
- [ ] Review license compliance for dependencies
- [ ] Update Terms of Service
- [ ] Update Privacy Policy
- [ ] Configure audit logging
- [ ] Set up access controls

## Documentation Updates

- [ ] Update README.md with production info
- [ ] Document API endpoints
- [ ] Create user guide
- [ ] Document troubleshooting procedures
- [ ] Create runbooks for common tasks
- [ ] Update architecture diagrams
- [ ] Document change management process

## Sign-Off

Before marking deployment as complete, obtain sign-off from:

- [ ] **Technical Lead**: _________________ Date: _______
- [ ] **Security Team**: _________________ Date: _______
- [ ] **Operations Team**: _______________ Date: _______
- [ ] **Product Owner**: _________________ Date: _______

---

## Reference

- Deployment Guide: [docs/DEPLOYMENT.md](DEPLOYMENT.md)
- Architecture: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- Security: [docs/SECURITY.md](SECURITY.md)
- Troubleshooting: [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)
