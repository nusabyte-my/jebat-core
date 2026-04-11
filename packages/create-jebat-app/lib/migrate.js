const fs = require('fs-extra');
const path = require('path');
const os = require('os');
const chalk = require('chalk');

const homeDir = os.homedir();
const oldDir = path.join(homeDir, '.openclaw');
const newDir = path.join(homeDir, '.jebat');

async function migrate(options = {}) {
  console.log(chalk.bold('\n🔄 Migrating from OpenClaw/Hermes to Jebat\n'));

  // Check if old config exists
  if (!(await fs.pathExists(oldDir))) {
    console.log(chalk.yellow('⚠️  No OpenClaw config found at ~/.openclaw'));
    console.log(chalk.dim('Nothing to migrate. Run regular setup instead.'));
    process.exit(0);
  }

  console.log(chalk.blue('1/4'), 'Found OpenClaw config at', chalk.dim(oldDir));

  // Backup new dir if exists
  if (await fs.pathExists(newDir)) {
    const backupDir = path.join(homeDir, '.jebat.backup.' + Date.now());
    console.log(chalk.blue('2/4'), 'Backing up existing Jebat config to', chalk.dim(backupDir));
    await fs.move(newDir, backupDir);
  } else {
    console.log(chalk.blue('2/4'), 'No existing Jebat config to backup');
  }

  // Copy files
  console.log(chalk.blue('3/4'), 'Copying and converting config...');
  await fs.copy(oldDir, newDir, { overwrite: true });

  // Convert config files
  const oldConfig = path.join(newDir, 'openclaw.json');
  const newConfig = path.join(newDir, 'jebat-gateway.json');

  if (await fs.pathExists(oldConfig)) {
    const config = await fs.readJson(oldConfig);
    
    // Convert structure if needed
    const convertedConfig = {
      gateway: config.gateway || {},
      env: config.env || {},
      channels: config.channels || {},
      plugins: config.plugins || {},
      agents: config.agents || {},
    };

    await fs.writeJson(newConfig, convertedConfig, { spaces: 2 });
    await fs.remove(oldConfig);
    console.log(chalk.green('   ✓'), 'Converted openclaw.json → jebat-gateway.json');
  }

  // Convert skill names
  const oldSkillDir = path.join(newDir, 'workspace', 'skills', 'hermes-agent');
  const newSkillDir = path.join(newDir, 'workspace', 'skills', 'jebat-agent');

  if (await fs.pathExists(oldSkillDir)) {
    await fs.move(oldSkillDir, newSkillDir, { overwrite: true });
    console.log(chalk.green('   ✓'), 'Renamed hermes-agent → jebat-agent');
  }

  // Update workspace references
  const workspaceFiles = await fs.readdir(path.join(newDir, 'workspace')).catch(() => []);
  for (const file of workspaceFiles) {
    const filePath = path.join(newDir, 'workspace', file);
    if ((await fs.stat(filePath)).isFile()) {
      let content = await fs.readFile(filePath, 'utf8');
      content = content
        .replace(/openclaw/g, 'jebat-gateway')
        .replace(/OpenClaw/g, 'Jebat Gateway')
        .replace(/hermes-agent/g, 'jebat-agent')
        .replace(/Hermes Agent/g, 'Jebat Agent');
      await fs.writeFile(filePath, content);
    }
  }

  console.log(chalk.blue('4/4'), 'Migration complete!');

  // Summary
  console.log(chalk.green('\n✅ Migration successful!\n'));
  console.log(chalk.bold('What was migrated:'));
  console.log(`  • Config: ${chalk.dim('~/.openclaw → ~/.jebat')}`);
  console.log(`  • Skills: ${chalk.dim('hermes-agent → jebat-agent')}`);
  console.log(`  • Workspace: ${chalk.dim('Updated references')}\n`);

  console.log(chalk.bold('Next steps:'));
  console.log(`  1. Review config: ${chalk.dim('cat ~/.jebat/jebat-gateway.json')}`);
  console.log(`  2. Start gateway: ${chalk.green('npx jebat-gateway start')}`);
  console.log(`  3. Remove old config (optional): ${chalk.dim('rm -rf ~/.openclaw')}\n`);

  console.log(chalk.dim('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'));
  console.log(chalk.green.bold('\n🎉 Migration complete! Welcome to Jebat!\n'));
}

module.exports = { migrate };
