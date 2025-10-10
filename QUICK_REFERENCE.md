# Kitchen Table - Quick Reference Guide

## Essential Commands

### Service Management
```bash
# Start/Stop/Restart
sudo systemctl start kitchen-table
sudo systemctl stop kitchen-table
sudo systemctl restart kitchen-table
sudo systemctl status kitchen-table

# Enable/Disable autostart
sudo systemctl enable kitchen-table
sudo systemctl disable kitchen-table

# View logs
sudo journalctl -u kitchen-table -f
sudo journalctl -u kitchen-table -n 100
```

### Application Logs
```bash
# Real-time application log
tail -f /var/www/kitchen-table/logs/kitchen_table.log

# Real-time error log
tail -f /var/www/kitchen-table/logs/error.log

# Real-time access log
tail -f /var/www/kitchen-table/logs/access.log

# Cron job logs
tail -f /var/www/kitchen-table/logs/cron.log
```

### Database Operations
```bash
# Backup database
cp /var/www/kitchen-table/kitchen_table.db /var/www/kitchen-table/backups/backup_$(date +%Y%m%d).db

# Open database
sqlite3 /var/www/kitchen-table/kitchen_table.db

# Useful SQL queries
sqlite3 kitchen_table.db "SELECT COUNT(*) FROM users;"
sqlite3 kitchen_table.db "SELECT COUNT(*) FROM tables;"
sqlite3 kitchen_table.db "SELECT * FROM tables;"
```

### Code Updates
```bash
cd /var/www/kitchen-table
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart kitchen-table
```

### Nginx
```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# Restart Nginx
sudo systemctl restart nginx

# View logs
sudo tail -f /var/log/nginx/error.log
```

### Cloudflare Tunnel
```bash
# Status
sudo systemctl status cloudflared

# Restart
sudo systemctl restart cloudflared

# Logs
sudo journalctl -u cloudflared -f

# Test tunnel
cloudflared tunnel info kitchen-table
```

## File Locations

| Purpose | Location |
|---------|----------|
| Application | `/var/www/kitchen-table/` |
| Virtual Environment | `/var/www/kitchen-table/venv/` |
| Database | `/var/www/kitchen-table/kitchen_table.db` |
| Logs | `/var/www/kitchen-table/logs/` |
| Backups | `/var/www/kitchen-table/backups/` |
| Environment | `/var/www/kitchen-table/.env` |
| Systemd Service | `/etc/systemd/system/kitchen-table.service` |
| Nginx Config | `/etc/nginx/sites-available/kitchen-table` |
| Cloudflared Config | `~/.cloudflared/config.yml` |

## Port Configuration

- **Gunicorn**: 127.0.0.1:8003 (internal only)
- **Nginx**: Port 80 (HTTP)
- **Cloudflare Tunnel**: Handles HTTPS externally

## Environment Variables

Located in `/var/www/kitchen-table/.env`:

```bash
SECRET_KEY=<your-secret-key>
JWT_SECRET_KEY=<your-jwt-secret-key>
DATABASE_PATH=kitchen_table.db
LOG_LEVEL=INFO
```

## Cron Jobs

```bash
# View current cron jobs
crontab -l

# Edit cron jobs
crontab -e
```

Current jobs:
- **Daily Prompts**: `1 0 * * *` (12:01 AM daily)
- **Database Backup**: `0 2 * * *` (2:00 AM daily)

## Troubleshooting

### Application Not Loading

1. Check service status:
   ```bash
   sudo systemctl status kitchen-table
   ```

2. Check logs:
   ```bash
   sudo journalctl -u kitchen-table -n 50
   ```

3. Check if port is in use:
   ```bash
   sudo netstat -tlnp | grep 8003
   ```

4. Restart service:
   ```bash
   sudo systemctl restart kitchen-table
   ```

### 502 Bad Gateway

1. Verify Gunicorn is running:
   ```bash
   sudo systemctl status kitchen-table
   ```

2. Check Nginx configuration:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. Check connection:
   ```bash
   curl http://127.0.0.1:8003
   ```

### Database Locked

```bash
# Check for .db-wal and .db-shm files
ls -la /var/www/kitchen-table/*.db*

# If stuck, restart application
sudo systemctl restart kitchen-table
```

### Cloudflare Tunnel Down

```bash
# Check status
sudo systemctl status cloudflared

# Restart tunnel
sudo systemctl restart cloudflared

# Verify tunnel
cloudflared tunnel info kitchen-table
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R $USER:www-data /var/www/kitchen-table

# Fix database permissions
chmod 664 /var/www/kitchen-table/kitchen_table.db
chmod 775 /var/www/kitchen-table
```

## Performance Monitoring

### Resource Usage
```bash
# Overall system
htop

# Specific process
ps aux | grep gunicorn
ps aux | grep nginx

# Memory
free -h

# Disk
df -h
```

### Database Size
```bash
# Current size
ls -lh /var/www/kitchen-table/kitchen_table.db

# Table sizes
sqlite3 kitchen_table.db "SELECT name, COUNT(*) as count FROM sqlite_master WHERE type='table' GROUP BY name;"
```

