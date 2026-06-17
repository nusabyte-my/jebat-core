#!/usr/bin/env bash
#
# Rebrand Script: OpenClaw & Hermes → Jebat
# Created: 2026-04-12
# Usage: bash scripts/rebrand_to_jebat.sh [--dry-run] [--rollback]
#
# Options:
#   --dry-run    Show what would be changed without making changes
#   --rollback   Restore from backup
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$REPO_ROOT/backups/rebrand_$(date +%Y%m%d_%H%M%S)"
DRY_RUN=false
ROLLBACK=false
CHANGES_MADE=0
ERRORS=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            echo -e "${YELLOW}[DRY RUN MODE]${NC} No changes will be made."
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--dry-run] [--rollback]"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ERRORS=$((ERRORS + 1))
}

log_change() {
    echo -e "${GREEN}[CHANGE]${NC} $1"
    CHANGES_MADE=$((CHANGES_MADE + 1))
}

# Backup function
backup_file() {
    local file="$1"
    if [[ -f "$file" ]]; then
        local relative_path="${file#$REPO_ROOT/}"
        local backup_path="$BACKUP_DIR/$relative_path"
        local backup_parent
        backup_parent="$(dirname "$backup_path")"
        mkdir -p "$backup_parent"
        cp -p "$file" "$backup_path"
        log_info "Backed up: $relative_path"
    fi
}

# Rename function
rename_path() {
    local old_path="$1"
    local new_path="$2"
    local description="$3"

    if [[ ! -e "$old_path" ]]; then
        log_warn "$description: Source not found: $old_path"
        return 0
    fi

    if [[ -e "$new_path" ]]; then
        log_warn "$description: Target already exists: $new_path (skipping)"
        return 0
    fi

    if $DRY_RUN; then
        log_info "[DRY RUN] Would rename: $old_path → $new_path"
        return 0
    fi

    backup_file "$old_path"
    mv "$old_path" "$new_path"
    log_change "Renamed: $old_path → $new_path"
}

# Replace in file function
replace_in_file() {
    local file="$1"
    local old_string="$2"
    local new_string="$3"
    local description="$4"

    if [[ ! -f "$file" ]]; then
        log_warn "$description: File not found: $file"
        return 0
    fi

    if ! grep -qF "$old_string" "$file" 2>/dev/null; then
        log_info "$description: Pattern not found in $file (skipping)"
        return 0
    fi

    if $DRY_RUN; then
        log_info "[DRY RUN] Would replace in $file: $description"
        return 0
    fi

    # Use sed for replacement
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|$(echo "$old_string" | sed 's/[&/\]/\\&/g')|$(echo "$new_string" | sed 's/[&/\]/\\&/g')|g" "$file"
    else
        sed -i "s|$(echo "$old_string" | sed 's/[&/\]/\\&/g')|$(echo "$new_string" | sed 's/[&/\]/\\&/g')|g" "$file"
    fi
    
    log_change "Updated in $file: $description"
}

# Rollback function
do_rollback() {
    log_info "Starting rollback..."
    
    # Find the most recent backup directory
    local latest_backup
    latest_backup=$(find "$REPO_ROOT/backups" -maxdepth 1 -type d -name "rebrand_*" 2>/dev/null | sort -r | head -n 1)
    
    if [[ -z "$latest_backup" ]] || [[ ! -d "$latest_backup" ]]; then
        log_error "No backup found. Cannot rollback."
        exit 1
    fi
    
    log_info "Rolling back from: $latest_backup"
    
    # Restore files from backup
    find "$latest_backup" -type f | while read -r backup_file; do
        local relative_path="${backup_file#$latest_backup/}"
        local original_path="$REPO_ROOT/$relative_path"
        local original_dir
        original_dir="$(dirname "$original_path")"
        
        mkdir -p "$original_dir"
        cp -p "$backup_file" "$original_path"
        log_change "Restored: $relative_path"
    done
    
    log_success "Rollback complete!"
    exit 0
}

