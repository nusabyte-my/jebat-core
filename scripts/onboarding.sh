#!/bin/bash
#
# onboarding.sh - JEBATCore Enhanced 7-Phase Onboarding
# Guides users through complete first-time setup
#

set -e

# ─── Configuration ──────────────────────────────────────────────────
JEBATCORE_HOME="${JEBATCORE_HOME:-$HOME/.jebatcore}"
BUNDLE_DIR="$JEBATCORE_HOME/bundle"
CONFIG_FILE="$JEBATCORE_HOME/config.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# User data (defaults)
USER_NAME=""
USER_ROLE=""
USE_CASE=""
RESPONSE_STYLE=""
LANGUAGE="English"
CONFIRM_CHANGES="true"
USE_MEMORY="true"
GATEWAY_URL="http://localhost:18789"
DETECTED_IDES=()
SELECTED_IDES=()
INSTALL_MODE="both"

# ─── Utility Functions ──────────────────────────────────────────────
print_banner() {
  echo ""
  echo -e "${CYAN}${BOLD}╔════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}${BOLD}║${NC}  ${GREEN}⚔️  JEBATCore Onboarding${NC}                              ${CYAN}${BOLD}║${NC}"
  echo -e "${CYAN}${BOLD}║${NC}  ${YELLOW}The LLM Ecosystem That Remembers Everything${NC}          ${CYAN}${BOLD}║${NC}"
  echo -e "${CYAN}${BOLD}╚════════════════════════════════════════════════════════╝${NC}"
  echo ""
}

print_phase() {
  local num=$1
  local name=$2
  echo ""
  echo -e "${MAGENTA}${BOLD}━━━ Phase $num/7: $name ━━━${NC}"
  echo ""
}

print_success() {
  echo -e "${GREEN}${BOLD}✅ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
  echo -e "${RED}❌ $1${NC}"
}

print_info() {
  echo -e "${CYAN}ℹ️  $1${NC}"
}

print_progress() {
  echo -e "${BLUE}🔨 $1${NC}"
}

ask_yes_no() {
  local prompt=$1
  local default=$2  # "y" or "n"
  local response

  if [ "$default" = "y" ]; then
    prompt="$prompt [Y/n]: "
  else
    prompt="$prompt [y/N]: "
  fi

  read -rp "$prompt" response
  response=$(echo "$response" | tr '[:upper:]' '[:lower:]')

  if [ -z "$response" ]; then
    [ "$default" = "y" ] && return 0 || return 1
  fi

  [[ "$response" =~ ^(yes|y)$ ]]
}

ask_input() {
  local prompt=$1
  local default=$2
  local result

  if [ -n "$default" ]; then
    read -rp "$prompt [$default]: " result
  else
    read -rp "$prompt: " result
  fi

  echo "${result:-$default}"
}

ask_choice() {
  local prompt=$1
  shift
  local options=("$@")
  local i

  echo ""
  echo -e "${BOLD}$prompt${NC}"
  for i in "${!options[@]}"; do
    echo -e "  ${GREEN}$((i+1))${NC}) ${options[$i]}"
  done
  echo ""

  local choice
  read -rp "Choose (1-${#options[@]}): " choice

  if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#options[@]}" ]; then
    echo "${options[$((choice-1))]}"
  else
    echo "${options[0]}"
  fi
}

