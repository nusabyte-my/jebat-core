import readline from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";

export async function withPrompt(fn) {
  const rl = readline.createInterface({ input, output });
  try {
    return await fn(rl);
  } finally {
    rl.close();
  }
}

export async function askText(rl, label, fallback = "") {
  const suffix = fallback ? ` [${fallback}]` : "";
  const answer = (await rl.question(`${label}${suffix}: `)).trim();
  return answer || fallback;
}

export async function chooseOne(rl, label, options, fallbackKey = "") {
  output.write(`\n${label}\n`);
  options.forEach((option, index) => {
    output.write(`  ${index + 1}) ${option.name}\n`);
  });
  const fallbackIndex = fallbackKey ? options.findIndex((option) => option.key === fallbackKey) + 1 : 0;
  const answer = await askText(rl, "Choose one", fallbackIndex ? String(fallbackIndex) : "");
  const parsed = Number.parseInt(answer, 10);
  if (Number.isNaN(parsed) || parsed < 1 || parsed > options.length) {
    throw new Error(`Invalid selection: ${answer}`);
  }
  return options[parsed - 1].key;
}

export async function chooseMany(rl, label, options) {
  output.write(`\n${label}\n`);
  options.forEach((option, index) => {
    const detected = option.detected ? " (detected)" : "";
    const recommended = option.recommendedMode ? ` [suggest ${option.recommendedMode}]` : "";
    output.write(`  ${index + 1}) ${option.name}${detected}${recommended}\n`);
  });
  output.write("  a) all\n");
  const answer = await askText(rl, "Choose number(s) or a", "a");
  if (answer.toLowerCase() === "a") {
    return options.map((option) => option.key);
  }
  const selected = [];
  for (const token of answer.replaceAll(",", " ").split(/\s+/).filter(Boolean)) {
    const parsed = Number.parseInt(token, 10);
    if (!Number.isNaN(parsed) && parsed >= 1 && parsed <= options.length) {
      selected.push(options[parsed - 1].key);
    }
  }
  if (!selected.length) {
    throw new Error("No IDEs selected.");
  }
  return [...new Set(selected)];
}

export async function askYesNo(label, defaultValue = true) {
  const rl = readline.createInterface({ input, output });
  try {
    const defaultStr = defaultValue ? "Y/n" : "y/N";
    const answer = (await rl.question(`${label} [${defaultStr}]: `)).trim().toLowerCase();
    if (answer === "") return defaultValue;
    return answer === "y" || answer === "yes";
  } finally {
    rl.close();
  }
}
