# Operator Terminal Stack

## Profiles

### Default tracked profile
- `config/alacritty/alacritty.toml`
- balanced operator terminal
- good for general shell and development work

### Red-team profile
- `config/alacritty/alacritty-redteam.toml`
- hotter red/pink accents
- auto-enters tmux session: `redteam`
- exports:
  - `OPERATOR_PROFILE=redteam`
  - `ALACRITTY_TITLE=REDTEAM-OPS`

### Blue-team profile
- `config/alacritty/alacritty-blueteam.toml`
- cooler blue/cyan accents
- auto-enters tmux session: `blueteam`
- exports:
  - `OPERATOR_PROFILE=blueteam`
  - `ALACRITTY_TITLE=BLUETEAM-OPS`

## Desktop launchers

Tracked launchers:
- `config/applications/alacritty-jebat.desktop`
- `config/applications/alacritty-redteam.desktop`
- `config/applications/alacritty-blueteam.desktop`

Install locally:

```bash
mkdir -p ~/.local/share/applications
cp -f config/applications/alacritty-*.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications 2>/dev/null || true
```

## Apply a profile

```bash
cp -f config/alacritty/alacritty-redteam.toml ~/.config/alacritty/alacritty.toml
# or
cp -f config/alacritty/alacritty-blueteam.toml ~/.config/alacritty/alacritty.toml
# or
cp -f config/alacritty/alacritty.toml ~/.config/alacritty/alacritty.toml
```

Fish helpers:

```fish
use-redteam
use-blueteam
use-defaultterm
op-profile
```

## Engagement-aware helpers

Tracked fish config:
- `config/fish/conf.d/operator-engagement-title.fish`

Commands:
- `engagement-name`
- `title-engagement`
- `tmux-rename-engagement`
- `ops-context`

## tmux layouts

Tracked fish config:
- `config/fish/conf.d/operator-tmux-layouts.fish`

Commands:
- `tmux-redteam-layout`
- `tmux-blueteam-layout`
- `tmux-ops-layout`

## Alacritty workflow changes

Added:
- more scrollback
- clipboard-friendly behavior
- search and vi mode shortcuts
- font resize shortcuts
- new window shortcut
- page scroll shortcuts
- profile-aware startup env

Keybinds:
- `Ctrl+Shift+C` copy
- `Ctrl+Shift+V` paste
- `Ctrl+Shift+F` search forward
- `Ctrl+Shift+B` search backward
- `Ctrl+Shift+Space` toggle vi mode
- `Ctrl+Shift+N` new window
- `Ctrl+Shift+L` clear screen
- `Ctrl+-` decrease font
- `Ctrl+=` increase font
- `Ctrl+0` reset font
- `Shift+PageUp/PageDown` page scroll
- `Shift+Home/End` jump top/bottom (default profile)

## Suggested usage

- Use default profile for normal work
- Use red-team profile for offensive/pentest sessions
- Use blue-team profile for monitoring, triage, and investigation
- Start a fresh Alacritty window after profile changes to enter the intended tmux session cleanly
- Use engagement-aware title helpers inside active engagement folders
