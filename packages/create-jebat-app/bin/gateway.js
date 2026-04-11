#!/usr/bin/env node

const chalk = require('chalk');
const { execa } = require('execa');
const os = require('os');
const path = require('path');

const homeDir = os.homedir();
const jebatDir = path.join(homeDir, '.jebat');

async function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'start';

  switch (command) {
    case 'start':
      await startGateway();
      break;
    case 'stop':
      await stopGateway();
      break;
    case 'restart':
      await restartGateway();
      break;
    case 'status':
      await showStatus();
      break;
    case 'logs':
      await showLogs();
      break;
    default:
      console.log(chalk.yellow('Unknown command:'), command);
      console.log(chalk.dim('\nUsage: npx jebat-gateway <command>'));
      console.log(chalk.dim('Commands: start, stop, restart, status, logs\n'));
  }
}

async function startGateway() {
  console.log(chalk.bold('\n🚀 Starting Jebat Gateway...\n'));

  const configPath = path.join(jebatDir, 'jebat-gateway.json');
  
  try {
    const { default: fs } = await import('fs-extra');
    if (!(await fs.pathExists(configPath))) {
      console.log(chalk.yellow('⚠️  Config not found. Running setup...\n'));
      await execa('npx', ['create-jebat-app', '--quick'], { stdio: 'inherit' });
    }
  } catch (e) {
    // fs-extra might not be available
  }

  console.log(chalk.green('✓'), 'Starting gateway server...');
  console.log(chalk.dim('Press Ctrl+C to stop\n'));

  try {
    // Try to find the repo
    const repoRoot = findRepoRoot();
    if (repoRoot) {
      const serverPath = path.join(repoRoot, 'apps', 'api', 'services', 'webui', 'webui_server.py');
      await execa('python', [serverPath], { stdio: 'inherit' });
    } else {
      console.log(chalk.yellow('⚠️  Jebat repository not found'));
      console.log(chalk.dim('Clone from: https://github.com/nusabyte-my/jebat-core'));
    }
  } catch (error) {
    console.error(chalk.red('Error starting gateway:'), error.message);
    process.exit(1);
  }
}

async function stopGateway() {
  console.log(chalk.bold('\n🛑 Stopping Jebat Gateway...\n'));
  
  try {
    await execa('pkill', ['-f', 'webui_server.py']);
    console.log(chalk.green('✓'), 'Gateway stopped');
  } catch (error) {
    console.log(chalk.yellow('⚠️  Gateway not running or could not stop'));
  }
}

async function restartGateway() {
  await stopGateway();
  await new Promise(resolve => setTimeout(resolve, 1000));
  await startGateway();
}

async function showStatus() {
  console.log(chalk.bold('\n📊 Jebat Gateway Status\n'));

  // Check config
  const configPath = path.join(jebatDir, 'jebat-gateway.json');
  try {
    const { default: fs } = await import('fs-extra');
    if (await fs.pathExists(configPath)) {
      console.log(chalk.green('✓'), 'Config exists');
    } else {
      console.log(chalk.yellow('⚠️'), 'Config not found');
    }
  } catch (e) {
    console.log(chalk.yellow('⚠️'), 'Could not check config');
  }

  // Check if running
  try {
    await execa('pgrep', ['-f', 'webui_server.py']);
    console.log(chalk.green('✓'), 'Gateway is running');
  } catch (e) {
    console.log(chalk.red('✗'), 'Gateway is not running');
  }

  // Check workspace
  const workspacePath = path.join(jebatDir, 'workspace');
  try {
    const { default: fs } = await import('fs-extra');
    if (await fs.pathExists(workspacePath)) {
      console.log(chalk.green('✓'), 'Workspace exists');
    } else {
      console.log(chalk.yellow('⚠️'), 'Workspace not found');
    }
  } catch (e) {
    console.log(chalk.yellow('⚠️'), 'Could not check workspace');
  }

  console.log();
}

async function showLogs() {
  console.log(chalk.bold('\n📋 Jebat Gateway Logs\n'));
  
  // Placeholder - in real implementation, would tail log files
  console.log(chalk.dim('Log file: ~/.jebat/gateway.log'));
  console.log(chalk.dim('Run: tail -f ~/.jebat/gateway.log\n'));
}

function findRepoRoot() {
  let current = process.cwd();
  while (current !== '/') {
    if (require('fs').existsSync(path.join(current, 'package.json'))) {
      return current;
    }
    current = path.dirname(current);
  }
  return null;
}

main().catch(console.error);
