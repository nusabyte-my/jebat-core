/**
 * JEBATCore — Python bootstrap installer for Node.js environments.
 *
 * This module handles the "pip install jebat" step programmatically,
 * so IDEs and CI/CD can install JEBAT without manual setup.
 *
 * Usage:
 *   const { bootstrap } = require('./bootstrap');
 *   await bootstrap();  // installs Python jebat if missing
 */

const { execSync } = require("child_process");

const JEBAT_PKG = "jebat";
const MIN_PYTHON = "3.10";

function findPython() {
  const candidates = ["python3", "python", "py"];
  for (const cmd of candidates) {
    try {
      const v = execSync(`${cmd} --version`, { encoding: "utf8", stdio: "pipe" });
      const m = v.match(/Python (\d+\.\d+)/);
      if (m && parseFloat(m[1]) >= parseFloat(MIN_PYTHON)) return cmd;
    } catch { continue; }
  }
  return null;
}

function isInstalled(python) {
  try {
    execSync(`${python} -c "import jebat"`, { stdio: "pipe" });
    return true;
  } catch { return false; }
}

/**
 * Bootstrap JEBAT — find Python, install jebat package if missing.
 * @param {Object} opts - { python?: string, quiet?: boolean }
 * @returns {{ python: string, installed: boolean, version: string }}
 */
function bootstrap(opts = {}) {
  const python = opts.python || findPython();
  if (!python) {
    throw new Error(`Python ${MIN_PYTHON}+ not found. Install Python first.`);
  }

  let installed = isInstalled(python);
  if (!installed) {
    if (!opts.quiet) console.log(`[jebatcore] Installing JEBAT via pip...`);
    execSync(`${python} -m pip install --upgrade ${JEBAT_PKG}`, { stdio: opts.quiet ? "pipe" : "inherit" });
    installed = true;
  }

  // Get installed version
  let version = "unknown";
  try {
    version = execSync(`${python} -c "import jebat; print(jebat.__version__)"`, { encoding: "utf8", stdio: "pipe" }).trim();
  } catch {}

  if (!opts.quiet) console.log(`[jebatcore] JEBAT v${version} ready (${python})`);
  return { python, installed, version };
}

module.exports = { bootstrap, findPython, isInstalled };