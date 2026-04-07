#!/usr/bin/env python3
"""
Serangan Auto-Fix — Automatic vulnerability remediation
Runs after security-autonomous-scan.py to offer and apply fixes.
"""

import os
import re
import sys
import shutil
from datetime import datetime
from pathlib import Path

WORKSPACE = os.environ.get("JEBAT_WORKSPACE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKUP_DIR = os.path.join(WORKSPACE, "security", "fix-backups")

# ─── Fix Rules ────────────────────────────────────────────────────────────────

FIX_RULES = [
    {
        "name": "Replace MD5 with SHA-256",
        "pattern": r'hashlib\.md5\s*\(',
        "replacement": 'hashlib.sha256(',
        "severity": "MEDIUM",
        "extensions": (".py",),
        "description": "MD5 is cryptographically broken. Replaced with SHA-256.",
    },
    {
        "name": "Replace SHA1 with SHA-256",
        "pattern": r'hashlib\.sha1\s*\(',
        "replacement": 'hashlib.sha256(',
        "severity": "LOW",
        "extensions": (".py",),
        "description": "SHA1 has known collision attacks. Replaced with SHA-256.",
    },
    {
        "name": "Safe YAML loading",
        "pattern": r'yaml\.load\s*\((?!.*Loader\s*=)',
        "replacement": 'yaml.safe_load(',
        "severity": "HIGH",
        "extensions": (".py",),
        "description": "yaml.safe_load() is unsafe with untrusted input. Using safe_load().",
    },
    {
        "name": "Remove # TODO: Replace eval() with safe alternative
# eval()",
        "pattern": r'\beval\s*\(',
        "replacement": '# TODO: Replace # TODO: Replace eval() with safe alternative
# eval() with safe alternative\n# # TODO: Replace eval() with safe alternative
# eval(',
        "severity": "CRITICAL",
        "extensions": (".py", ".js", ".ts"),
        "description": "# TODO: Replace eval() with safe alternative
# eval() allows arbitrary code execution. Commented out for manual review.",
    },
    {
        "name": "Remove # TODO: Replace exec() with safe alternative
# exec()",
        "pattern": r'\bexec\s*\(',
        "replacement": '# TODO: Replace # TODO: Replace exec() with safe alternative
# exec() with safe alternative\n# # TODO: Replace exec() with safe alternative
# exec(',
        "severity": "CRITICAL",
        "extensions": (".py", ".js", ".ts"),
        "description": "# TODO: Replace exec() with safe alternative
# exec() allows arbitrary code execution. Commented out for manual review.",
    },
    {
        "name": "React dangerouslySetInnerHTML",
        "pattern": r'dangerouslySetInnerHTML',
        "replacement": '/* TODO: Sanitize HTML before using dangerouslySetInnerHTML */ dangerouslySetInnerHTML',
        "severity": "MEDIUM",
        "extensions": (".tsx", ".jsx", ".js", ".ts"),
        "description": "Added warning comment. Sanitize HTML input before use.",
    },
    {
        "name": "Pickle deserialization",
        "pattern": r'pickle\.loads?\s*\(',
        "replacement": '# TODO: Replace pickle with json/msgpack\n# # TODO: Replace pickle with json/msgpack
# pickle.load(',
        "severity": "CRITICAL",
        "extensions": (".py",),
        "description": "Pickle allows arbitrary code execution. Commented out for manual review.",
    },
    {
        "name": "os.system command injection",
        "pattern": r'os\.system\s*\(',
        "replacement": 'subprocess.run(',  # Will need manual fix for args
        "severity": "HIGH",
        "extensions": (".py",),
        "description": "subprocess.run() is vulnerable to command injection. Placeholder: use subprocess.run with list args.",
    },
]


def backup_file(filepath):
    """Create a backup before modifying a file."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = os.path.join(BACKUP_DIR, f"{os.path.basename(filepath)}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak")
    shutil.copy2(filepath, backup_path)
    return backup_path


def apply_fix(filepath, rule):
    """Apply a single fix rule to a file. Returns number of fixes applied."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        matches = re.findall(rule["pattern"], content)
        if not matches:
            return 0

        new_content = re.sub(rule["pattern"], rule["replacement"], content)

        if new_content == content:
            return 0

        backup_file(filepath)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

        return len(matches)
    except Exception as e:
        print(f"  ⚠️  Error fixing {filepath}: {e}")
        return 0


def find_fixable_files():
    """Find all files that can be auto-fixed."""
    fixable = {}
    for rule in FIX_RULES:
        for root, dirs, files in os.walk(WORKSPACE):
            # Skip excluded dirs
            dirs[:] = [d for d in dirs if d not in {"node_modules", ".next", "out", ".git", "jebat-core", ".claude", ".gemini", "__pycache__", "security", "fix-backups"}]
            for f in files:
                if f.endswith(rule["extensions"]):
                    filepath = os.path.join(root, f)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(rule["pattern"], content):
                            if rule["name"] not in fixable:
                                fixable[rule["name"]] = {"rule": rule, "files": [], "total_fixes": 0}
                            fixable[rule["name"]]["files"].append(filepath)
                    except (PermissionError, UnicodeDecodeError):
                        pass
    return fixable


def generate_fix_report(fixable, fixes_applied):
    """Generate a report of what was fixed."""
    report = f"""# 🔧 JEBAT Auto-Fix Report

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Workspace:** {WORKSPACE}

## Summary

| Fix Type | Files Modified | Instances Fixed |
|----------|---------------|-----------------|
"""
    total_fixes = 0
    total_files = 0
    for name, data in fixes_applied.items():
        if data > 0:
            rule = next(r for r in FIX_RULES if r["name"] == name)
            report += f"| {rule['description'][:50]} | {len(fixable[name]['files'])} | {data} |\n"
            total_fixes += data
            total_files += len(fixable[name]["files"])

    report += f"\n**Total:** {total_files} files modified, {total_fixes} instances fixed\n"
    report += f"\nBackups saved to: `{BACKUP_DIR}/`\n"

    return report


def main():
    print("🔧 Serangan Auto-Fix — Analyzing fixable vulnerabilities...")
    print(f"   Workspace: {WORKSPACE}")

    # Find fixable issues
    fixable = find_fixable_files()

    if not fixable:
        print("\n   ✅ No auto-fixable issues found.")
        return 0

    # Show what can be fixed
    print("\n   Found auto-fixable issues:")
    total_potential = 0
    for name, data in fixable.items():
        rule = data["rule"]
        print(f"   {rule['severity']:8s} {name}: {len(data['files'])} file(s)")
        total_potential += len(data["files"])

    print(f"\n   Total: {total_potential} files can be auto-fixed")
    print(f"   Backups will be saved to: {BACKUP_DIR}")

    # Apply fixes
    print("\n   Applying fixes...")
    fixes_applied = {}
    for name, data in fixable.items():
        fixes_applied[name] = 0
        for filepath in data["files"]:
            count = apply_fix(filepath, data["rule"])
            fixes_applied[name] += count
            if count > 0:
                rel_path = os.path.relpath(filepath, WORKSPACE)
                print(f"   ✅ {name}: {rel_path} ({count} instance(s))")

    # Generate report
    report = generate_fix_report(fixable, fixes_applied)
    report_dir = os.path.join(WORKSPACE, "security", "scan-reports")
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, f"autofix-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md")
    with open(report_file, "w") as f:
        f.write(report)

    print(f"\n🔧 Auto-fix complete. Report: {report_file}")

    total_fixed = sum(fixes_applied.values())
    if total_fixed > 0:
        print(f"   ✅ {total_fixed} vulnerability instances fixed across {sum(1 for v in fixes_applied.values() if v > 0)} fix types")
        print(f"   💾 Backups in: {BACKUP_DIR}")
        print(f"   📋 Review report: {report_file}")
    else:
        print("   ⚠️  No fixes were applied (patterns may need manual review)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
