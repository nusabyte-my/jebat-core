#!/usr/bin/env node
/**
 * postinstall.js - Runs after npm install to guide users through onboarding
 */

import { existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { platform } from "node:process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const packageRoot = join(__dirname, "..");
const isWindows = platform === "win32";

function printBanner() {
  console.log("");
  console.log("╔════════════════════════════════════════════════════════╗");
  console.log("║  🎉 JEBATCore Installed Successfully!                 ║");
  console.log("║  The LLM Ecosystem That Remembers Everything          ║");
  console.log("╚════════════════════════════════════════════════════════╝");
  console.log("");
}

function printQuickStart() {
  console.log("📦 Installation complete! Here's what to do next:");
  console.log("");
  console.log("1️⃣  Run the installer:");
  console.log("   $ jebatcore install");
  console.log("");
  console.log("2️⃣  View help:");
  console.log("   $ jebatcore help");
  console.log("");
  console.log("3️⃣  Check system health:");
  console.log("   $ jebatcore doctor");
  console.log("");
  console.log("4️⃣  List available skills:");
  console.log("   $ jebatcore skill-list");
  console.log("");
  console.log("💡 Pro tip: Use --dry-run to preview changes before installing");
  console.log("");
}

function checkBundleFiles() {
  const requiredFiles = [
    "AGENTS.md",
    "SOUL.md",
    "IDENTITY.md",
    "MEMORY.md",
    "ORCHESTRA.md",
    "TOOLS.md",
    "USER.md"
  ];

  const missingFiles = [];

  for (const file of requiredFiles) {
    const filePath = join(packageRoot, file);
    if (!existsSync(filePath)) {
      missingFiles.push(file);
    }
  }

  return missingFiles;
}

function main() {
  printBanner();

  // Check if bundle files are present
  const missingFiles = checkBundleFiles();

  if (missingFiles.length > 0) {
    console.log("⚠️  Warning: Some identity files are missing:");
    for (const file of missingFiles) {
      console.log(`   ❌ ${file}`);
    }
    console.log("");
    console.log("This might indicate an incomplete installation.");
    console.log("Please try reinstalling or report an issue:");
    console.log("https://github.com/nusabyte-my/jebat-core/issues");
    console.log("");
  } else {
    console.log("✅ All identity files verified successfully!");
    console.log("");
  }

  // Print quick start guide
  printQuickStart();

  // Point to onboarding script
  const onboardingScript = isWindows
    ? "scripts\\onboarding.bat"
    : "bash scripts/onboarding.sh";

  console.log("🚀 For a guided setup experience, run:");
  console.log(`   $ ${onboardingScript}`);
  console.log("");
  console.log("📚 Documentation: https://github.com/nusabyte-my/jebat-core");
  console.log("");
}

main();
