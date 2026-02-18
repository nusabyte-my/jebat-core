#!/usr/bin/env node
/**
 * JEBAT Awesome Skills Installer
 *
 * Usage:
 *   npx jebat-skills
 *   npx jebat-skills --vscode
 *   npx jebat-skills --zed
 *   npx jebat-skills --cursor
 *   npx jebat-skills --path ./my-skills
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const SKILLS_REPO = 'https://github.com/nusabyte-my/jebat-awesome-skills.git';

// IDE paths
const IDE_PATHS = {
  vscode: path.join(os.homedir(), '.vscode', 'jebat-skills'),
  zed: path.join(os.homedir(), '.config', 'zed', 'jebat-skills'),
  cursor: path.join(os.homedir(), '.cursor', 'jebat-skills'),
  claude: path.join(os.homedir(), '.claude', 'skills'),
  gemini: path.join(os.homedir(), '.gemini', 'skills'),
  universal: path.join(os.homedir(), '.jebat', 'skills'),
};

function detectIDE() {
  const detected = [];

  if (fs.existsSync(path.join(os.homedir(), '.vscode'))) {
    detected.push('vscode');
  }
  if (fs.existsSync(path.join(os.homedir(), '.config', 'zed'))) {
    detected.push('zed');
  }
  if (fs.existsSync(path.join(os.homedir(), '.cursor'))) {
    detected.push('cursor');
  }

  return detected;
}

function cloneRepo(targetPath) {
  console.log(`📦 Cloning skills to ${targetPath}...`);

  if (fs.existsSync(targetPath)) {
    console.log('⚠️  Skills already exist. Updating...');
    execSync('git pull', { cwd: targetPath, stdio: 'inherit' });
  } else {
    execSync(`git clone ${SKILLS_REPO} ${targetPath}`, { stdio: 'inherit' });
  }

  console.log(`✅ Skills installed to ${targetPath}`);
}

function main() {
  const args = process.argv.slice(2);

  console.log('🗡️  JEBAT Awesome Skills Installer\n');

  // Parse arguments
  let targetPath = null;

  if (args.includes('--vscode')) {
    targetPath = IDE_PATHS.vscode;
  } else if (args.includes('--zed')) {
    targetPath = IDE_PATHS.zed;
  } else if (args.includes('--cursor')) {
    targetPath = IDE_PATHS.cursor;
  } else if (args.includes('--claude')) {
    targetPath = IDE_PATHS.claude;
  } else if (args.includes('--gemini')) {
    targetPath = IDE_PATHS.gemini;
  } else if (args.includes('--path')) {
    const pathIndex = args.indexOf('--path');
    targetPath = args[pathIndex + 1] || process.cwd();
  }

  // If no specific IDE, use universal or detect
  if (!targetPath) {
    const detected = detectIDE();

    if (detected.length === 0) {
      console.log('ℹ️  No IDE detected. Using universal path.');
      targetPath = IDE_PATHS.universal;
    } else if (detected.length === 1) {
      console.log(`✓ Detected IDE: ${detected[0]}`);
      targetPath = IDE_PATHS[detected[0]];
    } else {
      console.log(`✓ Detected IDEs: ${detected.join(', ')}`);
      console.log('   Using universal path.');
      targetPath = IDE_PATHS.universal;
    }
  }

  // Create directory if needed
  const dir = path.dirname(targetPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  // Clone repository
  cloneRepo(targetPath);

  console.log('\n📚 Next steps:');
  console.log(`   1. Restart your IDE`);
  console.log(`   2. Use @skill-name in chat (e.g., @typescript-expert)`);
  console.log(`   3. Browse skills: ${targetPath}`);
  console.log('\n📖 Documentation: https://github.com/nusabyte-my/jebat-awesome-skills\n');
}

main();
