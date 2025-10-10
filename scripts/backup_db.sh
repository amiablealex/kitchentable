#!/bin/bash
BACKUP_DIR="/home/pi/kitchentable/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_PATH="/home/pi/kitchentable/kitchen_table.db"

mkdir -p $BACKUP_DIR

# Create backup
cp $DB_PATH "$BACKUP_DIR/kitchen_table_$DATE.db"

# Keep only last 30 backups
ls -t $BACKUP_DIR/kitchen_table_*.db | tail -n +31 | xargs -r rm

echo "Backup completed: kitchen_table_$DATE.db"
