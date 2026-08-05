/**
 * JEBAT MCP Client Adapter — connects to JEBAT MCP server from Node.js/IDEs.
 *
 * This is the bridge between IDE MCP clients (VS Code, Cursor, Windsurf, JetBrains)
 * and the JEBAT Python MCP server. It handles:
 * - stdio transport: starts the workspace `jebat-mcp` entry point
 * - HTTP transport: connects to JEBAT MCP server over HTTP/SSE
 * - Streamable HTTP: connects to JEBAT MCP server using MCP 2025-03-26 spec
 *
 * Usage:
 *   const client = new JebatMCPClient({ transport: 'stdio' });
 *   await client.connect();
 *   const tools = await client.listTools();
 *   const result = await client.callTool('web_search', { query: 'test' });
 */

const { Client } = require("@modelcontextprotocol/sdk/client/index.js");
const { StdioClientTransport } = require("@modelcontextprotocol/sdk/client/stdio.js");
const { SSEClientTransport } = require("@modelcontextprotocol/sdk/client/sse.js");
const { StreamableHTTPClientTransport } = require("@modelcontextprotocol/sdk/client/streamableHttp.js");

class JebatMCPClient {
  /**
   * @param {Object} options
   * @param {string} options.transport - 'stdio' | 'http' | 'streamable-http'
   * @param {string} options.command - Command to run for stdio (default: 'python3')
   * @param {string[]} options.args - Args for stdio command (default: ['./jebat-mcp'])
   * @param {string} options.url - URL for HTTP/streamable-http transport
   * @param {number} options.timeout - Request timeout in ms (default: 30000)
   * @param {string} options.env - Extra env vars for stdio subprocess
   */
  constructor(options = {}) {
    this.transportType = options.transport || "stdio";
    this.command = options.command || "python3";
    this.args = options.args || ["./jebat-mcp"];
    this.url = options.url || "http://127.0.0.1:8100/mcp";
    this.timeout = options.timeout || 30000;
    this.env = options.env || {};
    this.client = null;
    this.connected = false;
  }

  /**
   * Connect to the JEBAT MCP server.
   * @returns {Promise<Object>} Server info from initialize handshake
   */
  async connect() {
    let transport;

    if (this.transportType === "stdio") {
      // Spawn JEBAT as subprocess — IDE integration mode
      transport = new StdioClientTransport({
        command: this.command,
        args: this.args,
        env: { ...process.env, ...this.env },
      });
    } else if (this.transportType === "http") {
      // Connect to JEBAT over SSE — remote mode
      transport = new SSEClientTransport(
        new URL(this.url.replace("/mcp", "/sse"))
      );
    } else if (this.transportType === "streamable-http") {
      // Connect to JEBAT using MCP 2025-03-26 Streamable HTTP
      transport = new StreamableHTTPClientTransport(new URL(this.url));
    } else {
      throw new Error(`Unknown transport: ${this.transportType}`);
    }

    this.client = new Client(
      { name: "jebatcore-adapter", version: "0.1.0" },
      { capabilities: {}, timeout: this.timeout }
    );

    const result = await this.client.connect(transport);
    this.connected = true;
    return result;
  }

  /**
   * List all available JEBAT tools.
   * @returns {Promise<Object>} Tool list from server
   */
  async listTools() {
    if (!this.connected) throw new Error("Not connected. Call connect() first.");
    return await this.client.listTools();
  }

  /**
   * Call a JEBAT tool.
   * @param {string} name - Tool name
   * @param {Object} args - Tool arguments
   * @returns {Promise<Object>} Tool result
   */
  async callTool(name, args = {}) {
    if (!this.connected) throw new Error("Not connected. Call connect() first.");
    return await this.client.callTool({ name, arguments: args });
  }

  /**
   * Request LLM completion via MCP sampling (createMessage).
   * Only works if JEBAT server supports sampling.
   * @param {Object[]} messages - Chat messages [{role, content}]
   * @param {number} maxTokens - Max response tokens
   * @param {Object} options - Extra sampling options
   * @returns {Promise<Object>} LLM response
   */
  async createMessage(messages, maxTokens = 4096, options = {}) {
    if (!this.connected) throw new Error("Not connected. Call connect() first.");
    return await this.client.createMessage({
      messages,
      maxTokens,
      ...options,
    });
  }

  /**
   * List available resources from JEBAT.
   * @returns {Promise<Object>} Resource list
   */
  async listResources() {
    if (!this.connected) throw new Error("Not connected. Call connect() first.");
    return await this.client.listResources();
  }

  /**
   * Read a resource from JEBAT.
   * @param {string} uri - Resource URI
   * @returns {Promise<Object>} Resource content
   */
  async readResource(uri) {
    if (!this.connected) throw new Error("Not connected. Call connect() first.");
    return await this.client.readResource({ uri });
  }

  /**
   * Subscribe to resource updates.
   * @param {string} uri - Resource URI to subscribe to
   * @returns {Promise<void>}
   */
  async subscribeResource(uri) {
    if (!this.connected) throw new Error("Not connected. Call connect() first.");
    return await this.client.subscribeResource({ uri });
  }

  /**
   * Disconnect from JEBAT MCP server.
   * @returns {Promise<void>}
   */
  async disconnect() {
    if (this.client && this.connected) {
      await this.client.close();
      this.connected = false;
    }
  }
}

module.exports = { JebatMCPClient };
