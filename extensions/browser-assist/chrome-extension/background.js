/**
 * Zero-Employee Browser Assist — Background Service Worker
 *
 * WebSocket connection to the backend and message relay between
 * content scripts and the API server.
 */

let ws = null;
let serverUrl = "ws://localhost:18234/ws/browser-assist";
let apiBaseUrl = "http://localhost:18234/api/v1";
let reconnectTimer = null;
const RECONNECT_INTERVAL = 5000;

// Load settings from storage
chrome.storage.sync.get(["serverUrl", "apiBaseUrl"], (items) => {
  if (items.serverUrl) serverUrl = items.serverUrl;
  if (items.apiBaseUrl) apiBaseUrl = items.apiBaseUrl;
});

// Listen for settings changes
chrome.storage.onChanged.addListener((changes) => {
  if (changes.serverUrl) serverUrl = changes.serverUrl.newValue;
  if (changes.apiBaseUrl) apiBaseUrl = changes.apiBaseUrl.newValue;
});

function connectWebSocket() {
  if (ws && ws.readyState === WebSocket.OPEN) return;

  try {
    ws = new WebSocket(serverUrl);

    ws.onopen = () => {
      console.log("[ZEO] WebSocket connected");
      clearTimeout(reconnectTimer);
      broadcastToTabs({ type: "ws_connected" });
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        broadcastToTabs({ type: "ws_message", data });
      } catch (e) {
        console.error("[ZEO] Failed to parse WS message:", e);
      }
    };

    ws.onclose = () => {
      console.log("[ZEO] WebSocket disconnected, scheduling reconnect");
      broadcastToTabs({ type: "ws_disconnected" });
      scheduleReconnect();
    };

    ws.onerror = (err) => {
      console.error("[ZEO] WebSocket error:", err);
    };
  } catch (e) {
    console.error("[ZEO] Failed to connect WebSocket:", e);
    scheduleReconnect();
  }
}

function scheduleReconnect() {
  if (reconnectTimer) clearTimeout(reconnectTimer);
  reconnectTimer = setTimeout(connectWebSocket, RECONNECT_INTERVAL);
}

function broadcastToTabs(message) {
  chrome.tabs.query({}, (tabs) => {
    for (const tab of tabs) {
      chrome.tabs.sendMessage(tab.id, message).catch(() => {});
    }
  });
}

// Handle messages from content scripts / popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "connect") {
    connectWebSocket();
    sendResponse({ status: "connecting" });
    return true;
  }

  if (message.type === "disconnect") {
    if (ws) ws.close();
    ws = null;
    sendResponse({ status: "disconnected" });
    return true;
  }

  if (message.type === "send_chat") {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message.data));
      sendResponse({ status: "sent" });
    } else {
      sendResponse({ status: "error", error: "Not connected" });
    }
    return true;
  }

  if (message.type === "capture_and_analyze") {
    // Capture visible tab and send for analysis
    chrome.tabs.captureVisibleTab(null, { format: "png" }, (dataUrl) => {
      if (chrome.runtime.lastError) {
        sendResponse({ status: "error", error: chrome.runtime.lastError.message });
        return;
      }
      const base64 = dataUrl.replace(/^data:image\/png;base64,/, "");
      // Send via REST API
      fetch(`${apiBaseUrl}/browser-assist/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: message.userId || "extension_user",
          action: message.action || "analyze_screen",
          screenshot_base64: base64,
          user_question: message.question,
          target_url: message.url || "",
          browser: "chrome",
          language: message.language || "ja",
        }),
      })
        .then((r) => r.json())
        .then((data) => sendResponse({ status: "ok", data }))
        .catch((err) => sendResponse({ status: "error", error: err.message }));
    });
    return true; // async response
  }

  if (message.type === "send_to_ws") {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message.data));
      sendResponse({ status: "sent" });
    } else {
      sendResponse({ status: "not_connected" });
    }
    return true;
  }
});

// Auto-connect on install
chrome.runtime.onInstalled.addListener(() => {
  console.log("[ZEO] Extension installed");
});
