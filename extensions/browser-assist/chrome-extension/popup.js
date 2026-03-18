/**
 * Zero-Employee Browser Assist — Popup Script
 */
document.addEventListener("DOMContentLoaded", () => {
  const serverUrlEl = document.getElementById("serverUrl");
  const apiBaseUrlEl = document.getElementById("apiBaseUrl");
  const userIdEl = document.getElementById("userId");
  const languageEl = document.getElementById("language");
  const saveBtnEl = document.getElementById("saveBtn");
  const saveMsgEl = document.getElementById("saveMsg");
  const connectBtnEl = document.getElementById("connectBtn");
  const statusEl = document.getElementById("status");
  const statusDotEl = document.getElementById("statusDot");
  const statusLabelEl = document.getElementById("statusLabel");

  // Load saved settings
  chrome.storage.sync.get(
    ["serverUrl", "apiBaseUrl", "userId", "language"],
    (items) => {
      if (items.serverUrl) serverUrlEl.value = items.serverUrl;
      if (items.apiBaseUrl) apiBaseUrlEl.value = items.apiBaseUrl;
      if (items.userId) userIdEl.value = items.userId;
      if (items.language) languageEl.value = items.language;
    }
  );

  // Save
  saveBtnEl.addEventListener("click", () => {
    chrome.storage.sync.set(
      {
        serverUrl: serverUrlEl.value,
        apiBaseUrl: apiBaseUrlEl.value,
        userId: userIdEl.value,
        language: languageEl.value,
      },
      () => {
        saveMsgEl.style.display = "block";
        setTimeout(() => (saveMsgEl.style.display = "none"), 2000);
      }
    );
  });

  // Connect
  connectBtnEl.addEventListener("click", () => {
    chrome.runtime.sendMessage({ type: "connect" });
  });

  // Listen for status updates
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "ws_connected") {
      statusEl.className = "status connected";
      statusDotEl.className = "dot on";
      statusLabelEl.textContent = "Connected";
      connectBtnEl.textContent = "Reconnect";
    } else if (msg.type === "ws_disconnected") {
      statusEl.className = "status disconnected";
      statusDotEl.className = "dot off";
      statusLabelEl.textContent = "Disconnected";
      connectBtnEl.textContent = "Connect";
    }
  });
});
