const fs = require('fs-extra');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const chalk = require('chalk');
const { execa } = require('execa');

const homeDir = os.homedir();
const jebatDir = path.join(homeDir, '.jebat');

// ASCII Art Banner
const banner = `
${chalk.cyan.bold('██╗ ██████╗')}    ${chalk.yellow.bold('Gateway')} + ${chalk.green.bold('Agent')}
${chalk.cyan.bold('██║██╔════╝')}    ${chalk.white('AI Agent Platform')}
${chalk.cyan.bold('██║██║ ███╗')}   ${chalk.dim('v1.0.0')}
${chalk.cyan.bold('██║██║  ██║')}   ${chalk.dim('Setup Wizard')}
${chalk.cyan.bold('██║╚██████╔╝')}
${chalk.cyan.bold('╚═╝ ╚═════╝')}
`;

async function createApp(options = {}) {
  console.log(banner);
  
  const setupType = options.type || 'full';
  const port = options.port || 18789;
  const token = options.token || crypto.randomBytes(32).toString('hex');
  const model = options.model || 'ollama/hermes3:8b';

  console.log(chalk.bold('\n🚀 Setting up Jebat...\n'));

  // Step 1: Create directory structure
  console.log(chalk.blue('1/5'), 'Creating directory structure...');
  await fs.ensureDir(path.join(jebatDir, 'workspace', 'skills'));
  await fs.ensureDir(path.join(jebatDir, 'extensions'));
  console.log(chalk.green('   ✓'), `Created ${chalk.dim(jebatDir)}\n`);

  // Step 2: Generate gateway config
  console.log(chalk.blue('2/5'), 'Generating gateway config...');
  const config = {
    gateway: {
      port: port,
      mode: 'local',
      bind: 'loopback',
      auth: {
        mode: 'token',
        token: token,
      },
      tailscale: {
        mode: 'off',
        resetOnExit: false,
      },
    },
    env: {
      shellEnv: {
        enabled: true,
        timeoutMs: 15000,
      },
    },
    channels: {
      telegram: {
        enabled: false,
        dmPolicy: 'pairing',
        botToken: '${TELEGRAM_BOT_TOKEN}',
        groupPolicy: 'allowlist',
        streaming: 'partial',
      },
    },
    plugins: {
      installs: {},
    },
    agents: {
      defaults: {
        model: {
          primary: model,
          fallbacks: [
            'ollama/hermes-sec-v2:latest',
            'google-gemini-cli/gemini-3-flash-preview',
          ],
        },
        systemPrompt: 'You are Jebat Agent, a helpful AI assistant.',
      },
      list: [
        {
          id: 'jebat-agent',
          identity: {
            name: 'Jebat Agent',
            title: 'Primary Agent',
          },
        },
      ],
    },
  };

  await fs.writeJson(
    path.join(jebatDir, 'jebat-gateway.json'),
    config,
    { spaces: 2 }
  );
  console.log(chalk.green('   ✓'), 'Gateway config generated\n');

  // Step 3: Setup workspace (if full)
  if (setupType === 'full') {
    console.log(chalk.blue('3/5'), 'Setting up workspace and skills...');
    
    // Create workspace files
    const workspaceFiles = {
      'IDENTITY.md': '# Jebat Workspace\n\nYour AI agent workspace.',
      'SOUL.md': '# Jebat Agent Soul\n\nDirect, technical, implementation-focused.',
      'TOOLS.md': '# Tools\n\nAvailable tools and capabilities.',
      'USER.md': '# User Preferences\n\nCustomize your agent behavior here.',
    };

    for (const [file, content] of Object.entries(workspaceFiles)) {
      await fs.writeFile(path.join(jebatDir, 'workspace', file), content);
    }

    // Create skill definition
    const skillMd = `---
name: jebat-agent
description: Primary Jebat agent for planning, execution, and multi-agent orchestration
category: jebat-native
tags:
  - jebat
  - agent
  - multi-agent
  - planning
ide_support:
  - vscode
  - zed
  - cursor
  - claude
  - gemini
author: JEBATCore / NusaByte
version: 1.0.0
---

# Jebat Agent

## Overview

Primary agent for the Jebat platform. Handles task planning, execution, and coordination.

## Capabilities

- Multi-agent orchestration
- Task planning and breakdown
- Code generation and review
- System administration
- Research and analysis

## Usage

This agent is automatically loaded for general tasks.
`;

    await fs.ensureDir(path.join(jebatDir, 'workspace', 'skills', 'jebat-agent'));
    await fs.writeFile(
      path.join(jebatDir, 'workspace', 'skills', 'jebat-agent', 'SKILL.md'),
      skillMd
    );

    console.log(chalk.green('   ✓'), 'Workspace and skills configured\n');
  } else {
    console.log(chalk.blue('3/5'), 'Skipping workspace setup (quick mode)\n');
  }

  // Step 4: Create .env file
  console.log(chalk.blue('4/5'), 'Creating environment file...');
  const envContent = `# Jebat Gateway Environment
JEBAT_GATEWAY_TOKEN=${token}
JEBAT_GATEWAY_PRIMARY_MODEL=${model}

# Optional: Channel tokens
# TELEGRAM_BOT_TOKEN=
# DISCORD_BOT_TOKEN=
# WHATSAPP_PHONE_ID=
`;

  await fs.writeFile(path.join(jebatDir, '.env'), envContent);
  console.log(chalk.green('   ✓'), 'Environment file created\n');

  // Step 5: Validation
  console.log(chalk.blue('5/5'), 'Validating setup...');
  
  const configExists = await fs.pathExists(path.join(jebatDir, 'jebat-gateway.json'));
  const envExists = await fs.pathExists(path.join(jebatDir, '.env'));

  if (configExists && envExists) {
    console.log(chalk.green('   ✓'), 'Validation passed\n');
  } else {
    console.log(chalk.yellow('   ⚠'), 'Some files missing, but continuing...\n');
  }

  // Print summary
  console.log(chalk.bold('\n✅ Jebat setup complete!\n'));
  console.log(chalk.bold('Configuration:'));
  console.log(`  Config: ${chalk.dim(jebatDir + '/jebat-gateway.json')}`);
  console.log(`  Port:   ${chalk.yellow(port.toString())}`);
  console.log(`  Model:  ${chalk.cyan(model)}`);
  console.log(`  Token:  ${chalk.dim(token.slice(0, 16) + '...')}\n`);

  console.log(chalk.bold('Next steps:'));
  console.log(`  1. ${chalk.green('cd')} to your project directory`);
  console.log(`  2. ${chalk.green('npx jebat-gateway start')} to launch`);
  console.log(`  3. Open ${chalk.cyan('http://localhost:' + port)} in your browser\n`);

  console.log(chalk.dim('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'));
  console.log(chalk.bold('\n📚 Documentation:'));
  console.log(`  • Integration Guide: ${chalk.cyan('INTEGRATION_GUIDE.md')}`);
  console.log(`  • Usage Guide: ${chalk.cyan('REBRAND_USAGE_GUIDE.md')}`);
  console.log(`  • GitHub: ${chalk.cyan('https://github.com/nusabyte-my/jebat-core')}\n`);

  console.log(chalk.dim('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'));
  console.log(chalk.green.bold('\n🎉 Ready to use Jebat!'));
  console.log(chalk.dim('   Start with: npx jebat-gateway start\n'));
}

module.exports = { createApp };