# ─── Phase 1: Welcome ──────────────────────────────────────────────
phase1_welcome() {
  print_banner

  echo -e "${BOLD}Welcome, warrior!${NC} This guided setup will configure your JEBATCore experience."
  echo ""
  echo "What we'll do:"
  echo -e "  ${GREEN}✅${NC} Verify your installation"
  echo -e "  ${GREEN}✅${NC} Detect your IDEs"
  echo -e "  ${GREEN}✅${NC} Install JEBATCore to your IDE(s)"
  echo -e "  ${GREEN}✅${NC} Personalize your configuration"
  echo -e "  ${GREEN}✅${NC} Test everything works"
  echo ""
  echo -e "${CYAN}Estimated time:${NC} 2-3 minutes"
  echo ""

  read -rp "Press Enter to begin..."

  # Collect user name
  USER_NAME=$(ask_input "What's your name or handle?" "")
  if [ -z "$USER_NAME" ]; then
    USER_NAME="Warrior"
  fi

  # Collect user role
  USER_ROLE=$(ask_choice "What's your primary role?" \
    "Developer" "Founder/CEO" "Designer" "Security Engineer" "DevOps" "Researcher" "Other")

  echo ""
  print_success "Welcome, $USER_NAME! Let's get you set up."
}

# ─── Phase 2: Environment Verification ──────────────────────────────
phase2_verify() {
  print_phase 2 "Environment Verification"

  local errors=0
  local warnings=0

  # Check Node.js
  print_progress "Checking prerequisites..."

  if command -v node &> /dev/null; then
    local node_version
    node_version=$(node --version)
    print_success "Node.js $node_version"
  else
    print_error "Node.js not found (required)"
    errors=$((errors+1))
  fi

  # Check npm/yarn/bun
  if command -v npm &> /dev/null; then
    print_success "npm $(npm --version)"
  elif command -v yarn &> /dev/null; then
    print_success "yarn $(yarn --version)"
  elif command -v bun &> /dev/null; then
    print_success "bun $(bun --version)"
  else
    print_warning "No package manager detected (npm/yarn/bun)"
    warnings=$((warnings+1))
  fi

  # Check JEBATCORE_HOME
  echo ""
  print_progress "Checking JEBATCore installation..."

  if [ -d "$JEBATCORE_HOME" ]; then
    print_success "JEBATCORE_HOME: $JEBATCORE_HOME"
  else
    print_warning "JEBATCORE_HOME not found: $JEBATCORE_HOME"
    warnings=$((warnings+1))
  fi

  # Check bundle directory
  if [ -d "$BUNDLE_DIR" ]; then
    print_success "Bundle directory exists"
  else
    print_error "Bundle directory missing: $BUNDLE_DIR"
    errors=$((errors+1))
  fi

  # Check 7 core MD files
  echo ""
  print_progress "Checking identity files..."

  local required_files=(
    "AGENTS.md"
    "IDENTITY.md"
    "MEMORY.md"
    "ORCHESTRA.md"
    "SOUL.md"
    "TOOLS.md"
    "USER.md"
  )

  local missing_files=()

  for file in "${required_files[@]}"; do
    if [ -f "$BUNDLE_DIR/$file" ]; then
      local size
      size=$(wc -c < "$BUNDLE_DIR/$file")
      if command -v numfmt &> /dev/null; then
        print_success "$file ($(numfmt --to=iec $size))"
      else
        print_success "$file ($size bytes)"
      fi
    else
      print_error "$file MISSING"
      missing_files+=("$file")
      errors=$((errors+1))
    fi
  done

  # Check supporting directories
  echo ""
  print_progress "Checking resources..."

  if [ -d "$BUNDLE_DIR/adapters" ]; then
    local adapter_count
    adapter_count=$(find "$BUNDLE_DIR/adapters" -type f 2>/dev/null | wc -l)
    print_success "Adapters ($adapter_count files)"
  else
    print_warning "Adapters directory missing"
    warnings=$((warnings+1))
  fi

  if [ -d "$BUNDLE_DIR/vault" ]; then
    local vault_count
    vault_count=$(find "$BUNDLE_DIR/vault" -type f 2>/dev/null | wc -l)
    print_success "Vault ($vault_count files)"
  else
    print_warning "Vault directory missing"
    warnings=$((warnings+1))
  fi

  if [ -d "$BUNDLE_DIR/skills" ]; then
    local skill_count
    skill_count=$(ls -1 "$BUNDLE_DIR/skills" 2>/dev/null | wc -l)
    print_success "Skills ($skill_count available)"
  else
    print_warning "Skills directory missing"
    warnings=$((warnings+1))
  fi

  # Summary
  echo ""
  if [ $errors -eq 0 ]; then
    print_success "All verifications passed!"
    return 0
  else
    print_error "$errors error(s), $warnings warning(s) found"

    # Attempt auto-repair
    echo ""
    if ask_yes_no "Attempt automatic repair?" "y"; then
      if auto_repair_bundle; then
        print_success "Repair successful! Re-running verification..."
        echo ""
        # Re-run this phase
        phase2_verify
        return $?
      else
        print_error "Repair failed. Please fix manually and re-run onboarding."
        echo ""
        echo -e "${BOLD}Manual fix steps:${NC}"
        echo "  1. Reinstall JEBATCore: npm install -g jebatcore"
        echo "  2. Run installation: jebatcore install"
        echo "  3. Re-run onboarding: bash scripts/onboarding.sh"
        echo ""
        echo "Still having issues? Report here:"
        echo -e "${CYAN}https://github.com/nusabyte-my/jebat-core/issues${NC}"
        echo ""
        exit 1
      fi
    else
      print_warning "Skipping repair. Some features may not work correctly."
      return 1
    fi
  fi
}