### Log Sizes
```bash
# Check log sizes
du -sh /var/www/kitchen-table/logs/*

# Rotate logs if needed
sudo logrotate -f /etc/logrotate.d/kitchen-table
```

## Common Database Queries

```bash
# Connect to database
sqlite3 /var/www/kitchen-table/kitchen_table.db
```

### User Statistics
```sql
-- Total users
SELECT COUNT(*) FROM users;

-- Recent signups
SELECT username, display_name, created_at 
FROM users 
ORDER BY created_at DESC 
LIMIT 10;

-- Active users (last 7 days)
SELECT COUNT(*) FROM users 
WHERE last_active >= date('now', '-7 days');
```

### Table Statistics
```sql
-- Total tables
SELECT COUNT(*) FROM tables;

-- Table member counts
SELECT t.name, COUNT(tm.id) as members
FROM tables t
LEFT JOIN table_members tm ON t.id = tm.table_id
GROUP BY t.id, t.name;

-- Tables with their invite codes
SELECT name, invite_code, created_at 
FROM tables 
ORDER BY created_at DESC;
```

### Prompt Statistics
```sql
-- Total prompts created
SELECT COUNT(*) FROM prompts;

-- Prompts by date
SELECT prompt_date, COUNT(*) as count
FROM prompts
GROUP BY prompt_date
ORDER BY prompt_date DESC
LIMIT 7;

-- Response rate
SELECT 
    p.prompt_date,
    COUNT(DISTINCT r.id) as responses,
    COUNT(DISTINCT tm.user_id) as members
FROM prompts p
LEFT JOIN responses r ON p.id = r.prompt_id
LEFT JOIN table_members tm ON p.table_id = tm.table_id
WHERE p.prompt_date >= date('now', '-7 days')
GROUP BY p.prompt_date
ORDER BY p.prompt_date DESC;
```

### Response Statistics
```sql
-- Total responses
SELECT COUNT(*) FROM responses;

-- Most active users
SELECT u.display_name, COUNT(r.id) as response_count
FROM users u
JOIN responses r ON u.id = r.user_id
GROUP BY u.id, u.display_name
ORDER BY response_count DESC
LIMIT 10;

-- Today's responses
SELECT u.display_name, r.response_text, r.created_at
FROM responses r
JOIN users u ON r.user_id = u.id
JOIN prompts p ON r.prompt_id = p.id
WHERE p.prompt_date = date('now')
ORDER BY r.created_at DESC;
```

## Security Checklist

- [ ] `.env` file contains secure random secrets
- [ ] Database file has correct permissions (664)
- [ ] Cloudflare SSL/TLS set to "Full" or "Full (strict)"
- [ ] Regular backups are running
- [ ] Logs are being monitored
- [ ] System packages are up to date
- [ ] Application dependencies are up to date

## Backup & Restore

### Manual Backup
```bash
# Backup database
cp /var/www/kitchen-table/kitchen_table.db \
   /var/www/kitchen-table/backups/manual_backup_$(date +%Y%m%d_%H%M%S).db

# Backup entire application
sudo tar -czf /home/pi/kitchen-table-backup-$(date +%Y%m%d).tar.gz \
    /var/www/kitchen-table \
    --exclude=/var/www/kitchen-table/venv \
    --exclude=/var/www/kitchen-table/__pycache__
```

### Restore Database
```bash
# Stop application
sudo systemctl stop kitchen-table

# Restore from backup
cp /var/www/kitchen-table/backups/kitchen_table_YYYYMMDD_HHMMSS.db \
   /var/www/kitchen-table/kitchen_table.db

# Start application
sudo systemctl start kitchen-table
```

## URLs

- **Application**: https://kitchen.yourdomain.com
- **Cloudflare Dashboard**: https://dash.cloudflare.com
- **Cloudflare Zero Trust**: https://one.dash.cloudflare.com

## Quick Fixes

### Reset User Password (Manual)
```bash
sqlite3 /var/www/kitchen-table/kitchen_table.db
```
```sql
-- Generate new password hash using Python:
-- python3 -c "from utils.auth import hash_password; print(hash_password('newpassword'))"

UPDATE users 
SET password_hash = '<new-hash>' 
WHERE username = 'username';
```

### Clear Old Logs
```bash
# Clear old application logs
echo > /var/www/kitchen-table/logs/kitchen_table.log
echo > /var/www/kitchen-table/logs/error.log
echo > /var/www/kitchen-table/logs/access.log
```

### Regenerate Secrets
```bash
cd /var/www/kitchen-table
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"

# Update .env with new secrets
nano .env

# Restart application
sudo systemctl restart kitchen-table
```

### Force Create Today's Prompt
```bash
cd /var/www/kitchen-table
source venv/bin/activate
python3 scripts/daily_prompt.py
```

## Contact & Support

For issues or questions about your deployment, check:
1. Application logs
2. Systemd journal
3. Nginx error logs
4. This quick reference guide
5. Full setup instructions (SETUP_INSTRUCTIONS.md)

---

**Last Updated**: Setup date
**Version**: 1.0.0
