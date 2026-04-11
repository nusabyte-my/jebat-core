#!/usr/bin/env node

const { createApp } = require('./lib/create-app');
const { setupIDE } = require('./lib/setup-ide');
const { setupChannel } = require('./lib/setup-channel');
const { migrate } = require('./lib/migrate');
const { setupLocalModel } = require('./lib/setup-local-model');
const pkg = require('./package.json');

const args = process.argv.slice(2);
const flags = {};

// Parse arguments
args.forEach(arg => {
  if (arg.startsWith('--')) {
    const [key, value] = arg.slice(2).split('=');
    flags[key] = value || true;
  }
});

// Handle help
if (flags.help || flags.h) {
  console.log(`
${pkg.name} v${pkg.version}

USAGE:
  npx jebat-agent [options]

OPTIONS:
  --quick          Quick setup (gateway only)
  --full           Full setup (workspace + skills)
  --ide <ide>      IDE integration (vscode, zed, claude, gemini, cursor)
  --channel <ch>   Channel setup (telegram, discord, whatsapp, slack, all)
  --local-model <m> Setup local model (qwen2.5, phi3, hermes3, gemma4, all)
  --migrate        Migrate from OpenClaw/Hermes
  --port <port>    Gateway port (default: 18789)
  --token <token>  Auth token (default: auto-generated)
  --model <model>  Primary model (default: ollama/hermes3:8b)
  --help, -h       Show this help
  --version, -v    Show version

EXAMPLES:
  npx jebat-agent              # Interactive wizard
  npx jebat-agent --quick      # Minimal setup
  npx jebat-agent --full       # Full workspace
  npx jebat-agent --ide vscode # VS Code integration
  npx jebat-agent --channel tg # Telegram bot
  npx jebat-agent --local-model qwen2.5  # Setup local Qwen2.5
  npx jebat-agent --local-model gemma4   # Setup local Gemma 4
  npx jebat-agent --migrate    # Migrate from OpenClaw

SUPPORTED IDEs:
  vscode, zed, claude, gemini, cursor

SUPPORTED CHANNELS:
  telegram, discord, whatsapp, slack, all

LOCAL MODELS:
  qwen2.5  - Qwen2.5 3B (RECOMMENDED, ~7GB)
  phi3     - Phi-3 Mini (~8GB)
  hermes3  - Hermes3 8B (~16GB)
  gemma4   - Gemma 4 via Ollama (~5-9GB)
  all      - Install all models

MORE INFO:
  https://github.com/nusabyte-my/jebat-core
`);
  process.exit(0);
}

if (flags.version || flags.v) {
  console.log(`v${pkg.version}`);
  process.exit(0);
}

// Main execution
async function main() {
  try {
    if (flags.migrate) {
      await migrate(flags);
    } else if (flags.ide) {
      await setupIDE(flags.ide, flags);
    } else if (flags.channel) {
      await setupChannel(flags.channel, flags);
    } else if (flags.quick) {
      await createApp({ type: 'quick', ...flags });
    } else if (flags.full) {
      await createApp({ type: 'full', ...flags });
    } else {
      // Interactive mode
      const inquirer = require('inquirer');
      const answers = await inquirer.prompt([
        {
          type: 'list',
          name: 'setupType',
          message: 'What would you like to set up?',
          choices: [
            { name: 'Quick (gateway only)', value: 'quick' },
            { name: 'Full (workspace + skills)', value: 'full' },
            { name: 'IDE integration', value: 'ide' },
            { name: 'Channel setup', value: 'channel' },
            { name: 'Migrate from OpenClaw/Hermes', value: 'migrate' },
          ],
        },
      ]);

      if (answers.setupType === 'ide') {
        const { ide } = await inquirer.prompt([
          {
            type: 'list',
            name: 'ide',
            message: 'Which IDE?',
            choices: ['vscode', 'zed', 'claude', 'gemini', 'cursor'],
          },
        ]);
        await setupIDE(ide, flags);
      } else if (answers.setupType === 'channel') {
        const { channel } = await inquirer.prompt([
          {
            type: 'list',
            name: 'channel',
            message: 'Which channel?',
            choices: ['telegram', 'discord', 'whatsapp', 'slack', 'all'],
          },
        ]);
        await setupChannel(channel, flags);
      } else if (answers.setupType === 'migrate') {
        await migrate(flags);
      } else {
        await createApp({ type: answers.setupType, ...flags });
      }
    }
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    process.exit(1);
  }
}

main();
