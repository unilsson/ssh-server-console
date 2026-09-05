#!/usr/bin/env bash
set -euo pipefail

rm -f "$HOME/.local/bin/ssh-server-console"
rm -rf "$HOME/.local/share/ssh-server-console"
rm -f "$HOME/.local/share/applications/se.haninge.SSHServerConsole.desktop"
echo "SSH-serverkonsol har avinstallerats. Din ~/.ssh-konfiguration är orörd."
