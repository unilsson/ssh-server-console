#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
app_dir="$HOME/.local/share/ssh-server-console"
launcher="$HOME/.local/bin/ssh-server-console"

sudo apt update
sudo apt install -y python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91 openssh-client python3-venv

python3 -m venv --system-site-packages "$app_dir/venv"
"$app_dir/venv/bin/python" -m pip install --upgrade --force-reinstall "$project_dir"
install -d "$HOME/.local/bin"
ln -sfn "$app_dir/venv/bin/ssh-server-console" "$launcher"

install -Dm644 \
  "$project_dir/data/se.haninge.SSHServerConsole.desktop" \
  "$HOME/.local/share/applications/se.haninge.SSHServerConsole.desktop"

echo "Installerat. Starta 'SSH-serverkonsol' från programmenyn eller kör:"
echo "  $launcher"
