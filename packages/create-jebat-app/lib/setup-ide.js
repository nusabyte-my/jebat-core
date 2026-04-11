const fs = require('fs-extra');
const path = require('path');
const os = require('os');
const chalk = require('chalk');

const homeDir = os.homedir();

async function setupIDE(ide, options = {}) {
  console.log(chalk.bold('\n🛠️  Setting up Jebat integration for', chalk.cyan(ide.toUpperCase()), '\n'));

  const jebatDir = path.join(homeDir, '.jebat');
  const workspaceDir = path.join(jebatDir, 'workspace');

  switch (ide) {
    case 'vscode':
    case 'cursor':
      await setupVSCode(workspaceDir, ide);
      break;
    case 'zed':
      await setupZed(workspaceDir);
      break;
    case 'claude':
      await setupClaude(workspaceDir);
      break;
    case 'gemini':
      await setupGemini(workspaceDir);
      break;
    default:
      console.log(chalk.yellow('⚠️  Unsupported IDE:'), ide);
      console.log(chalk.dim('Supported: vscode, zed, claude, gemini, cursor'));
      process.exit(1);
  }

  console.log(chalk.green('\n✅ IDE integration complete!'));
  console.log(chalk.dim('\nRestart your IDE to apply changes.\n'));
}

async function setupVSCode(workspaceDir, ide) {
  const vscodeDir = ide === 'cursor' 
    ? path.join(process.cwd(), '.cursor')
    : path.join(process.cwd(), '.vscode');

  await fs.ensureDir(vscodeDir);

  // Settings
  const settings = {
    'jebat.gateway.enabled': true,
    'jebat.agent.enabled': true,
    'jebat.workspace.path': workspaceDir,
    'editor.codeActionsOnSave': {
      'source.jebat': 'explicit',
    },
  };

  await fs.writeJson(path.join(vscodeDir, 'settings.json'), settings, { spaces: 2 });

  // Snippets
  const snippets = {
    'Jebat Agent Prompt': {
      prefix: 'jebat',
      body: [
        '---',
        'agent: jebat-agent',
        'mode: capture-first',
        '---',
        '',
        '$0',
      ],
      description: 'Jebat Agent prompt template',
    },
    'Jebat Skill Definition': {
      prefix: 'jebat-skill',
      body: [
        '---',
        'name: ${1:skill-name}',
        'description: ${2:Skill description}',
        'category: ${3:category}',
        'tags:',
        '  - ${4:tag}',
        '---',
        '',
        '# ${1:Skill Name}',
        '',
        '$0',
      ],
      description: 'Jebat skill definition template',
    },
  };

  await fs.writeJson(path.join(vscodeDir, 'jebat.code-snippets'), snippets, { spaces: 2 });

  console.log(chalk.green('✓'), `Created ${chalk.dim('.vscode/settings.json')}`);
  console.log(chalk.green('✓'), `Created ${chalk.dim('.vscode/jebat.code-snippets')}`);
}

async function setupZed(workspaceDir) {
  const zedDir = path.join(process.cwd(), '.zed');
  await fs.ensureDir(zedDir);

  const settings = {
    'jebat': {
      'gateway': {
        'enabled': true,
        'workspace': workspaceDir,
      },
    },
  };

  await fs.writeJson(path.join(zedDir, 'settings.json'), settings, { spaces: 2 });

  console.log(chalk.green('✓'), `Created ${chalk.dim('.zed/settings.json')}`);
}

async function setupClaude(workspaceDir) {
  const claudeDir = path.join(homeDir, '.claude');
  await fs.ensureDir(claudeDir);

  const settings = {
    'jebat_integration': {
      'enabled': true,
      'workspace': workspaceDir,
      'agent': 'jebat-agent',
    },
  };

  await fs.writeJson(path.join(claudeDir, 'settings.json'), settings, { spaces: 2 });

  // Create skill definition for Claude
  const skillDir = path.join(workspaceDir, 'skills', 'jebat-agent');
  await fs.ensureDir(skillDir);

  const skillMd = `# Jebat Agent for Claude

Integration layer between Claude Desktop and Jebat Gateway.

## Usage

When working with Jebat:
1. Reference the workspace at \`${workspaceDir}\`
2. Use Jebat skills for structured tasks
3. Follow capture-first operating model
`;

  await fs.writeFile(path.join(skillDir, 'CLAUDE.md'), skillMd);

  console.log(chalk.green('✓'), `Created ${chalk.dim('~/.claude/settings.json')}`);
  console.log(chalk.green('✓'), `Created ${chalk.dim('skills/jebat-agent/CLAUDE.md')}`);
}

async function setupGemini(workspaceDir) {
  const geminiDir = path.join(process.cwd(), '.gemini');
  await fs.ensureDir(geminiDir);

  const config = {
    'jebat': {
      'workspace': workspaceDir,
      'agent': 'jebat-agent',
    },
  };

  await fs.writeJson(path.join(geminiDir, 'config.json'), config, { spaces: 2 });

  console.log(chalk.green('✓'), `Created ${chalk.dim('.gemini/config.json')}`);
}

module.exports = { setupIDE };