auto_repair_bundle() {
  print_progress "Attempting automatic repair..."
  echo ""

  # Strategy 1: Rebuild from source (if dev setup)
  if [ -f "$SCRIPT_DIR/../build-cli-bundle.sh" ]; then
    print_progress "Rebuilding bundle from source..."
    if bash "$SCRIPT_DIR/../build-cli-bundle.sh" 2>&1 | tail -5; then
      return 0
    fi
  fi

  # Strategy 2: Check if we're in the main repo
  if [ -f "$SCRIPT_DIR/../../scripts/build-cli-bundle.sh" ]; then
    print_progress "Rebuilding from repository..."
    if bash "$SCRIPT_DIR/../../scripts/build-cli-bundle.sh" 2>&1 | tail -5; then
      return 0
    fi
  fi

  # Strategy 3: Re-copy from CLI package
  if [ -d "$CLI_DIR" ] && [ -f "$CLI_DIR/AGENTS.md" ]; then
    print_progress "Re-copying from CLI package..."
    mkdir -p "$BUNDLE_DIR"
    for file in AGENTS.md IDENTITY.md MEMORY.md ORCHESTRA.md SOUL.md TOOLS.md USER.md; do
      if [ -f "$CLI_DIR/$file" ]; then
        cp "$CLI_DIR/$file" "$BUNDLE_DIR/$file"
        print_success "  Restored $file"
      fi
    done

    # Copy directories
    for dir in adapters vault skills; do
      if [ -d "$CLI_DIR/$dir" ]; then
        cp -r "$CLI_DIR/$dir" "$BUNDLE_DIR/$dir"
        print_success "  Restored $dir/"
      fi
    done
    return 0
  fi

  # All strategies failed
  return 1
}

