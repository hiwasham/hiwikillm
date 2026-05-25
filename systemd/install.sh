#!/usr/bin/env bash
# Install + enable the wikillm systemd units. Requires sudo.
# Replaces the fragile `tmux new-session` setup. After this runs, the bot and
# the Drive mount survive Pi reboots.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

if [ "$EUID" -ne 0 ]; then
  echo "error: this script must run as root. Try: sudo $0" >&2
  exit 1
fi

# Stop any existing tmux bot session so the systemd unit doesn't race it.
sudo -u miraddo tmux kill-session -t wikillm-bot 2>/dev/null || true
sleep 1

# Copy unit files into place
install -m 0644 "$HERE/rclone-gdrive.service" /etc/systemd/system/rclone-gdrive.service
install -m 0644 "$HERE/wikillm-bot.service"   /etc/systemd/system/wikillm-bot.service

systemctl daemon-reload
systemctl enable --now rclone-gdrive.service
sleep 3
systemctl enable --now wikillm-bot.service

echo
echo "--- status ---"
systemctl --no-pager status rclone-gdrive.service | head -8
echo
systemctl --no-pager status wikillm-bot.service | head -10
echo
echo "Done. Both units now auto-start on reboot. To watch the bot:"
echo "  journalctl -u wikillm-bot -f"
echo "or tail -f /home/miraddo/.openclaw/workspace/wikillm/bot.log"
