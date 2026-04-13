#!/usr/bin/env node
const BANNER = `
   ██████╗ ██████╗ ██████╗ ████████╗    ██╗      ██████╗  █████╗ ██████╗ ██╗   ██╗
  ██╔════╝██╔═══██╗██╔══██╗╚══██╔══╝    ██║     ██╔═══██╗██╔══██╗██╔══██╗██║   ██║
  ██║     ██║   ██║██║  ██║   ██║       ██║     ██║   ██║███████║██║  ██║██║   ██║
  ██║     ██║   ██║██║  ██║   ██║       ██║     ██║   ██║██╔══██║██║  ██║██║   ██║
  ╚██████╗╚██████╔╝██████╔╝   ██║       ███████╗╚██████╔╝██║  ██║██████╔╝╚██████╔╝
   ╚═════╝ ╚═════╝ ╚═════╝    ╚═╝       ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝  ╚═════╝
                       Guides CLI v1.0.0
`;
const COMMANDS = {
  setup: { desc: "Quick setup guide", usage: "jebat-guides setup" },
  ide: { desc: "IDE integration guide", usage: "jebat-guides ide" },
  models: { desc: "Local LLM deployment guide", usage: "jebat-guides models" },
  channels: { desc: "Channel setup guide", usage: "jebat-guides channels" },
  migrate: { desc: "Migration guide", usage: "jebat-guides migrate" },
  security: { desc: "Security hardening guide", usage: "jebat-guides security" },
};
function printHelp() {
  console.log(BANNER);
  console.log("Setup & Deployment Guides CLI for JEBAT AI Platform\n");
  console.log("Usage:");
  console.log("  jebat-guides <command>\n");
  console.log("Commands:");
  Object.entries(COMMANDS).forEach(([cmd, info]) => {
    console.log(`  ${cmd.padEnd(12)} ${info.desc}`);
    console.log(`                 ${info.usage}\n`);
  });
  console.log("Learn more: https://jebat.online/guides");
}
function runCommand(cmd) {
  const c = COMMANDS[cmd];
  if (!c) { console.error(`Unknown command: ${cmd}\nRun 'jebat-guides --help' for usage.`); process.exit(1); }
  console.log(BANNER);
  console.log(`\n📖 ${c.desc}`);
  console.log(`📋 Command: ${c.usage}`);
  console.log("\n" + "─".repeat(50));
  console.log(`\n✅ ${cmd} guide ready`);
  console.log(`📖 Full documentation: https://jebat.online/guides`);
}
const cmd = process.argv[2];
if (!cmd || cmd === "--help" || cmd === "-h") { printHelp(); process.exit(0); }
if (cmd === "--version" || cmd === "-v") { console.log("jebat-guides@1.0.0"); process.exit(0); }
runCommand(cmd);