# ─── Phase 3: IDE Detection ────────────────────────────────────────
phase3_detect_ides() {
  print_phase 3 "IDE Detection"

  print_progress "Scanning for IDEs..."

  DETECTED_IDES=()

  # VS Code
  if command -v code &> /dev/null; then
    local vscode_version
    vscode_version=$(code --version 2>/dev/null | head -1 || echo "unknown")
    DETECTED_IDES+=("vscode:VS Code:$vscode_version")
    print_success "VS Code detected ($vscode_version)"
  elif [ -d "$HOME/.vscode/extensions" ]; then
    DETECTED_IDES+=("vscode:VS Code:installed")
    print_success "VS Code detected (via extensions)"
  fi

  # Cursor
  if command -v cursor &> /dev/null; then
    local cursor_version
    cursor_version=$(cursor --version 2>/dev/null || echo "unknown")
    DETECTED_IDES+=("cursor:Cursor:$cursor_version")
    print_success "Cursor detected ($cursor_version)"
  elif [ -d "$HOME/.cursor" ]; then
    DETECTED_IDES+=("cursor:Cursor:installed")
    print_success "Cursor detected (via config)"
  fi

  # Zed
  if command -v zed &> /dev/null; then
    local zed_version
    zed_version=$(zed --version 2>/dev/null || echo "unknown")
    DETECTED_IDES+=("zed:Zed:$zed_version")
    print_success "Zed detected ($zed_version)"
  elif [ -d "$HOME/.config/zed" ]; then
    DETECTED_IDES+=("zed:Zed:installed")
    print_success "Zed detected (via config)"
  fi

  # JetBrains
  if command -v idea &> /dev/null || command -v webstorm &> /dev/null || command -v pycharm &> /dev/null; then
    DETECTED_IDES+=("jetbrains:JetBrains:installed")
    print_success "JetBrains IDE detected"
  fi

  # Windsurf
  if command -v windsurf &> /dev/null; then
    DETECTED_IDES+=("windsurf:Windsurf:installed")
    print_success "Windsurf detected"
  fi

  # Neovim
  if command -v nvim &> /dev/null; then
    DETECTED_IDES+=("neovim:Neovim:installed")
    print_success "Neovim detected"
  fi

  # Summary
  echo ""
  if [ ${#DETECTED_IDES[@]} -eq 0 ]; then
    print_warning "No IDEs detected"
    print_info "You can still install JEBATCore in workstation mode"
  else
    print_success "Found ${#DETECTED_IDES[@]} IDE(s)"
  fi
}

# ─── Phase 4: Installation ──────────────────────────────────────────
phase4_install() {
  print_phase 4 "Installation"

  # Check if already installed
  if [ -d "$JEBATCORE_HOME/ide-snippets" ]; then
    local existing_ides
    existing_ides=$(ls -1 "$JEBATCORE_HOME/ide-snippets" 2>/dev/null | tr '\n' ', ' | sed 's/,$//')
    print_warning "JEBATCore appears to be already installed to: $existing_ides"
    echo ""

    if ask_yes_no "Re-install?" "n"; then
      echo "Proceeding with fresh installation..."
    else
      print_info "Skipping installation. You can always run 'jebatcore install' later."
      return 0
    fi
  fi

  # Select IDEs
  echo ""
  if [ ${#DETECTED_IDES[@]} -gt 0 ]; then
    print_progress "Select IDE(s) to install to:"
    echo ""

    local ide_names=()
    local ide_keys=()

    for ide_entry in "${DETECTED_IDES[@]}"; do
      IFS=':' read -r key name version <<< "$ide_entry"
      ide_names+=("$name")
      ide_keys+=("$key")
    done

    echo "Detected IDEs:"
    for i in "${!ide_names[@]}"; do
      echo -e "  ${GREEN}$((i+1))${NC}) ${ide_names[$i]}"
    done
    echo -e "  ${GREEN}a${NC}) All detected IDEs"
    echo ""

    local choice
    read -rp "Select IDE(s) to install to (comma-separated numbers, or 'a' for all): " choice

    if [ "$choice" = "a" ] || [ "$choice" = "A" ]; then
      SELECTED_IDES=("${ide_keys[@]}")
    else
      SELECTED_IDES=()
      IFS=',' read -ra choices <<< "$choice"
      for c in "${choices[@]}"; do
        c=$(echo "$c" | tr -d ' ')
        if [[ "$c" =~ ^[0-9]+$ ]] && [ "$c" -ge 1 ] && [ "$c" -le "${#ide_keys[@]}" ]; then
          SELECTED_IDES+=("${ide_keys[$((c-1))]}")
        fi
      done
    fi
  else
    print_warning "No IDEs detected. Installing in workstation mode only."
    SELECTED_IDES=()
  fi

  if [ ${#SELECTED_IDES[@]} -eq 0 ]; then
    print_warning "No IDEs selected. Installation will create bundle only."
    print_info "You can run 'jebatcore install' later to add IDE integration."
    return 0
  fi

  # Choose install mode
  echo ""
  INSTALL_MODE=$(ask_choice "Install mode for ${SELECTED_IDES[*]}?" \
    "both (extension + MCP)" "extension only" "MCP only")

  # Map to CLI format
  case "$INSTALL_MODE" in
    *"both"*) INSTALL_MODE="both" ;;
    *"extension"*) INSTALL_MODE="extension" ;;
    *"MCP"*) INSTALL_MODE="mcp" ;;
    *) INSTALL_MODE="both" ;;
  esac

  # Confirm
  echo ""
  echo -e "${BOLD}Installation Summary:${NC}"
  echo -e "  ${CYAN}IDEs:${NC} ${SELECTED_IDES[*]}"
  echo -e "  ${CYAN}Mode:${NC} $INSTALL_MODE"
  echo -e "  ${CYAN}Scope:${NC} workstation"
  echo -e "  ${CYAN}Location:${NC} $JEBATCORE_HOME"
  echo ""

  if ask_yes_no "Proceed with installation?" "y"; then
    echo ""
    print_progress "Installing JEBATCore..."
    echo ""

    # Build IDE list for CLI
    local ide_list
    ide_list=$(IFS=,; echo "${SELECTED_IDES[*]}")

    # Run the installer
    local install_cmd="node \"$CLI_DIR/bin/jebatcore.js\" install --ide $ide_list --mode $INSTALL_MODE --scope workstation --home \"$JEBATCORE_HOME\" --yes"

    echo -e "${BLUE}Running:${NC} $install_cmd"
    echo ""

    if eval "$install_cmd"; then
      print_success "Installation completed!"
    else
      print_error "Installation failed. Check the output above for details."
      return 1
    fi
  else
    print_info "Installation cancelled. You can run it manually later:"
    echo -e "  ${BOLD}jebatcore install --ide ${SELECTED_IDES[*]} --mode $INSTALL_MODE${NC}"
  fi
}

# ─── Phase 5: Configuration ────────────────────────────────────────
phase5_configure() {
  print_phase 5 "Configuration"

  print_progress "Let's personalize your JEBATCore experience..."
  echo ""

  # Primary use case
  USE_CASE=$(ask_choice "What's your primary use case for JEBATCore?" \
    "Coding & development" "Research & analysis" "Security review" \
    "Operations & deployment" "Content & growth" "All of the above")

  # Response style
  RESPONSE_STYLE=$(ask_choice "Preferred response style?" \
    "direct — short answers, no filler" \
    "detailed — thorough explanations" \
    "balanced — concise but complete")

  # Language
  LANGUAGE=$(ask_input "Preferred language" "English")

  # Confirm before changes
  if ask_yes_no "Confirm before making changes to files?" "y"; then
    CONFIRM_CHANGES="true"
  else
    CONFIRM_CHANGES="false"
  fi

  # Enable memory
  if ask_yes_no "Enable persistent memory (JEBAT remembers past work)?" "y"; then
    USE_MEMORY="true"
  else
    USE_MEMORY="false"
  fi

  # Gateway URL
  echo ""
  GATEWAY_URL=$(ask_input "Gateway URL" "$GATEWAY_URL")

  # Save configuration
  echo ""
  print_progress "Saving configuration..."

  mkdir -p "$JEBATCORE_HOME"

  cat > "$CONFIG_FILE" << EOF
{
  "userName": "$USER_NAME",
  "userRole": "$USER_ROLE",
  "useCase": "$USE_CASE",
  "responseStyle": "$RESPONSE_STYLE",
  "language": "$LANGUAGE",
  "confirmBeforeAction": $CONFIRM_CHANGES,
  "useMemory": $USE_MEMORY,
  "gatewayUrl": "$GATEWAY_URL",
  "onboardedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "version": "2.0.0"
}
EOF

  print_success "Configuration saved to $CONFIG_FILE"

  # Generate USER.md in bundle
  if [ -d "$BUNDLE_DIR" ]; then
    cat > "$BUNDLE_DIR/USER.md" << EOF
# USER.md — JEBATCore User Profile

**Name**: $USER_NAME
**Role**: $USER_ROLE
**Language**: $LANGUAGE

## Primary Use Case
$USE_CASE

## Working Style
- Response style: $RESPONSE_STYLE
- Confirm before changes: $CONFIRM_CHANGES
- Persistent memory: $USE_MEMORY

## Preferences
- JEBAT should be $RESPONSE_STYLE
- Gateway: $GATEWAY_URL
EOF
    print_success "USER.md updated with your preferences"
  fi
}

# ─── Phase 6: Testing ──────────────────────────────────────────────
phase6_test() {
  print_phase 6 "Testing Setup"

  local test_errors=0

  print_progress "Running verification tests..."
  echo ""

  # Test 1: Bundle files
  print_progress "Test 1/6: Bundle integrity..."
  local bundle_ok=true
  for file in AGENTS.md IDENTITY.md MEMORY.md ORCHESTRA.md SOUL.md TOOLS.md USER.md; do
    if [ ! -f "$BUNDLE_DIR/$file" ]; then
      print_error "$file missing"
      bundle_ok=false
      test_errors=$((test_errors+1))
    fi
  done
  if [ "$bundle_ok" = true ]; then
    print_success "All 7 identity files present"
  fi

  # Test 2: IDE snippets
  echo ""
  print_progress "Test 2/6: IDE snippets..."
  if [ -d "$JEBATCORE_HOME/ide-snippets" ]; then
    local snippet_count
    snippet_count=$(ls -1 "$JEBATCORE_HOME/ide-snippets" 2>/dev/null | wc -l)
    print_success "IDE snippets generated ($snippet_count IDEs)"
  else
    print_warning "No IDE snippets (workstation-only mode)"
  fi

  # Test 3: MCP server
  echo ""
  print_progress "Test 3/6: MCP server..."
  if [ -f "$JEBATCORE_HOME/server/mcp-server.js" ]; then
    print_success "MCP server installed"
  else
    print_warning "MCP server not found"
  fi

  # Test 4: Config file
  echo ""
  print_progress "Test 4/6: Configuration..."
  if [ -f "$CONFIG_FILE" ]; then
    print_success "Config file created ($CONFIG_FILE)"
  else
    print_warning "Config file missing"
  fi

  # Test 5: File access
  echo ""
  print_progress "Test 5/6: File access..."
  if [ -r "$BUNDLE_DIR/AGENTS.md" ]; then
    local first_line
    first_line=$(head -1 "$BUNDLE_DIR/AGENTS.md")
    if [ -n "$first_line" ]; then
      print_success "File access test passed"
    else
      print_error "AGENTS.md appears to be empty"
      test_errors=$((test_errors+1))
    fi
  else
    print_error "Cannot read AGENTS.md"
    test_errors=$((test_errors+1))
  fi

  # Test 6: CLI health check
  echo ""
  print_progress "Test 6/6: CLI health check..."
  if command -v jebatcore &> /dev/null; then
    if jebatcore doctor > /dev/null 2>&1; then
      print_success "Health check passed"
    else
      print_warning "Health check returned non-zero (may need gateway)"
    fi
  else
    print_info "CLI not in PATH, skipping health check"
  fi

  # Summary
  echo ""
  if [ $test_errors -eq 0 ]; then
    print_success "All tests passed!"
    return 0
  else
    print_error "$test_errors test(s) failed"
    return 1
  fi
}

# ─── Phase 7: Completion ───────────────────────────────────────────
phase7_complete() {
  echo ""
  echo -e "${CYAN}${BOLD}╔════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}${BOLD}║${NC}  ${GREEN}🎉 Onboarding Complete!${NC}                              ${CYAN}${BOLD}║${NC}"
  echo -e "${CYAN}${BOLD}║${NC}  ${YELLOW}JEBATCore is ready for action!${NC}                      ${CYAN}${BOLD}║${NC}"
  echo -e "${CYAN}${BOLD}╚════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # Show setup summary
  echo -e "${BOLD}📊 Your Setup:${NC}"

  local identity_count=0
  for file in AGENTS.md IDENTITY.md MEMORY.md ORCHESTRA.md SOUL.md TOOLS.md USER.md; do
    [ -f "$BUNDLE_DIR/$file" ] && identity_count=$((identity_count+1))
  done
  echo -e "  Identity Files: $identity_count/7 ✅"

  if [ -d "$JEBATCORE_HOME/ide-snippets" ]; then
    local ide_count
    ide_count=$(ls -1 "$JEBATCORE_HOME/ide-snippets" 2>/dev/null | wc -l)
    echo -e "  IDEs Configured: $ide_count ✅"
  else
    echo -e "  IDEs Configured: 0 (workstation mode)"
  fi

  if [ -f "$JEBATCORE_HOME/server/mcp-server.js" ]; then
    echo -e "  MCP Server: ✅"
  else
    echo -e "  MCP Server: ❌"
  fi

  if [ -d "$BUNDLE_DIR/skills" ]; then
    local skill_count
    skill_count=$(ls -1 "$BUNDLE_DIR/skills" 2>/dev/null | wc -l)
    echo -e "  Skills Available: $skill_count"
  fi

  echo -e "  Memory: $([ "$USE_MEMORY" = "true" ] && echo 'Enabled ✅' || echo 'Disabled ❌')"
  echo ""

  # Next steps
  echo -e "${BOLD}🚀 Next Steps:${NC}"
  echo ""
  if [ ${#SELECTED_IDES[@]} -gt 0 ]; then
    echo "  1. ${BOLD}Restart your IDE(s)${NC} to activate JEBATCore"
    echo "  2. Open a project and JEBAT will auto-load!"
    echo ""
  else
    echo "  1. Run ${BOLD}jebatcore install${NC} to add IDE integration"
    echo "  2. Restart your IDE after installation"
    echo ""
  fi

  echo -e "${BOLD}📚 What You Can Do:${NC}"
  echo ""
  echo "  jebatcore help          — View all commands"
  echo "  jebatcore doctor        — Health check"
  echo "  jebatcore skill-list    — Browse available skills"
  echo "  jebatcore status        — System status"
  echo "  jebatcore token-analyze — Optimize prompts"
  echo ""

  echo -e "${BOLD}💡 Pro Tips:${NC}"
  echo ""
  echo "  • Use --dry-run to preview changes"
  echo "  • Skills auto-activate based on context"
  echo "  • JEBAT remembers your preferences"
  echo "  • Check docs/ for detailed guides"
  echo "  • Set JEBATCORE_HOME to customize location"
  echo ""

  echo -e "${BOLD}🆘 Need Help?${NC}"
  echo ""
  echo "  • Documentation: https://github.com/nusabyte-my/jebat-core"
  echo "  • Issues: https://github.com/nusabyte-my/jebat-core/issues"
  echo ""

  echo -e "${GREEN}${BOLD}⚔️  Welcome to JEBAT, $USER_NAME! Let's build something epic.${NC}"
  echo ""
}

# ─── Main Flow ──────────────────────────────────────────────────────
main() {
  phase1_welcome
  phase2_verify
  phase3_detect_ides
  phase4_install
  phase5_configure
  phase6_test
  phase7_complete
}

main
