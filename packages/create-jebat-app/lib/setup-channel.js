const fs = require('fs-extra');
const path = require('path');
const os = require('os');
const chalk = require('chalk');
const inquirer = require('inquirer');

const homeDir = os.homedir();
const jebatDir = path.join(homeDir, '.jebat');

async function setupChannel(channel, options = {}) {
  console.log(chalk.bold('\n📡 Setting up Jebat channel:', chalk.cyan(channel), '\n'));

  const configPath = path.join(jebatDir, 'jebat-gateway.json');
  let config = {};

  if (await fs.pathExists(configPath)) {
    config = await fs.readJson(configPath);
  } else {
    console.log(chalk.yellow('⚠️  Gateway config not found. Run setup first.'));
    console.log(chalk.dim('   npx create-jebat-app'));
    process.exit(1);
  }

  if (!config.channels) {
    config.channels = {};
  }

  switch (channel) {
    case 'telegram':
    case 'tg':
      await setupTelegram(config);
      break;
    case 'discord':
      await setupDiscord(config);
      break;
    case 'whatsapp':
    case 'wa':
      await setupWhatsApp(config);
      break;
    case 'slack':
      await setupSlack(config);
      break;
    case 'all':
      await setupAllChannels(config);
      break;
    default:
      console.log(chalk.yellow('⚠️  Unsupported channel:'), channel);
      console.log(chalk.dim('Supported: telegram, discord, whatsapp, slack, all'));
      process.exit(1);
  }

  // Save config
  await fs.writeJson(configPath, config, { spaces: 2 });

  console.log(chalk.green('\n✅ Channel setup complete!'));
  console.log(chalk.dim('\nRestart Jebat Gateway to apply changes.\n'));
  console.log(chalk.yellow('npx jebat-gateway restart'));
  console.log();
}

async function setupTelegram(config) {
  console.log(chalk.bold('📱 Telegram Setup\n'));

  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'botToken',
      message: 'Bot token from @BotFather:',
      validate: (input) => {
        if (!input || input.length < 10) {
          return 'Please enter a valid bot token';
        }
        return true;
      },
    },
    {
      type: 'confirm',
      name: 'enable',
      message: 'Enable Telegram channel?',
      default: true,
    },
  ]);

  config.channels.telegram = {
    enabled: answers.enable,
    dmPolicy: 'pairing',
    botToken: answers.botToken,
    groupPolicy: 'allowlist',
    streaming: 'partial',
  };

  console.log(chalk.green('✓'), 'Telegram channel configured');
}

async function setupDiscord(config) {
  console.log(chalk.bold('🎮 Discord Setup\n'));

  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'botToken',
      message: 'Discord bot token:',
      validate: (input) => {
        if (!input || input.length < 10) {
          return 'Please enter a valid bot token';
        }
        return true;
      },
    },
    {
      type: 'input',
      name: 'guildId',
      message: 'Server (guild) ID:',
    },
    {
      type: 'confirm',
      name: 'enable',
      message: 'Enable Discord channel?',
      default: true,
    },
  ]);

  config.channels.discord = {
    enabled: answers.enable,
    botToken: answers.botToken,
    guildId: answers.guildId || null,
    streaming: 'partial',
  };

  console.log(chalk.green('✓'), 'Discord channel configured');
}

async function setupWhatsApp(config) {
  console.log(chalk.bold('💬 WhatsApp Setup\n'));

  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'phoneNumberId',
      message: 'Phone number ID (from Meta):',
    },
    {
      type: 'input',
      name: 'accessToken',
      message: 'Access token:',
    },
    {
      type: 'input',
      name: 'verifyToken',
      message: 'Verify token:',
    },
    {
      type: 'confirm',
      name: 'enable',
      message: 'Enable WhatsApp channel?',
      default: true,
    },
  ]);

  config.channels.whatsapp = {
    enabled: answers.enable,
    phoneNumberId: answers.phoneNumberId,
    accessToken: answers.accessToken,
    verifyToken: answers.verifyToken,
  };

  console.log(chalk.green('✓'), 'WhatsApp channel configured');
}

async function setupSlack(config) {
  console.log(chalk.bold('💼 Slack Setup\n'));

  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'botToken',
      message: 'Bot token (xoxb-...):',
    },
    {
      type: 'input',
      name: 'appToken',
      message: 'App token (xapp-...):',
    },
    {
      type: 'confirm',
      name: 'enable',
      message: 'Enable Slack channel?',
      default: true,
    },
  ]);

  config.channels.slack = {
    enabled: answers.enable,
    botToken: answers.botToken,
    appToken: answers.appToken,
  };

  console.log(chalk.green('✓'), 'Slack channel configured');
}

async function setupAllChannels(config) {
  console.log(chalk.bold('📡 Setting up all channels\n'));

  const { channels } = await inquirer.prompt([
    {
      type: 'checkbox',
      name: 'channels',
      message: 'Which channels to enable?',
      choices: [
        { name: 'Telegram', value: 'telegram', checked: true },
        { name: 'Discord', value: 'discord' },
        { name: 'WhatsApp', value: 'whatsapp' },
        { name: 'Slack', value: 'slack' },
      ],
    },
  ]);

  for (const ch of channels) {
    await setupChannel(ch, config);
  }

  console.log(chalk.green('\n✓'), `${channels.length} channels configured`);
}

module.exports = { setupChannel };