# Main migration
main() {
    if $ROLLBACK; then
        do_rollback
    fi

    log_info "========================================="
    log_info "Jebat Rebrand Migration Script"
    log_info "========================================="
    log_info "Repository: $REPO_ROOT"
    log_info "Backup directory: $BACKUP_DIR"
    log_info ""

    # Create backup directory
    if ! $DRY_RUN; then
        mkdir -p "$BACKUP_DIR"
    fi

    # ==========================================
    # PHASE 1: Directory & File Renames
    # ==========================================
    log_info "========================================="
    log_info "PHASE 1: Directory & File Renames"
    log_info "========================================="

    # Root level integrations
    rename_path \
        "$REPO_ROOT/integrations/openclaw" \
        "$REPO_ROOT/integrations/jebat-gateway" \
        "Integrations directory"

    if [[ -d "$REPO_ROOT/integrations/jebat-gateway" ]]; then
        rename_path \
            "$REPO_ROOT/integrations/jebat-gateway/openclaw.template.json" \
            "$REPO_ROOT/integrations/jebat-gateway/jebat-gateway.template.json" \
            "Gateway template config"

        rename_path \
            "$REPO_ROOT/integrations/jebat-gateway/workspace/skills/hermes-agent" \
            "$REPO_ROOT/integrations/jebat-gateway/workspace/skills/jebat-agent" \
            "Hermes agent skill directory"
    fi

    # jebat-core level integrations
    rename_path \
        "$REPO_ROOT/jebat-core/integrations/openclaw" \
        "$REPO_ROOT/jebat-core/integrations/jebat-gateway" \
        "Jebat-core integrations directory"

    if [[ -d "$REPO_ROOT/jebat-core/integrations/jebat-gateway" ]]; then
        rename_path \
            "$REPO_ROOT/jebat-core/integrations/jebat-gateway/openclaw.template.json" \
            "$REPO_ROOT/jebat-core/integrations/jebat-gateway/jebat-gateway.template.json" \
            "Jebat-core gateway template"

        rename_path \
            "$REPO_ROOT/jebat-core/integrations/jebat-gateway/workspace/skills/hermes-agent" \
            "$REPO_ROOT/jebat-core/integrations/jebat-gateway/workspace/skills/jebat-agent" \
            "Jebat-core Hermes agent skill"
    fi

    # Skill directories
    rename_path \
        "$REPO_ROOT/skills/hermes-agent" \
        "$REPO_ROOT/skills/jebat-agent" \
        "Root skills/hermes-agent"

    rename_path \
        "$REPO_ROOT/jebat-core/skills/hermes-agent" \
        "$REPO_ROOT/jebat-core/skills/jebat-agent" \
        "Jebat-core skills/hermes-agent"

    rename_path \
        "$REPO_ROOT/jebat-core/jebat-tokguru/skills/jebat-native/hermes-agent" \
        "$REPO_ROOT/jebat-core/jebat-tokguru/skills/jebat-native/jebat-agent" \
        "Jebat-tokguru hermes-agent"

    # Script renames
    rename_path \
        "$REPO_ROOT/scripts/export_openclaw_jebatcore.py" \
        "$REPO_ROOT/scripts/export_jebat_gateway.py" \
        "Export script"

    rename_path \
        "$REPO_ROOT/jebat-core/scripts/export_openclaw_jebatcore.py" \
        "$REPO_ROOT/jebat-core/scripts/export_jebat_gateway.py" \
        "Jebat-core export script"

    rename_path \
        "$REPO_ROOT/config/fish/conf.d/openclaw-grok-tools.fish" \
        "$REPO_ROOT/config/fish/conf.d/jebat-gateway-grok-tools.fish" \
        "Fish shell config"

    # Documentation renames
    rename_path \
        "$REPO_ROOT/brain/concepts/OpenClaw-Adaptation.md" \
        "$REPO_ROOT/brain/concepts/Jebat-Gateway-Adaptation.md" \
        "OpenClaw Adaptation concept"

    rename_path \
        "$REPO_ROOT/brain/concepts/Hermes.md" \
        "$REPO_ROOT/brain/concepts/Jebat-Agent.md" \
        "Hermes concept"

    rename_path \
        "$REPO_ROOT/core/HERMES.md" \
        "$REPO_ROOT/core/JEBAT_AGENT.md" \
        "HERMES core doc"

    rename_path \
        "$REPO_ROOT/AWESOME_OPENCLAW_SHORTLIST.md" \
        "$REPO_ROOT/AWESOME_JEBAT_GATEWAY_SHORTLIST.md" \
        "Awesome OpenClaw shortlist"

    rename_path \
        "$REPO_ROOT/OPENCLAW_ADAPTATION_MAP.md" \
        "$REPO_ROOT/JEBAT_GATEWAY_ADAPTATION_MAP.md" \
        "OpenClaw adaptation map"

    rename_path \
        "$REPO_ROOT/docs/OPENCLAW_JEBATCORE_INTEGRATION.md" \
        "$REPO_ROOT/docs/JEBAT_GATEWAY_INTEGRATION.md" \
        "OpenClaw integration doc"

    rename_path \
        "$REPO_ROOT/docs/VSCODE_JEBAT_HERMES_PROJECT_START.md" \
        "$REPO_ROOT/docs/VSCODE_JEBAT_AGENT_PROJECT_START.md" \
        "VSCode Hermes project start"

    rename_path \
        "$REPO_ROOT/jebat-core/docs/OPENCLAW_JEBATCORE_INTEGRATION.md" \
        "$REPO_ROOT/jebat-core/docs/JEBAT_GATEWAY_INTEGRATION.md" \
        "Jebat-core OpenClaw integration doc"

    rename_path \
        "$REPO_ROOT/jebat-core/docs/VSCODE_JEBAT_HERMES_PROJECT_START.md" \
        "$REPO_ROOT/jebat-core/docs/VSCODE_JEBAT_AGENT_PROJECT_START.md" \
        "Jebat-core VSCode Hermes project start"

    # ==========================================
    # PHASE 2: Configuration Files
    # ==========================================
    log_info ""
    log_info "========================================="
    log_info "PHASE 2: Configuration Files"
    log_info "========================================="

    local gateway_template="$REPO_ROOT/integrations/jebat-gateway/jebat-gateway.template.json"
    local gateway_template_core="$REPO_ROOT/jebat-core/integrations/jebat-gateway/jebat-gateway.template.json"

    for template in "$gateway_template" "$gateway_template_core"; do
        if [[ -f "$template" ]]; then
            replace_in_file "$template" '${OPENCLAW_GATEWAY_TOKEN}' '${JEBAT_GATEWAY_TOKEN}' "Gateway token env var"
            replace_in_file "$template" '~/.openclaw/extensions/builtin-channel-telegram' '~/.jebat/extensions/builtin-channel-telegram' "Extension install path"
            replace_in_file "$template" '~/.openclaw/workspace' '~/.jebat/workspace' "Workspace path"
            replace_in_file "$template" '"hermes-agent"' '"jebat-agent"' "Skill reference"
            replace_in_file "$template" '"alias": "JEBAT Hermes"' '"alias": "Jebat Agent"' "Model alias"
        fi
    done

    # .env.example
    local env_example="$REPO_ROOT/integrations/jebat-gateway/.env.example"
    if [[ -f "$env_example" ]]; then
        replace_in_file "$env_example" 'OPENCLAW_GATEWAY_TOKEN=' 'JEBAT_GATEWAY_TOKEN=' "Gateway token env var name"
    fi

    # Fish shell config
    local fish_config="$REPO_ROOT/config/fish/conf.d/jebat-gateway-grok-tools.fish"
    if [[ -f "$fish_config" ]]; then
        replace_in_file "$fish_config" '# OpenClaw Grok helpers' '# Jebat Gateway Grok helpers' "Comment header"
        replace_in_file "$fish_config" 'OPENCLAW_PRIMARY_MODEL=' 'JEBAT_GATEWAY_PRIMARY_MODEL=' "Primary model env var"
        replace_in_file "$fish_config" 'function openclaw-grok-check' 'function jebat-gateway-grok-check' "Function name"
        replace_in_file "$fish_config" '$OPENCLAW_PRIMARY_MODEL' '$JEBAT_GATEWAY_PRIMARY_MODEL' "Env var reference"
    fi

    # ==========================================
    # PHASE 3: Python Source Files
    # ==========================================
    log_info ""
    log_info "========================================="
    log_info "PHASE 3: Python Source Files"
    log_info "========================================="

    local webui_files=(
        "$REPO_ROOT/apps/api/services/webui/webui_server.py"
        "$REPO_ROOT/jebat-core/jebat/services/webui/webui_server.py"
    )

    for webui in "${webui_files[@]}"; do
        if [[ -f "$webui" ]]; then
            log_info "Processing: $webui"
            replace_in_file "$webui" 'integrations/openclaw/openclaw.template.json' 'integrations/jebat-gateway/jebat-gateway.template.json' "Template path"
            replace_in_file "$webui" 'skills/hermes-agent/SKILL.md' 'skills/jebat-agent/SKILL.md' "Skill path"
            replace_in_file "$webui" '{"cli", "openclaw", "vscode"}' '{"cli", "jebat-gateway", "vscode"}' "Workstation types"
            replace_in_file "$webui" '"openclaw"' '"jebat-gateway"' "Dictionary key"
            replace_in_file "$webui" 'openclaw_data' 'jebat_gateway_data' "Data variable"
            replace_in_file "$webui" '"OpenClaw"' '"Jebat Gateway"' "Workstation name"
            replace_in_file "$webui" 'openclaw_excerpt' 'jebat_gateway_excerpt' "Excerpt key"
            replace_in_file "$webui" '{"id": "openclaw", "label": "OpenClaw"' '{"id": "jebat-gateway", "label": "Jebat Gateway"' "Surface ID/label"
            replace_in_file "$webui" '"Hermes x OpenClaw"' '"Jebat Agent × Jebat Gateway"' "UI branding"
            replace_in_file "$webui" '<span>hermes</span><span>openclaw</span>' '<span>jebat-agent</span><span>jebat-gateway</span>' "Tag spans"
            replace_in_file "$webui" "{id:'livechat', label:'Hermes'" "{id:'livechat', label:'Jebat Agent'" "Live chat label"
            replace_in_file "$webui" '"OpenClaw Pattern"' '"Jebat Gateway Pattern"' "Pattern name"
            replace_in_file "$webui" '"Hermes Mode"' '"Jebat Agent Mode"' "Mode name"
            replace_in_file "$webui" '"Hermes posture active"' '"Jebat Agent posture active"' "Posture text"
            replace_in_file "$webui" '"OpenClaw-style surface"' '"Jebat Gateway surface"' "Surface text"
            replace_in_file "$webui" '"OpenClaw Hermes skill excerpt"' '"Jebat Gateway Jebat Agent skill excerpt"' "Excerpt label"
            replace_in_file "$webui" '"CLI, OpenClaw, VS Code' '"CLI, Jebat Gateway, VS Code' "Surface list"
            replace_in_file "$webui" '"Serve OpenClaw-style control page."' '"Serve Jebat Gateway-style control page."' "Docstring"
        fi
    done

    # Export scripts
    local export_scripts=(
        "$REPO_ROOT/scripts/export_jebat_gateway.py"
        "$REPO_ROOT/jebat-core/scripts/export_jebat_gateway.py"
    )

    for script in "${export_scripts[@]}"; do
        if [[ -f "$script" ]]; then
            log_info "Processing: $script"
            replace_in_file "$script" 'Path.home() / ".openclaw"' 'Path.home() / ".jebat"' "Source root path"
            replace_in_file "$script" 'REPO_ROOT / "integrations" / "openclaw"' 'REPO_ROOT / "integrations" / "jebat-gateway"' "Target root path"
            replace_in_file "$script" 'openclaw.json' 'jebat-gateway.json' "Source config name"
            replace_in_file "$script" 'openclaw.template.json' 'jebat-gateway.template.json' "Target config name"
            replace_in_file "$script" 'skills/hermes-agent/SKILL.md' 'skills/jebat-agent/SKILL.md' "Skill path"
            replace_in_file "$script" 'JEBATCore OpenClaw bundle' 'JEBATCore Jebat Gateway bundle' "Print message"
        fi
    done

    # jebat_selector.py
    local selectors=(
        "$REPO_ROOT/jebat_selector.py"
        "$REPO_ROOT/jebat-core/jebat_selector.py"
    )

    for selector in "${selectors[@]}"; do
        if [[ -f "$selector" ]]; then
            log_info "Processing: $selector"
            replace_in_file "$selector" 'OpenClaw-style interface' 'Jebat Gateway-style interface' "Docstring"
            replace_in_file "$selector" 'OpenClaw-Style Bot Orchestrator' 'Jebat Gateway-Style Bot Orchestrator' "Description"
            replace_in_file "$selector" 'OpenClaw-style UI' 'Jebat Gateway-style UI' "UI description"
        fi
    done

    # devtool __init__.py
    local devtool_inits=(
        "$REPO_ROOT/apps/devtool/__init__.py"
        "$REPO_ROOT/jebat-core/jebat_dev/__init__.py"
    )

    for init in "${devtool_inits[@]}"; do
        if [[ -f "$init" ]]; then
            log_info "Processing: $init"
            replace_in_file "$init" 'OpenClaw architecture' 'Jebat Gateway architecture' "Architecture reference"
        fi
    done

    # validate.py
    local validators=(
        "$REPO_ROOT/packages/adapters/adapters/validate.py"
        "$REPO_ROOT/packages/cli/adapters/validate.py"
        "$REPO_ROOT/jebat-core/adapters/validate.py"
    )

    for validator in "${validators[@]}"; do
        if [[ -f "$validator" ]]; then
            log_info "Processing: $validator"
            replace_in_file "$validator" 'openclaw.json' 'jebat-gateway.json' "Config file reference"
        fi
    done

    # agent_registry.py
    local registry="$REPO_ROOT/apps/api/core/agents/agent_registry.py"
    if [[ -f "$registry" ]]; then
        log_info "Processing: $registry"
        # Keep model name, just add alias comment if needed
        # No changes needed since we're keeping external model names
    fi

    # ==========================================
    # PHASE 4: Skill Definitions
    # ==========================================
    log_info ""
    log_info "========================================="
    log_info "PHASE 4: Skill Definitions"
    log_info "========================================="

    local skill_files=(
        "$REPO_ROOT/skills/jebat-agent/SKILL.md"
        "$REPO_ROOT/jebat-core/skills/jebat-agent/SKILL.md"
        "$REPO_ROOT/jebat-core/jebat-tokguru/skills/jebat-native/jebat-agent/SKILL.md"
        "$REPO_ROOT/integrations/jebat-gateway/workspace/skills/jebat-agent/SKILL.md"
        "$REPO_ROOT/jebat-core/integrations/jebat-gateway/workspace/skills/jebat-agent/SKILL.md"
    )

    for skill in "${skill_files[@]}"; do
        if [[ -f "$skill" ]]; then
            log_info "Processing: $skill"
            replace_in_file "$skill" 'name: hermes-agent' 'name: jebat-agent' "Skill name"
            replace_in_file "$skill" '# Hermes Agent' '# Jebat Agent' "Title"
            replace_in_file "$skill" 'tags:.*hermes' 'tags: jebat-agent' "Tags (hermes)"
        fi
    done

    # skills_index.json
    local indices=(
        "$REPO_ROOT/jebat-core/skills_index.json"
    )

    for index in "${indices[@]}"; do
        if [[ -f "$index" ]]; then
            log_info "Processing: $index"
            replace_in_file "$index" '"name": "hermes-agent"' '"name": "jebat-agent"' "Skill name"
            replace_in_file "$index" '"tags": ["jebat", "hermes"' '"tags": ["jebat", "jebat-agent"' "Tags"
            replace_in_file "$index" 'skills/jebat-native/hermes-agent/SKILL.md' 'skills/jebat-native/jebat-agent/SKILL.md' "Skill path"
        fi
    done

    # ==========================================
    # PHASE 5: Shell Scripts
    # ==========================================
    log_info ""
    log_info "========================================="
    log_info "PHASE 5: Shell Scripts"
    log_info "========================================="

    local setup_script="$REPO_ROOT/setup-jebat-workstation.sh"
    if [[ -f "$setup_script" ]]; then
        log_info "Processing: $setup_script"
        replace_in_file "$setup_script" 'ollama pull hermes-sec-v2:latest' 'ollama pull hermes-sec-v2:latest  # alias: jebat-security' "Ollama model with alias comment"
    fi

    # jebat.js CLI
    local cli_js="$REPO_ROOT/packages/cli/bin/jebat.js"
    if [[ -f "$cli_js" ]]; then
        log_info "Processing: $cli_js"
        replace_in_file "$cli_js" '"hermes-agent"' '"jebat-agent"' "Core skills list"
    fi

    # ==========================================
    # PHASE 6: Documentation (Root Level)
    # ==========================================
    log_info ""
    log_info "========================================="
    log_info "PHASE 6: Documentation (Root Level)"
    log_info "========================================="

    # Major doc files - batch process
    local root_docs=(
        "$REPO_ROOT/JEBAT.md"
        "$REPO_ROOT/CODEX_PROFILE.md"
        "$REPO_ROOT/core/TOOLS.md"
        "$REPO_ROOT/core/ORCHESTRATION_PATTERNS.md"
        "$REPO_ROOT/SKILL_REGISTRY.md"
        "$REPO_ROOT/PROMPT_INJECTION_DEFENSE.md"
        "$REPO_ROOT/REDTEAM_TEST_CASES.md"
        "$REPO_ROOT/OPERATIONS.md"
        "$REPO_ROOT/OPS_DASHBOARD.md"
        "$REPO_ROOT/BRAIN_USAGE_POLICY.md"
        "$REPO_ROOT/brain/INDEX.md"
        "$REPO_ROOT/brain/concepts/Jebat.md"
        "$REPO_ROOT/JEBAT_INTEGRATION_PLAN.md"
        "$REPO_ROOT/JEBAT_RUNTIME_PROCEDURES.md"
        "$REPO_ROOT/JEBAT_IMPORT_PLAN.md"
        "$REPO_ROOT/JEBAT_EXEC_SUMMARY.md"
        "$REPO_ROOT/JEBAT_FOUNDATION_MILESTONE.md"
        "$REPO_ROOT/JEBAT_ABSORPTION_SUMMARY.md"
        "$REPO_ROOT/EXTERNAL_SKILL_VETTING.md"
        "$REPO_ROOT/EXTERNAL_SKILL_REVIEWS.md"
        "$REPO_ROOT/SKILL_VETTING_WORKFLOW.md"
        "$REPO_ROOT/SKILL_SCORING_GUIDE.md"
        "$REPO_ROOT/DIRECT_SOURCE_INSPECTION_NOTES.md"
        "$REPO_ROOT/REVIEWED_SKILL_ATTESTATION_GUIDE.md"
        "$REPO_ROOT/REVIEWED_SKILL_ATTESTATION_FORMAT.md"
        "$REPO_ROOT/REVIEWED_SKILLS_MANIFEST.md"
        "$REPO_ROOT/MEMORY_PROMOTION_GUIDE.md"
        "$REPO_ROOT/PHASE2_HELPERS_GUIDE.md"
        "$REPO_ROOT/JEBAT_ADMIN.md"
        "$REPO_ROOT/SECOND_BATCH_EXTERNAL_REVIEWS.md"
        "$REPO_ROOT/DECISION_PROVENANCE_LOG.md"
    )

    for doc in "${root_docs[@]}"; do
        if [[ -f "$doc" ]]; then
            log_info "Processing: $doc"
            replace_in_file "$doc" 'OpenClaw' 'Jebat Gateway' "OpenClaw brand"
            replace_in_file "$doc" 'openclaw' 'jebat-gateway' "openclaw identifier"
            replace_in_file "$doc" 'Hermes' 'Jebat Agent' "Hermes brand"
            replace_in_file "$doc" 'hermes-agent' 'jebat-agent' "hermes-agent identifier"
        fi
    done

    # ==========================================
    # PHASE 7: Documentation (jebat-core Level)
    # ==========================================
    log_info ""
    log_info "========================================="
    log_info "PHASE 7: Documentation (jebat-core Level)"
    log_info "========================================="

    local core_docs=(
        "$REPO_ROOT/jebat-core/JEBAT.md"
        "$REPO_ROOT/jebat-core/JEBAT_ASSISTANT_GUIDE.md"
        "$REPO_ROOT/jebat-core/AGENTS.md"
        "$REPO_ROOT/jebat-core/TOOLS.md"
        "$REPO_ROOT/jebat-core/MEMORY.md"
        "$REPO_ROOT/jebat-core/USER.md"
        "$REPO_ROOT/jebat-core/BOOTSTRAP.md"
        "$REPO_ROOT/jebat-core/KERISCORE.md"
        "$REPO_ROOT/jebat-core/JEBAT_STATUS.md"
        "$REPO_ROOT/jebat-core/JEBAT_PRODUCT_FAMILY.md"
        "$REPO_ROOT/jebat-core/JEBAT_DEVASSISTANT_PLAN.md"
    )

    for doc in "${core_docs[@]}"; do
        if [[ -f "$doc" ]]; then
            log_info "Processing: $doc"
            replace_in_file "$doc" 'OpenClaw' 'Jebat Gateway' "OpenClaw brand"
            replace_in_file "$doc" 'openclaw' 'jebat-gateway' "openclaw identifier"
            replace_in_file "$doc" 'Hermes' 'Jebat Agent' "Hermes brand"
            replace_in_file "$doc" 'hermes-agent' 'jebat-agent' "hermes-agent identifier"
        fi
    done

    # Workspace docs in integrations
    local workspace_docs=(
        "$REPO_ROOT/jebat-core/integrations/jebat-gateway/workspace/BOOTSTRAP.md"
        "$REPO_ROOT/jebat-core/integrations/jebat-gateway/workspace/IDENTITY.md"
        "$REPO_ROOT/jebat-core/integrations/jebat-gateway/workspace/SOUL.md"
        "$REPO_ROOT/jebat-core/integrations/jebat-gateway/workspace/TOOLS.md"
        "$REPO_ROOT/jebat-core/integrations/jebat-gateway/workspace/ORCHESTRA.md"
        "$REPO_ROOT/jebat-core/integrations/jebat-gateway/workspace/USER.md"
    )

    for doc in "${workspace_docs[@]}"; do
        if [[ -f "$doc" ]]; then
            log_info "Processing: $doc"
            replace_in_file "$doc" 'OpenClaw' 'Jebat Gateway' "OpenClaw brand"
            replace_in_file "$doc" 'openclaw' 'jebat-gateway' "openclaw identifier"
            replace_in_file "$doc" 'Hermes' 'Jebat Agent' "Hermes brand"
            replace_in_file "$doc" 'hermes-agent' 'jebat-agent' "hermes-agent identifier"
            replace_in_file "$doc" '~/.openclaw' '~/.jebat' "Home directory path"
        fi
    done

    # ==========================================
    # PHASE 8: Web UI Components
    # ==========================================
    log_info ""
    log_info "========================================="
    log_info "PHASE 8: Web UI Components"
    log_info "========================================="

    local web_ui=(
        "$REPO_ROOT/apps/web/app/page.tsx"
        "$REPO_ROOT/apps/web/app/setup/page.tsx"
    )

    for ui in "${web_ui[@]}"; do
        if [[ -f "$ui" ]]; then
            log_info "Processing: $ui"
            replace_in_file "$ui" 'hermes-agent' 'jebat-agent' "Agent skill reference"
            replace_in_file "$ui" 'hermes-sec-v2' 'hermes-sec-v2' "Model name (keep, external)"
        fi
    done

    # ==========================================
    # PHASE 9: Test Files
    # ==========================================
    log_info ""
    log_info "========================================="
    log_info "PHASE 9: Test Files"
    log_info "========================================="

    local test_files=(
        "$REPO_ROOT/test_llm_cli.py"
        "$REPO_ROOT/jebat-core/test_llm_cli.py"
    )

    for test in "${test_files[@]}"; do
        if [[ -f "$test" ]]; then
            log_info "Processing: $test"
            replace_in_file "$test" 'hermes-agent' 'jebat-agent' "Agent skill reference"
        fi
    done

    # ==========================================
    # PHASE 10: Memory & Log Files
    # ==========================================
    log_info ""
    log_info "========================================="
    log_info "PHASE 10: Memory & Log Files (Optional)"
    log_info "========================================="

    log_warn "Memory/log files contain historical references."
    log_warn "These can be updated but may lose historical context."
    log_warn "Skipping by default. Run manually if needed."

    # ==========================================
    # SUMMARY
    # ==========================================
    log_info ""
    log_info "========================================="
    log_info "MIGRATION SUMMARY"
    log_info "========================================="
    log_info "Changes made: $CHANGES_MADE"
    log_info "Errors encountered: $ERRORS"
    log_info "Backup location: $BACKUP_DIR"
    log_info ""

    if $DRY_RUN; then
        log_info "This was a DRY RUN. No changes were made."
        log_info "Run without --dry-run to apply changes."
    elif [[ $ERRORS -eq 0 ]]; then
        log_success "Migration completed successfully!"
        log_info ""
        log_info "Next steps:"
        log_info "1. Review changes with: git status"
        log_info "2. Test the application"
        log_info "3. Commit changes when ready"
        log_info ""
        log_info "To rollback, run: bash scripts/rebrand_to_jebat.sh --rollback"
    else
        log_error "Migration completed with $ERRORS error(s)."
        log_info "Review the errors above and fix them manually."
        log_info "Backup is available at: $BACKUP_DIR"
    fi

    log_info ""
    log_info "See REBRAND_MAP.md for full details."
}

# Run main
main
