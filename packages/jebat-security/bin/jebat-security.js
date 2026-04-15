#!/usr/bin/env node
const BANNER = `
  __  __    ___    _____   _    ____      ____   ____   _   _    ____  
 |  \\/  |  / _ \\  | ____| | |  / ___|    / ___| / ___| | \\ | |  / ___| 
 | |\\/| | | | | | |  _|   | | | |       | |  _  | |   |  \\| | | |  _  
 | |  | | | |_| | | |___  | | | |___    | |_| | | |___ | |\\  | | |_| | 
 |_|  |_|  \\___/  |_____| |_|  \\____|    \\____|  \\____||_| \\_|  \\____| 
                                                                       
                          Security CLI v1.0.4
`;
const COMMANDS = {
  audit: { desc: "Run Hulubalang security audit", usage: "jebat-security audit [target]" },
  scan: { desc: "Run Pengawal vulnerability scan", usage: "jebat-security scan [target]" },
  harden: { desc: "Run Perisai system hardening", usage: "jebat-security harden [target]" },
  pentest: { desc: "Run Serangan penetration test", usage: "jebat-security pentest [target]" },
  report: { desc: "Generate security report", usage: "jebat-security report [session-id]" },
  status: { desc: "Check security system status", usage: "jebat-security status" },
  init: { desc: "Initialize security workspace", usage: "jebat-security init" },
};
function printHelp() {
  console.log(BANNER);
  console.log("Enterprise security CLI for JEBAT AI Platform\n");
  console.log("Usage:");
  console.log("  jebat-security <command> [options]\n");
  console.log("Commands:");
  Object.entries(COMMANDS).forEach(([cmd, info]) => {
    console.log(`  ${cmd.padEnd(12)} ${info.desc}`);
    console.log(`                 ${info.usage}\n`);
  });
  console.log("Security Suite:");
  console.log("  🔍 Hulubalang   - Security audit & compliance");
  console.log("  🛡️  Pengawal     - CyberSec defense & scanning");
  console.log("  🔒 Perisai      - System hardening & compliance");
  console.log("  ⚔️  Serangan     - Penetration testing & red team");
  console.log("\nLearn more: https://jebat.online/security");
}
function runCommand(cmd) {
  const c = COMMANDS[cmd];
  if (!c) { console.error(`Unknown command: ${cmd}\nRun 'jebat-security --help' for usage.`); process.exit(1); }
  console.log(BANNER);
  console.log(`\n🚀 Running: ${c.desc}`);
  console.log(`📋 Command: ${c.usage}`);
  console.log("\n" + "─".repeat(50));
  console.log(`\n✅ ${cmd} command ready`);
  console.log(`📖 Full documentation: https://jebat.online/security`);
  console.log(`🔧 API: https://jebat.online/api/v1/security/*`);
}
const cmd = process.argv[2];
if (!cmd || cmd === "--help" || cmd === "-h") { printHelp(); process.exit(0); }
if (cmd === "--version" || cmd === "-v") { console.log("jebat-security@1.0.4"); process.exit(0); }
runCommand(cmd);
