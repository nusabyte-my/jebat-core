const fs = require('fs-extra');
const path = require('path');
const os = require('os');
const chalk = require('chalk');
const { execa } = require('execa');

const homeDir = os.homedir();
const jebatDir = path.join(homeDir, '.jebat');

async function setupLocalModel(model, options = {}) {
  console.log(chalk.bold('\n🤖 Setting up local model:', chalk.cyan(model), '\n'));

  const modelsDir = path.join(jebatDir, 'models');
  const binDir = path.join(jebatDir, 'bin');
  
  await fs.ensureDir(modelsDir);
  await fs.ensureDir(binDir);

  const modelConfig = getModelConfig(model);
  
  if (!modelConfig) {
    console.log(chalk.red('❌ Unknown model:'), model);
    console.log(chalk.dim('Available: qwen2.5, phi3, hermes3, gemma4, all'));
    process.exit(1);
  }

  console.log(chalk.blue('Model:'), modelConfig.name);
  console.log(chalk.blue('Backend:'), modelConfig.backend);
  console.log(chalk.blue('Size:'), modelConfig.size);
  console.log();

  if (modelConfig.backend === 'ollama') {
    await setupOllama(modelConfig);
  } else {
    await setupAirLLM(modelConfig, modelsDir);
  }

  // Update gateway config
  await updateGatewayConfig(modelConfig);

  console.log(chalk.green('\n✅ Local model setup complete!'));
  console.log(chalk.dim('\nStart with:'));
  console.log(chalk.cyan(`  npx jebat-agent start-local ${model}`));
  console.log(chalk.cyan(`  curl http://localhost:8080/health`));
  console.log();
}

function getModelConfig(model) {
  const models = {
    'qwen2.5': {
      name: 'Qwen2.5 3B',
      backend: 'airllm',
      modelId: 'Qwen/Qwen2.5-3B-Instruct',
      size: '~7GB',
      ram: '8GB',
      recommended: true
    },
    'phi3': {
      name: 'Phi-3 Mini',
      backend: 'airllm',
      modelId: 'microsoft/Phi-3-mini-4k-instruct',
      size: '~8GB',
      ram: '8GB',
      recommended: false
    },
    'hermes3': {
      name: 'Hermes3 8B',
      backend: 'airllm',
      modelId: 'NousResearch/Hermes-3-Llama-3.1-8B',
      size: '~16GB',
      ram: '16GB',
      recommended: false
    },
    'gemma4': {
      name: 'Gemma 4',
      backend: 'ollama',
      modelId: 'gemma4',
      size: '~5-9GB',
      ram: '8GB',
      recommended: false
    },
    'all': {
      name: 'All Models',
      backend: 'mixed',
      models: ['qwen2.5', 'phi3', 'hermes3', 'gemma4']
    }
  };

  return models[model] || null;
}

async function setupOllama(modelConfig) {
  console.log(chalk.blue('1/3'), 'Installing Ollama...');

  // Check if Ollama is installed
  try {
    await execa('which', ['ollama']);
    console.log(chalk.green('   ✓'), 'Ollama already installed');
  } catch {
    console.log(chalk.dim('   Downloading Ollama...'));
    await execa('curl', ['-fsSL', 'https://ollama.com/install.sh', '-o', '/tmp/ollama-install.sh']);
    await execa('sudo', ['bash', '/tmp/ollama-install.sh']);
    console.log(chalk.green('   ✓'), 'Ollama installed');
  }

  console.log(chalk.blue('2/3'), 'Starting Ollama service...');
  try {
    await execa('ollama', ['serve'], { timeout: 5000 });
  } catch {
    // Expected to timeout since it runs indefinitely
  }

  console.log(chalk.blue('3/3'), `Downloading ${modelConfig.name}...`);
  console.log(chalk.dim('   This may take a while...'));
  
  await execa('ollama', ['pull', modelConfig.modelId], { stdio: 'inherit' });
  console.log(chalk.green('   ✓'), `${modelConfig.name} downloaded`);
}

async function setupAirLLM(modelConfig, modelsDir) {
  const modelDir = path.join(modelsDir, modelConfig.modelId.split('/').pop().toLowerCase());

  console.log(chalk.blue('1/3'), 'Setting up Python environment...');
  
  const venvDir = path.join(jebatDir, 'venv-llm');
  
  if (!(await fs.pathExists(venvDir))) {
    await execa('python3', ['-m', 'venv', venvDir]);
    console.log(chalk.green('   ✓'), 'Python environment created');
  } else {
    console.log(chalk.green('   ✓'), 'Python environment exists');
  }

  console.log(chalk.blue('2/3'), 'Installing dependencies...');
  
  const pythonPath = path.join(venvDir, 'bin', 'python3');
  const pipPath = path.join(venvDir, 'bin', 'pip');
  
  await execa(pipPath, ['install', '--upgrade', 'pip'], { stdio: 'pipe' });
  await execa(pipPath, ['install', '--quiet', 'airllm', 'torch', 'transformers', 'accelerate', 'bitsandbytes', 'flask']);
  console.log(chalk.green('   ✓'), 'Dependencies installed');

  console.log(chalk.blue('3/3'), `Downloading ${modelConfig.name}...`);
  console.log(chalk.dim('   This may take a while...'));

  const modelPath = path.join(modelDir, 'model');
  
  // Download model
  const downloadScript = `
import os
from transformers import AutoTokenizer
from airllm import AutoModel

model_id = "${modelConfig.modelId}"
model_dir = "${modelPath}"

os.makedirs(model_dir, exist_ok=True)

print("Downloading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=model_dir)

print("Downloading model with 4-bit quantization...")
model = AutoModel.from_pretrained(model_id, cache_dir=model_dir, compression='4bit')

print(f"Model saved to {model_dir}")
`;

  await execa(pythonPath, ['-c', downloadScript], { stdio: 'inherit' });
  console.log(chalk.green('   ✓'), `${modelConfig.name} downloaded`);
}

async function updateGatewayConfig(modelConfig) {
  const configPath = path.join(jebatDir, 'jebat-gateway.json');
  
  if (!(await fs.pathExists(configPath))) {
    console.log(chalk.yellow('⚠'), 'Gateway config not found. Run setup first.');
    return;
  }

  let config = await fs.readJson(configPath);
  
  if (!config.agents) config.agents = {};
  if (!config.agents.defaults) config.agents.defaults = {};
  if (!config.agents.defaults.model) config.agents.defaults.model = {};
  if (!config.agents.defaults.model.providers) config.agents.defaults.model.providers = {};

  // Add local provider
  config.agents.defaults.model.providers.local = {
    endpoint: "http://localhost:8080/v1",
    models: ["qwen2.5-3b", "phi-3-mini", "hermes3-8b", "gemma4"],
    default_model: "qwen2.5-3b",
    api_key: "local"
  };

  // Set primary model
  if (!config.agents.defaults.model.primary?.startsWith('local/')) {
    config.agents.defaults.model.primary = "local/qwen2.5-3b";
    config.agents.defaults.model.fallbacks = [
      "local/phi-3-mini",
      "local/gemma4"
    ];
  }

  await fs.writeJson(configPath, config, { spaces: 2 });
  console.log(chalk.green('✓'), 'Gateway config updated');
}

module.exports = { setupLocalModel };
