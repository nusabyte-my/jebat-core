#!/usr/bin/env bash
   set -u

   log() {
     printf '\n==> %s\n' "$1"
   }

   warn() {
     printf '\n[warn] %s\n' "$1"
   }

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

link_or_copy_file() {
  local src="$1"
  local dest="$2"
  mkdir -p "$(dirname "$dest")"

  if have_cmd ln; then
    ln -sf "$src" "$dest" || cp -f "$src" "$dest"
  else
    cp -f "$src" "$dest"
  fi
}

install_if_available() {
     local pkg
     local to_install=()
     for pkg in "$@"; do
       if dnf5 repoquery --available "$pkg" >/dev/null 2>&1 || dnf5 repoquery "$pkg"
 >/dev/null 2>&1; then
         to_install+=("$pkg")
       else
         warn "Skipping unavailable package: $pkg"
       fi
     done

     if [ "${#to_install[@]}" -gt 0 ]; then
       sudo dnf5 install -y "${to_install[@]}"
     fi
   }

   log "Updating system"
   sudo dnf5 upgrade -y || warn "System upgrade had issues; continuing"

   log "Installing base plugin support"
   sudo dnf5 install -y dnf5-plugins || warn "dnf5-plugins install failed"

   log "Adding Opera repository"
   sudo rpm --import https://rpm.opera.com/rpmrepo.key || warn "Opera GPG import failed
 or already present"
   sudo dnf5 config-manager addrepo
 --from-repofile=https://rpm.opera.com/rpm/opera-stable.repo || warn "Opera repo may
 already exist or config-manager unavailable"

   log "Installing core desktop tools"
   install_if_available \
     alacritty \
     fish \
     opera-stable \
     git \
     curl \
     wget \
     unzip \
     zip \
     tar \
     btop \
     htop \
     fastfetch \
     neovim \
     tmux \
     wl-clipboard \
     xclip

   log "Installing development stack"
   install_if_available \
     nodejs \
     npm \
     python3 \
     python3-pip \
     python3-virtualenv \
     gcc \
     gcc-c++ \
     make \
     cmake \
     go \
     java-21-openjdk \
     php \
     composer \
     sqlite \
     mariadb \
     postgresql

   log "Installing containers and virtualization support"
   install_if_available \
     podman \
     distrobox \
     docker \
     docker-compose \
     virt-manager \
     qemu-kvm \
     libvirt \
     virt-install \
     bridge-utils

   log "Enabling services where present"
   if systemctl list-unit-files | grep -q '^docker\.service'; then
     sudo systemctl enable --now docker || warn "Could not enable docker"
   else
     warn "docker.service not found"
   fi

   if systemctl list-unit-files | grep -q '^libvirtd\.service'; then
     sudo systemctl enable --now libvirtd || warn "Could not enable libvirtd"
   else
     warn "libvirtd.service not found"
   fi

   log "Adding current user to useful groups"
   sudo usermod -aG docker "$USER" 2>/dev/null || warn "Could not add $USER to docker
 group"
   sudo usermod -aG libvirt "$USER" 2>/dev/null || warn "Could not add $USER to libvirt
 group"

   log "Installing database and productivity tools"
   install_if_available \
     dbeaver \
     sqlitebrowser \
     filezilla

   log "Installing pentest/security tools"
   install_if_available \
     nmap \
     wireshark \
     wireshark-cli \
     wireshark-qt \
     tcpdump \
     sqlmap \
     john \
     hashcat \
     hydra \
     nikto \
     masscan \
     whois \
     bind-utils \
     net-tools

   log "Installing content creation tools"
   install_if_available \
     obs-studio \
     gimp \
     inkscape \
     kdenlive

   log "Installing Ollama if missing"
   if have_cmd ollama; then
     warn "Ollama already installed"
   else
     curl -fsSL https://ollama.com/install.sh | sh || warn "Ollama install failed"
   fi

   log "Setting Fish as default shell if installed"
   if have_cmd fish; then
     chsh -s "$(command -v fish)" "$USER" || warn "Could not change shell
 automatically"
   else
     warn "fish not installed"
   fi

log "Setting Opera as default browser if installed"
if [ -f /usr/share/applications/opera.desktop ] || [ -f
 /var/lib/flatpak/exports/share/applications/opera.desktop ]; then
  xdg-settings set default-web-browser opera.desktop || warn "Could not set Opera as
 default browser automatically"
else
  warn "opera.desktop not found"
fi

log "Provisioning Alacritty config"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALACRITTY_SOURCE="$SCRIPT_DIR/config/alacritty/alacritty.toml"
ALACRITTY_TARGET="$HOME/.config/alacritty/alacritty.toml"

if [ -f "$ALACRITTY_SOURCE" ]; then
  link_or_copy_file "$ALACRITTY_SOURCE" "$ALACRITTY_TARGET"
else
  warn "Tracked Alacritty config not found at $ALACRITTY_SOURCE"
fi

log "Creating common distroboxes if distrobox is installed"
if have_cmd distrobox; then
     distrobox create --name archbox --image archlinux:latest || warn "archbox create
 skipped/failed"
     distrobox create --name debsec --image debian:stable || warn "debsec create
 skipped/failed"
     distrobox create --name nodebox --image docker.io/library/node:22 || warn "nodebox
 create skipped/failed"
     distrobox create --name pybox --image docker.io/library/python:3.12 || warn "pybox
 create skipped/failed"
   else
     warn "distrobox not installed"
   fi

   log "Summary"
   echo "Done."
   echo
   echo "Recommended next commands:"
   echo " ollama pull qwen2.5-coder:7b"
   echo " ollama pull llama3:8b"
   echo " ollama pull hermes-sec-v2:latest  # alias: jebat-security"
   echo
   echo "Recommended manual checks:"
   echo " 1. Log out and log back in for shell/group changes"
   echo " 2. KDE System Settings -> Default Applications"
   echo " - Web Browser: Opera"
   echo " - Terminal Emulator: Alacritty"
   echo " 3. Verify current shell with: echo \$SHELL"
   echo " 4. Verify desktop with: echo \$XDG_CURRENT_DESKTOP"
