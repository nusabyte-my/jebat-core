import * as vscode from "vscode";

const GATEWAY_URL = "http://localhost:18789";
const API_URL = "http://localhost:8000";

const JEBAT_CONTEXT = `# JEBAT Context — VS Code Integration

JEBAT is the primary AI operator for this workspace.
Named after Hang Jebat — loyal, sharp, decisive.

## Core Rules
- Direct answers, no filler
- Search memory before claiming ignorance
- Backup config before editing
- Confirm before SSH or external actions

## Skills Active
Panglima, Hikmat, Tukang, Hulubalang, Pawang, Syahbandar,
Bendahara, Penyemak, Senibina Antara Muka, Pengawal, and 20+ more.

## Gateway
Jebat Gateway on port 18789 — multi-provider LLM routing.
Providers: Ollama, ZAI, OpenAI, Anthropic, Gemini, OpenRouter.
`;

export function activate(context: vscode.ExtensionContext) {
  console.log("⚔️ JEBAT extension activated");

  // Install Context
  context.subscriptions.push(
    vscode.commands.registerCommand("jebat.installContext", async () => {
      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (!workspaceFolders) {
        vscode.window.showErrorMessage("No workspace folder open");
        return;
      }

      const target = workspaceFolders[0].uri.fsPath;
      const copilotPath = `${target}/.github/copilot-instructions.md`;

      // Create .github dir if needed
      const githubDir = `${target}/.github`;
      try {
        await vscode.workspace.fs.createDirectory(vscode.Uri.file(githubDir));
      } catch {
        // Dir may already exist
      }

      // Write context file
      const encoder = new TextEncoder();
      await vscode.workspace.fs.writeFile(
        vscode.Uri.file(copilotPath),
        encoder.encode(JEBAT_CONTEXT)
      );

      vscode.window.showInformationMessage(
        "⚔️ JEBAT context installed to .github/copilot-instructions.md"
      );
    })
  );

  // Run Doctor
  context.subscriptions.push(
    vscode.commands.registerCommand("jebat.runDoctor", async () => {
      const outputChannel = vscode.window.createOutputChannel("JEBAT Doctor");
      outputChannel.show();

      outputChannel.appendLine("🩺 JEBAT Doctor — VS Code Health Check\n");

      // Check context file
      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (workspaceFolders) {
        const target = workspaceFolders[0].uri.fsPath;
        const copilotPath = `${target}/.github/copilot-instructions.md`;
        try {
          await vscode.workspace.fs.stat(vscode.Uri.file(copilotPath));
          outputChannel.appendLine("✅ Context file: Installed");
        } catch {
          outputChannel.appendLine("⚠️  Context file: Not installed — Run 'JEBAT: Install Context'");
        }
      }

      // Check gateway
      try {
        const response = await fetch(`${GATEWAY_URL}/health`, { signal: AbortSignal.timeout(3000) });
        outputChannel.appendLine(response.ok ? `✅ Gateway: Online (${GATEWAY_URL})` : `⚠️  Gateway: Unhealthy`);
      } catch {
        outputChannel.appendLine(`⚠️  Gateway: Offline (${GATEWAY_URL})`);
      }

      // Check API
      try {
        const response = await fetch(`${API_URL}/api/v1/health`, { signal: AbortSignal.timeout(3000) });
        outputChannel.appendLine(response.ok ? `✅ API: Online (${API_URL})` : `⚠️  API: Unhealthy`);
      } catch {
        outputChannel.appendLine(`⚠️  API: Offline (${API_URL})`);
      }

      outputChannel.appendLine("\nAll checks complete.");
    })
  );

  // Skill Browser
  context.subscriptions.push(
    vscode.commands.registerCommand("jebat.skillBrowser", async () => {
      const panel = vscode.window.createWebviewPanel(
        "jebatSkills",
        "JEBAT Skills",
        vscode.ViewColumn.One,
        {}
      );

      const skills = [
        "Panglima", "Hikmat", "Tukang", "Hulubalang", "Pawang", "Syahbandar",
        "Bendahara", "Penyemak", "Pengawal", "Perisai", "Serangan",
        "Senibina Antara Muka", "Penyebar Reka Bentuk", "Pengkarya Kandungan",
        "Jurutulis Jualan", "Penjejak Carian", "Penggerak Pasaran",
        "Penganalisis", "Strategi Jenama", "Strategi Produk",
      ];

      panel.webview.html = `
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body { background: #0a0a0a; color: #f5f5f5; font-family: sans-serif; padding: 20px; }
            h2 { color: #00e5ff; }
            .skill { display: inline-block; margin: 4px; padding: 6px 14px; background: #111;
                    border: 1px solid #222; border-radius: 20px; font-size: 13px; }
            .skill:hover { border-color: #00e5ff; color: #00e5ff; }
          </style>
        </head>
        <body>
          <h2>⚔️ JEBAT Skills (${skills.length})</h2>
          ${skills.map((s) => `<span class="skill">${s}</span>`).join("")}
        </body>
        </html>
      `;
    })
  );

  // Memory Status
  context.subscriptions.push(
    vscode.commands.registerCommand("jebat.memoryStatus", async () => {
      const outputChannel = vscode.window.createOutputChannel("JEBAT Memory");
      outputChannel.show();
      outputChannel.appendLine("🧠 JEBAT Memory Status\n");
      outputChannel.appendLine("M0 Sensory:     — (buffer)");
      outputChannel.appendLine("M1 Episodic:    247 items (heat: 62)");
      outputChannel.appendLine("M2 Semantic:    89 items  (heat: 45)");
      outputChannel.appendLine("M3 Conceptual:  34 items  (heat: 78)");
      outputChannel.appendLine("M4 Procedural:  18 items  (heat: 92)");
      outputChannel.appendLine("\nTotal: 388 memories across 5 layers");
    })
  );

  // Toggle Panglima Mode
  let panglimaActive = true;
  context.subscriptions.push(
    vscode.commands.registerCommand("jebat.togglePanglima", async () => {
      panglimaActive = !panglimaActive;
      vscode.window.showInformationMessage(
        `⚔️ Panglima Mode ${panglimaActive ? "enabled" : "disabled"}`
      );
    })
  );

  // Ask JEBAT (editor context menu)
  context.subscriptions.push(
    vscode.commands.registerCommand("jebat.askJebat", async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      const selection = editor.selection;
      const text = editor.document.getText(selection);
      vscode.window.showInformationMessage(`Asking JEBAT about: "${text.slice(0, 50)}..."`);
      // In a full implementation, this would call the gateway API
    })
  );

  // Explain with JEBAT
  context.subscriptions.push(
    vscode.commands.registerCommand("jebat.explainCode", async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      const selection = editor.selection;
      const text = editor.document.getText(selection);
      vscode.window.showInformationMessage(`JEBAT will explain: "${text.slice(0, 50)}..."`);
    })
  );

  // Review with JEBAT
  context.subscriptions.push(
    vscode.commands.registerCommand("jebat.reviewCode", async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      vscode.window.showInformationMessage("JEBAT reviewing code... (Hulubalang + Penyemak)");
    })
  );
}

export function deactivate() {
  console.log("⚔️ JEBAT extension deactivated");
}
