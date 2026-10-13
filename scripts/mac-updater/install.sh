#!/bin/bash
# One-time setup: installs the weekly writing-page job on this Mac and runs it once.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.mikelewis.update-writing.plist"

mkdir -p "$HOME/Library/Scripts" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
cp "$DIR/update-writing.sh" "$HOME/Library/Scripts/update-writing.sh"
chmod +x "$HOME/Library/Scripts/update-writing.sh"
sed "s|__HOME__|$HOME|g" "$DIR/com.mikelewis.update-writing.plist" > "$PLIST"

launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed: runs Tuesdays at 9 AM. Log: ~/Library/Logs/update-writing.log"
echo
echo "Running it once now to test..."
/bin/bash "$HOME/Library/Scripts/update-writing.sh"
