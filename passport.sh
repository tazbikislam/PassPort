#!/bin/bash
APP_DIR="/home/tazbik/Documents/Python/passport"
VENV_DIR="$APP_DIR/.venv"
ICON_PATH="$APP_DIR/icons/passport.png"

show_notification() {
    if command -v notify-send &> /dev/null; then
        notify-send -i "$ICON_PATH" "PassPort" "$1"
    fi
}

cd "$APP_DIR" || exit 1

if [ ! -d "$VENV_DIR" ]; then
    echo "irtual environment not found!"
    echo "Please run setup first: python -m venv .venv && source .venv/bin/activate && pip install -e ."
    exit 1
fi

source "$VENV_DIR/bin/activate"

case "${1:-}" in
    init)
        python -m passport.main init
        ;;
    backup)
        echo "Creating backup..."
        BACKUP_DIR="$HOME/passport-backups"
        mkdir -p "$BACKUP_DIR"
        BACKUP_FILE="$BACKUP_DIR/passport-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
        tar -czf "$BACKUP_FILE" passport.key passwords.enc .env
        chmod 600 "$BACKUP_FILE"
        echo "Backup created: $BACKUP_FILE"
        show_notification "Backup created successfully"
        ;;
    *)
        python -m passport.main
        ;;
esac

deactivate 2>/dev/null