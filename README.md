# 🏠 The Kitchen Table

A warm, intimate web application for staying connected with the people you care about through daily conversation prompts.

## Overview

The Kitchen Table is a cozy digital space where small groups (families, friend circles, book clubs) answer one thoughtful question together each day. It's designed to foster meaningful connections through simple, asynchronous conversations.

### Key Features

- **Daily Questions**: Thoughtful prompts delivered at a customizable time each day
- **Private Groups**: Secure, invite-only "tables" for up to 10 members
- **Simple & Beautiful**: Clean, modern interface optimized for all devices
- **Privacy First**: See others' responses only after you've shared yours
- **Lightweight**: Runs efficiently on a Raspberry Pi 4

## Tech Stack

- **Backend**: Flask (Python 3)
- **Database**: SQLite with WAL mode
- **Frontend**: Vanilla JavaScript, modern CSS
- **Authentication**: JWT tokens with httpOnly cookies
- **Deployment**: Gunicorn, Nginx, Cloudflare Tunnel

## Quick Start

See [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) for complete deployment guide.

```bash
# Clone repository
git clone https://github.com/yourusername/kitchen-table.git
cd kitchen-table

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your secure secrets

# Run development server
python3 app.py
```

Visit `http://localhost:8003` to see the application.

## Project Structure

```
kitchen-table/
├── app.py                 # Main Flask application
├── config.py              # Configuration
├── wsgi.py               # Production entry point
├── models/               # Data models
├── routes/               # API routes and views
├── utils/                # Helper functions
├── templates/            # HTML templates
├── static/               # CSS and JavaScript
└── scripts/              # Cron jobs and utilities
```

## Usage

### For Users

1. **Sign Up**: Create an account with username, email, and display name
2. **Create or Join**: Start your own kitchen table or join with an invite code
3. **Daily Ritual**: Answer the day's question whenever you're ready
4. **Connect**: See what everyone else shared after you respond
5. **Reflect**: Check yesterday's conversation anytime

### For Administrators

- **Table Settings**: Customize table name and question timing
- **Invite Management**: Share the unique invite code with new members
- **Member Overview**: See who's part of your table

## Architecture Highlights

### Security
- Bcrypt password hashing
- JWT authentication with secure httpOnly cookies
- CSRF protection through SameSite cookie policy
- Input validation and sanitization
- Rate limiting on sensitive endpoints

### Performance
- SQLite with WAL mode for concurrent reads
- Indexed queries for fast lookups
- Static asset caching
- Gzip compression
- Efficient polling (30-second intervals)

### User Experience
- Progressive enhancement approach
- Responsive design (mobile-first)
- Minimal JavaScript (no frameworks)
- Graceful error handling
- Loading states and feedback

## Development

### Running Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run application in debug mode
python3 app.py
```

### Database Migrations
Database schema is in `schema.sql`. For changes:

1. Update `schema.sql`
2. Create migration script if needed
3. Test thoroughly before deploying

### Adding New Prompts
Edit `seed_prompts.sql` and re-run the seed script, or add them directly:

```sql
INSERT INTO default_prompts (prompt_text, category) 
VALUES ('Your new prompt here', 'category');
```

## Deployment

Designed to run on Raspberry Pi 4 with:
- Gunicorn as WSGI server (port 8003)
- Nginx as reverse proxy
- Cloudflare Tunnel for secure external access
- Systemd for service management
- Cron for daily prompt generation

See [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) for complete deployment guide.

## Monitoring & Maintenance

### Logs
- Application: `/var/www/kitchen-table/logs/kitchen_table.log`
- Gunicorn: `/var/www/kitchen-table/logs/error.log`
- Access: `/var/www/kitchen-table/logs/access.log`

### Backup
- Database: Automatic daily backups at 2 AM
- Location: `/var/www/kitchen-table/backups/`
- Retention: Last 30 backups

### Health Checks
```bash
# Service status
sudo systemctl status kitchen-table

# View live logs
sudo journalctl -u kitchen-table -f

# Database size
ls -lh kitchen_table.db
```

## Contributing

This is a personal project, but suggestions are welcome! Please open an issue to discuss proposed changes.

## License

This project is private and not licensed for public use.

## Acknowledgments

Built with love for meaningful connections in a digital age.

---

**Note**: This application is designed for small, trusted groups. It's not intended for large-scale social networking.
