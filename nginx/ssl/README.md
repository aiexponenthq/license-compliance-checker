# SSL/TLS Certificates

This directory contains SSL/TLS certificates for HTTPS support.

## Quick Setup (Self-Signed for Development)

For development/testing purposes, generate self-signed certificates:

```bash
# Generate self-signed certificate (valid for 365 days)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Generate Diffie-Hellman parameters (takes a few minutes)
openssl dhparam -out nginx/ssl/dhparam.pem 2048
```

## Production Setup (Let's Encrypt)

For production with real domain, use Let's Encrypt with Certbot:

### Option 1: Standalone Mode (Recommended)

```bash
# Stop nginx temporarily
docker-compose -f docker-compose.prod.yml stop nginx

# Generate certificates
sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos \
  --no-eff-email

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem

# Set permissions
sudo chmod 644 nginx/ssl/cert.pem
sudo chmod 600 nginx/ssl/key.pem

# Start nginx
docker-compose -f docker-compose.prod.yml start nginx
```

### Option 2: Webroot Mode

```bash
# Ensure nginx is running
docker-compose -f docker-compose.prod.yml up -d nginx

# Generate certificates using webroot
sudo certbot certonly --webroot \
  -w /var/www/letsencrypt \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos

# Copy and set permissions (same as above)
```

### Option 3: Docker Certbot

```bash
# Add certbot service to docker-compose.prod.yml
docker run -it --rm \
  -v $(pwd)/nginx/ssl:/etc/letsencrypt \
  -v $(pwd)/nginx/www:/var/www/certbot \
  certbot/certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos \
  --no-eff-email
```

## Certificate Renewal

Let's Encrypt certificates expire after 90 days. Set up auto-renewal:

### Manual Renewal

```bash
# Test renewal (dry run)
sudo certbot renew --dry-run

# Actual renewal
sudo certbot renew

# Copy renewed certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem

# Reload nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Automatic Renewal (Cron)

Add to crontab (`sudo crontab -e`):

```cron
# Renew certificates daily at 2 AM
0 2 * * * certbot renew --quiet --deploy-hook "docker-compose -f /path/to/docker-compose.prod.yml exec nginx nginx -s reload"
```

## Certificate Verification

Verify certificate configuration:

```bash
# Check certificate details
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Check certificate expiration
openssl x509 -in nginx/ssl/cert.pem -noout -dates

# Test SSL configuration
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

## SSL/TLS Best Practices

1. **Strong Protocols**: Use TLS 1.2 and TLS 1.3 only
2. **Strong Ciphers**: Use modern cipher suites (already configured in ssl.conf)
3. **HSTS**: Enable HTTP Strict Transport Security (already configured)
4. **OCSP Stapling**: Enable for better performance (already configured)
5. **Certificate Monitoring**: Monitor expiration dates
6. **Regular Updates**: Keep OpenSSL and Nginx updated

## Testing SSL Configuration

Use online tools to verify SSL configuration:

- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/)
- [Mozilla Observatory](https://observatory.mozilla.org/)

Target: A+ rating on SSL Labs

## Troubleshooting

### Certificate Not Found

```bash
# Check file exists and permissions
ls -la nginx/ssl/
```

### Permission Denied

```bash
# Fix permissions
chmod 644 nginx/ssl/cert.pem
chmod 600 nginx/ssl/key.pem
chown root:root nginx/ssl/*.pem
```

### Nginx Won't Start

```bash
# Check nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Check logs
docker-compose -f docker-compose.prod.yml logs nginx
```

## Security Notes

- **Never commit private keys**: Add `*.key`, `*.pem` to .gitignore
- **Secure key permissions**: Private keys should be readable only by root (600)
- **Backup certificates**: Include in backup strategy
- **Revoke compromised certificates**: Use `certbot revoke` if key is compromised

## Directory Structure

```
nginx/ssl/
├── README.md          # This file
├── cert.pem          # Public certificate (or fullchain.pem)
├── key.pem           # Private key
└── dhparam.pem       # Diffie-Hellman parameters
```

## Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Nginx SSL Module Documentation](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)
