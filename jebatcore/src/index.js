/**
 * JEBATCore — main module export.
 *
 * Exports the MCP client adapter and bootstrap installer.
 *
 * Usage:
 *   const { JebatMCPClient, bootstrap } = require('jebatcore');
 *   const info = await bootstrap();
 *   const client = new JebatMCPClient({ transport: 'stdio' });
 *   await client.connect();
 */

const { JebatMCPClient } = require("./mcp-client");
const { bootstrap, findPython, isInstalled } = require("./bootstrap");

module.exports = {
  JebatMCPClient,
  bootstrap,
  findPython,
  isInstalled,
};