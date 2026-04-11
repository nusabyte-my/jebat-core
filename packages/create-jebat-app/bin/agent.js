#!/usr/bin/env node

const chalk = require('chalk');
const { execa } = require('execa');
const os = require('os');
const path = require('path');
const fs = require('fs-extra');

const homeDir = os.homedir();
const jebatDir = path.join(homeDir, '.jebat');

async function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'health';

  switch (command) {
    case 'health':
      await checkHealth();
      break;
    case 'skills':
      await listSkills();
      break;
    case 'test':
      await testAgent();
      break;
    case 'info':
      await showInfo();
      break;
    default:
      console.log(chalk.yellow('Unknown command:'), command);
      console.log(chalk.dim('\nUsage: npx jebat-agent <command>'));
      console.log(chalk.dim('Commands: health, skills, test, info\n'));
  }
}

async function checkHealth() {
  console.log(chalk.bold('\n🏥 Jebat Agent Health Check\n'));

  // Check workspace
  const workspacePath = path.join(jebatDir, 'workspace');
  if (await fs.pathExists(workspacePath)) {
    console.log(chalk.green('✓'), 'Workspace exists');
  } else {
    console.log(chalk.red('✗'), 'Workspace not found');
    console.log(chalk.dim('  Run: npx create-jebat-app --full'));
  }

  // Check skills
  const skillsPath = path.join(workspacePath, 'skills', 'jebat-agent');
  if (await fs.pathExists(skillsPath)) {
    console.log(chalk.green('✓'), 'Jebat Agent skill installed');
  } else {
    console.log(chalk.yellow('⚠️'), 'Jebat Agent skill not found');
  }

  // Check config
  const configPath = path.join(jebatDir, 'jebat-gateway.json');
  if (await fs.pathExists(configPath)) {
    const config = await fs.readJson(configPath);
    const model = config.agents?.defaults?.model?.primary || 'not set';
    console.log(chalk.green('✓'), `Primary model: ${chalk.cyan(model)}`);
  } else {
    console.log(chalk.red('✗'), 'Gateway config not found');
  }

  // Check gateway
  try {
    await execa('pgrep', ['-f', 'webui_server.py']);
    console.log(chalk.green('✓'), 'Gateway is running');
  } catch (e) {
    console.log(chalk.red('✗'), 'Gateway is not running');
    console.log(chalk.dim('  Run: npx jebat-gateway start'));
  }

  console.log();
}

async function listSkills() {
  console.log(chalk.bold('\n🎯 Available Jebat Agent Skills\n'));

  const skillsPath = path.join(jebatDir, 'workspace', 'skills');
  
  if (!(await fs.pathExists(skillsPath))) {
    console.log(chalk.yellow('⚠️  No skills directory found'));
    console.log(chalk.dim('Run: npx create-jebat-app --full'));
    return;
  }

  const skills = await fs.readdir(skillsPath);
  
  for (const skill of skills) {
    const skillFile = path.join(skillsPath, skill, 'SKILL.md');
    if (await fs.pathExists(skillFile)) {
      const content = await fs.readFile(skillFile, 'utf8');
      const nameMatch = content.match(/^name:\s*(.+)$/m);
      const descMatch = content.match(/^description:\s*(.+)$/m);
      
      const name = nameMatch ? nameMatch[1].trim() : skill;
      const desc = descMatch ? descMatch[1].trim() : 'No description';
      
      console.log(chalk.cyan.bold(name));
      console.log(chalk.dim(`  ${desc}\n`));
    }
  }

  console.log(chalk.dim(`Total: ${skills.length} skills\n`));
}

async function testAgent() {
  console.log(chalk.bold('\n🧪 Testing Jebat Agent\n'));

  const configPath = path.join(jebatDir, 'jebat-gateway.json');
  
  if (!(await fs.pathExists(configPath))) {
    console.log(chalk.yellow('⚠️  Gateway config not found'));
    return;
  }

  const config = await fs.readJson(configPath);
  const port = config.gateway?.port || 18789;
  const token = config.gateway?.auth?.token;

  console.log(chalk.blue('Sending test request to gateway...'));

  try {
    const { stdout } = await execa('curl', [
      '-s',
      '-H', `Authorization: Bearer ${token}`,
      `http://localhost:${port}/health`
    ]);

    console.log(chalk.green('✓'), 'Gateway responded');
    console.log(chalk.dim(stdout));
  } catch (error) {
    console.log(chalk.red('✗'), 'Could not reach gateway');
    console.log(chalk.dim('  Make sure gateway is running: npx jebat-gateway start'));
  }

  console.log();
}

async function showInfo() {
  console.log(chalk.bold('\nℹ️  Jebat Agent Information\n'));

  console.log(chalk.cyan.bold('Jebat Agent'));
  console.log(chalk.dim('Version: 1.0.0'));
  console.log(chalk.dim('Author: JEBATCore / NusaByte'));
  console.log();

  console.log(chalk.bold('Description:'));
  console.log('Primary AI agent for the Jebat platform with multi-agent');
  console.log('orchestration, task planning, and execution capabilities.');
  console.log();

  console.log(chalk.bold('Features:'));
  console.log('  • Multi-agent orchestration');
  console.log('  • Task planning and breakdown');
  console.log('  • Code generation and review');
  console.log('  • System administration');
  console.log('  • Research and analysis');
  console.log();

  console.log(chalk.bold('Configuration:'));
  console.log(`  Directory: ${chalk.dim(jebatDir)}`);
  console.log(`  Skills:    ${chalk.dim(path.join(jebatDir, 'workspace', 'skills'))}`);
  console.log();

  console.log(chalk.bold('Resources:'));
  console.log(`  Documentation: ${chalk.cyan('INTEGRATION_GUIDE.md')}`);
  console.log(`  GitHub:        ${chalk.cyan('https://github.com/nusabyte-my/jebat-core')}`);
  console.log();
}

main().catch(console.error);
