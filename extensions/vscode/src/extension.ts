/**
 * Zero-Employee Orchestrator — VS Code extension entry point.
 *
 * Minimal v0.1.7 scaffold:
 *
 *   - `zeo.openChat`                  — open the web UI at the configured endpoint
 *   - `zeo.createTicketFromSelection` — POST the current editor selection as a ticket
 *   - `zeo.listTickets`               — quick-pick of in-progress tickets
 *   - `zeo.killSwitch`                — engage the global kill switch via REST
 *
 * The extension does NOT bundle the ZEO daemon. It assumes `zero-employee serve`
 * is already running on the `zeo.endpoint` setting (default http://localhost:18234).
 *
 * MCP bridge:
 *   For multi-tool chat sessions, point your MCP-compatible IDE plugin at the
 *   stdio transport exposed by `zero-employee mcp serve`. This extension does not
 *   re-implement that transport; it focuses on ergonomic VS Code affordances.
 */

import * as vscode from 'vscode';

interface Ticket {
  id: string;
  ticket_no: number;
  title: string;
  status: string;
}

function getEndpoint(): string {
  return vscode.workspace
    .getConfiguration('zeo')
    .get<string>('endpoint', 'http://localhost:18234');
}

async function zeoFetch(path: string, init?: RequestInit): Promise<Response> {
  const url = `${getEndpoint()}${path}`;
  return fetch(url, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  });
}

async function ensureSession(): Promise<string | null> {
  try {
    const resp = await zeoFetch('/api/v1/auth/anonymous-session', { method: 'POST' });
    if (!resp.ok) return null;
    const data = (await resp.json()) as { access_token?: string };
    return data.access_token ?? null;
  } catch (err) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------

async function openChat(): Promise<void> {
  const endpoint = getEndpoint();
  // The web UI runs separately on port 5173 by convention; fall back to 18234.
  const webUi = endpoint.replace(/:\d+$/, ':5173');
  await vscode.env.openExternal(vscode.Uri.parse(webUi));
}

async function createTicketFromSelection(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage('ZEO: open a file and select text before dispatching.');
    return;
  }
  const selection = editor.document.getText(editor.selection).trim();
  if (!selection) {
    vscode.window.showWarningMessage('ZEO: select a non-empty range first.');
    return;
  }

  const token = await ensureSession();
  if (!token) {
    vscode.window.showErrorMessage(
      `ZEO: could not reach the daemon at ${getEndpoint()}. Start it with \`zero-employee serve\`.`,
    );
    return;
  }

  const title = await vscode.window.showInputBox({
    prompt: 'Ticket title',
    value: selection.split('\n', 1)[0]?.slice(0, 80) ?? '',
  });
  if (!title) return;

  try {
    const resp = await zeoFetch('/api/v1/tickets', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        title,
        description: selection,
        priority: 'medium',
        source: 'vscode-extension',
      }),
    });
    if (!resp.ok) {
      const text = await resp.text();
      vscode.window.showErrorMessage(`ZEO: ticket creation failed (${resp.status}): ${text}`);
      return;
    }
    const ticket = (await resp.json()) as Ticket;
    vscode.window.showInformationMessage(
      `ZEO ticket #${ticket.ticket_no} created — ${ticket.status}.`,
    );
  } catch (err) {
    vscode.window.showErrorMessage(`ZEO: unreachable — ${String(err)}`);
  }
}

async function listTickets(): Promise<void> {
  const token = await ensureSession();
  if (!token) {
    vscode.window.showErrorMessage(
      `ZEO: could not reach the daemon at ${getEndpoint()}. Start it with \`zero-employee serve\`.`,
    );
    return;
  }
  try {
    const resp = await zeoFetch('/api/v1/tickets?status=in_progress', {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resp.ok) {
      vscode.window.showErrorMessage(`ZEO: failed to fetch tickets (${resp.status}).`);
      return;
    }
    const tickets = (await resp.json()) as Ticket[];
    if (tickets.length === 0) {
      vscode.window.showInformationMessage('ZEO: no in-progress tickets.');
      return;
    }
    const picked = await vscode.window.showQuickPick(
      tickets.map((t) => ({
        label: `#${t.ticket_no}`,
        description: t.title,
        detail: `status: ${t.status}`,
        ticket: t,
      })),
      { placeHolder: 'Select a ticket to open in the web UI' },
    );
    if (picked) {
      const webUi = getEndpoint().replace(/:\d+$/, ':5173');
      await vscode.env.openExternal(vscode.Uri.parse(`${webUi}/tickets/${picked.ticket.id}`));
    }
  } catch (err) {
    vscode.window.showErrorMessage(`ZEO: unreachable — ${String(err)}`);
  }
}

async function killSwitch(): Promise<void> {
  const confirm = await vscode.window.showWarningMessage(
    'Engage the ZEO kill switch? All running agent tasks will be halted.',
    { modal: true },
    'Engage',
  );
  if (confirm !== 'Engage') return;

  const token = await ensureSession();
  if (!token) {
    vscode.window.showErrorMessage('ZEO: daemon not reachable.');
    return;
  }
  try {
    const resp = await zeoFetch('/api/v1/kill-switch/engage', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ reason: 'engaged from VS Code extension' }),
    });
    if (resp.ok) {
      vscode.window.showInformationMessage('ZEO: kill switch engaged.');
    } else {
      vscode.window.showErrorMessage(`ZEO: kill-switch call failed (${resp.status}).`);
    }
  } catch (err) {
    vscode.window.showErrorMessage(`ZEO: ${String(err)}`);
  }
}

// ---------------------------------------------------------------------------
// Activation
// ---------------------------------------------------------------------------

export function activate(context: vscode.ExtensionContext): void {
  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  status.text = '$(rocket) ZEO';
  status.tooltip = 'Zero-Employee Orchestrator';
  status.command = 'zeo.openChat';
  status.show();
  context.subscriptions.push(status);

  context.subscriptions.push(
    vscode.commands.registerCommand('zeo.openChat', openChat),
    vscode.commands.registerCommand('zeo.createTicketFromSelection', createTicketFromSelection),
    vscode.commands.registerCommand('zeo.listTickets', listTickets),
    vscode.commands.registerCommand('zeo.killSwitch', killSwitch),
  );
}

export function deactivate(): void {
  // Nothing to clean up — the extension holds no long-lived connections.
}
