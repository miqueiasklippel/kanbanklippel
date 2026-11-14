#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(realpath "$0")")"

APP_ID=io.github.miqueiasklippel.KanbanKlippel
VERSION=1.0.0

flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user -y --noninteractive flathub org.gnome.Sdk//50 org.gnome.Platform//50 org.flatpak.Builder

flatpak run org.flatpak.Builder --user --force-clean --repo=repo --install-deps-from=flathub build "$APP_ID.yml"
flatpak build-bundle repo "kanban-klippel-$VERSION.flatpak" "$APP_ID" --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo

if [[ "${1:-}" == "--install" ]]; then
  flatpak install --user -y --reinstall "kanban-klippel-$VERSION.flatpak"
fi

echo "kanban-klippel-$VERSION.flatpak"
