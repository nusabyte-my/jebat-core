#!/usr/bin/env node
const BANNER = `
   ██████╗ ██████╗ ██████╗ ████████╗    ██╗     ██╗ ██████╗ ██╗  ██╗
  ██╔════╝██╔═══██╗██╔══██╗╚══██╔══╝    ██║     ██║██╔════╝ ██║  ██║
  ██║     ██║   ██║██║  ██║   ██║       ██║     ██║██║  ███╗███████║
  ██║     ██║   ██║██║  ██║   ██║       ██║     ██║██║   ██║██╔══██║
  ╚██████╗╚██████╔╝██████╔╝   ██║       ███████╗██║╚██████╔╝██║  ██║
   ╚═════╝ ╚═════╝ ╚═════╝    ╚═╝       ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝
                      Arena CLI v1.0.0
`;
const COMMANDS = {
  debate: { desc: "Start LLM-to-LLM debate", usage: "jebat-gelanggang debate <topic>" },
  consensus: { desc: "Start consensus building", usage: "jebat-gelanggang consensus <topic>" },
  sequential: { desc: "Start sequential chain", usage: "jebat-gelanggang sequential <topic>" },
  parallel: { desc: "Start parallel analysis", usage: "jebat-gelanggang parallel <topic>" },
  hierarchical: { desc: "Start hierarchical review", usage: "jebat-gelanggang hierarchical <topic>" },
  status: { desc: "Check arena status", usage: "jebat-gelanggang status" },
  init: { desc: "Initialize arena workspace", usage: "jebat-gelanggang init" },
};
function printHelp() {
  console.log(BANNER);
  console.log("LLM-to-LLM Arena CLI for JEBAT AI Platform\n");
  console.log("Usage:");
  console.log("  jebat-gelanggang <command> [options]\n");
  console.log("Commands:");
  Object.entries(COMMANDS).forEach(([cmd, info]) => {
    console.log(`  ${cmd.padEnd(14)} ${info.desc}`);
    console.log(`                 ${info.usage}\n`);
  });
  console.log("Orchestration Modes:");
  console.log("  ⚖️  Debate       - Advocate vs Critic → Moderator");
  console.log("  🤝  Consensus    - Collaborative agreement");
  console.log("  🔗  Sequential   - Linear knowledge building");
  console.log("  ⚡  Parallel     - Independent analysis");
  console.log("  🏛️  Hierarchical - Senior delegates to Junior");
  console.log("\nLearn more: https://jebat.online/gelanggang");
}
function runCommand(cmd) {
  const c = COMMANDS[cmd];
  if (!c) { console.error(`Unknown command: ${cmd}\nRun 'jebat-gelanggang --help' for usage.`); process.exit(1); }
  console.log(BANNER);
  console.log(`\n🚀 Running: ${c.desc}`);
  console.log(`📋 Command: ${c.usage}`);
  console.log("\n" + "─".repeat(50));
  console.log(`\n✅ ${cmd} command ready`);
  console.log(`📖 Full documentation: https://jebat.online/gelanggang`);
}
const cmd = process.argv[2];
if (!cmd || cmd === "--help" || cmd === "-h") { printHelp(); process.exit(0); }
if (cmd === "--version" || cmd === "-v") { console.log("jebat-gelanggang@1.0.0"); process.exit(0); }
runCommand(cmd);
