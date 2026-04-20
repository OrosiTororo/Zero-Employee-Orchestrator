# Zero-Employee Orchestrator — VS Code Extension

In-editor bridge to a locally-running Zero-Employee Orchestrator (ZEO) daemon.
The extension focuses on small, non-intrusive affordances so you never feel
like the editor is "taking over" — every dispatch goes through ZEO's own
approval gate + audit trail.

## What this extension does

| Command                             | What it does                                                                 |
|-------------------------------------|------------------------------------------------------------------------------|
| `ZEO: Open Chat`                    | Opens the ZEO web UI in a browser (default `http://localhost:5173`).         |
| `ZEO: Create Ticket from Selection` | Sends the current editor selection as a ZEO ticket. Status-bar notification. |
| `ZEO: Show Active Tickets`          | Quick-pick of in-progress tickets; selecting one opens it in the web UI.     |
| `ZEO: Engage Kill Switch`           | Halts every running agent task. Requires modal confirmation.                 |

## What this extension does *not* do

- Bundle the ZEO daemon. Start it separately (`zero-employee serve`).
- Send editor content to a remote LLM on its own. All LLM routing goes through
  the ZEO daemon, which enforces the operator's configured provider + autonomy
  level.
- Re-implement an MCP client. For multi-tool chat, point your MCP-compatible
  IDE plugin at `zero-employee mcp serve` (stdio transport).

## Configuration

Settings live under `zeo.*`:

```jsonc
{
  "zeo.endpoint": "http://localhost:18234",
  "zeo.autonomyLevel": "supervised",
  "zeo.showApprovalInStatusBar": true
}
```

## Build

```bash
cd extensions/vscode
pnpm install
pnpm run package   # produces dist/*.vsix
```

Then `Extensions: Install from VSIX…` in VS Code, point at the `.vsix`, done.

## Status

**Experimental.** Shipped in v0.1.7 as the scaffold the community can iterate on;
the distributed Marketplace listing lands in a follow-up release.
