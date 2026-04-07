import { existsSync } from "node:fs";
import { delimiter } from "node:path";
import { env, platform } from "node:process";
import { IDES } from "./constants.js";

function inPath(executable) {
  const pathValue = env.PATH || "";
  const exts = platform === "win32" ? [".exe", ".cmd", ".bat", ""] : [""];
  for (const dir of pathValue.split(delimiter)) {
    if (!dir) continue;
    for (const ext of exts) {
      if (existsSync(`${dir}/${executable}${ext}`)) {
        return true;
      }
    }
  }
  return false;
}

function detectJetBrains() {
  return [
    "idea64",
    "webstorm",
    "pycharm64",
    "goland",
    "phpstorm64",
    "rubymine64"
  ].some(inPath);
}

const detectors = {
  vscode: () => inPath("code"),
  cursor: () => inPath("cursor"),
  windsurf: () => inPath("windsurf"),
  zed: () => inPath("zed"),
  jetbrains: () => detectJetBrains(),
  neovim: () => inPath("nvim"),
  sublime: () => inPath("subl") || inPath("sublime_text"),
  vscodium: () => inPath("codium"),
  trae: () => inPath("trae"),
  antigravity: () => inPath("antigravity")
};

export function detectIdes() {
  return IDES.map((ide) => ({
    ...ide,
    detected: detectors[ide.key] ? detectors[ide.key]() : false
  }));
}
