/**
 * Zero-Employee Browser Assist — Content Script (Overlay Chat)
 *
 * Injects a floating chat widget on every page. Users can ask AI questions
 * about the current page, attach screenshots or files, and receive guidance
 * without leaving the browser.
 */

(() => {
  "use strict";

  // Prevent double injection
  if (document.getElementById("zeo-overlay-root")) return;

  // ---------- State ----------
  let isOpen = false;
  let isConnected = false;
  let attachments = []; // { name, type, dataUrl }
  let userId = "extension_user";
  let language = "ja";

  // Load settings
  if (typeof chrome !== "undefined" && chrome.storage) {
    chrome.storage.sync.get(["userId", "language"], (items) => {
      if (items.userId) userId = items.userId;
      if (items.language) language = items.language;
    });
  }

  // ---------- DOM ----------
  const root = document.createElement("div");
  root.id = "zeo-overlay-root";

  root.innerHTML = `
    <div id="zeo-chat-window">
      <div id="zeo-chat-header">
        <div>
          <div class="zeo-title">Zero-Employee Assist</div>
          <div class="zeo-status">
            <span class="zeo-status-dot offline" id="zeo-status-dot"></span>
            <span id="zeo-status-text">Disconnected</span>
          </div>
        </div>
        <div class="zeo-header-actions">
          <button class="zeo-header-btn" id="zeo-capture-page-btn" title="Capture page for AI">
            &#128247;
          </button>
          <button class="zeo-header-btn" id="zeo-minimize-btn" title="Close">&#10005;</button>
        </div>
      </div>
      <div id="zeo-chat-messages">
        <div class="zeo-message system">
          AI browser assist is ready. Ask questions about the page you are viewing.
        </div>
      </div>
      <div class="zeo-typing" id="zeo-typing">
        <span></span><span></span><span></span>
      </div>
      <div id="zeo-chat-input-area">
        <div id="zeo-attachment-preview"></div>
        <div id="zeo-chat-input-row">
          <div class="zeo-input-actions">
            <button class="zeo-action-btn" id="zeo-attach-btn" title="Attach image/file">
              &#128206;
            </button>
            <button class="zeo-action-btn" id="zeo-screenshot-btn" title="Send screenshot of this page">
              &#128248;
            </button>
          </div>
          <textarea id="zeo-chat-input" rows="1"
            placeholder="Ask about this page..."></textarea>
          <button class="zeo-action-btn primary" id="zeo-send-btn" title="Send">&#10148;</button>
        </div>
        <input type="file" id="zeo-file-input" multiple
          accept="image/*,.pdf,.txt,.csv,.json,.md,.html">
      </div>
    </div>
    <button id="zeo-toggle-btn" title="Zero-Employee Browser Assist">
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
        <circle cx="8" cy="10" r="1.2"/>
        <circle cx="12" cy="10" r="1.2"/>
        <circle cx="16" cy="10" r="1.2"/>
      </svg>
    </button>
  `;

  document.body.appendChild(root);

  // ---------- Element refs ----------
  const chatWindow = document.getElementById("zeo-chat-window");
  const toggleBtn = document.getElementById("zeo-toggle-btn");
  const minimizeBtn = document.getElementById("zeo-minimize-btn");
  const messagesEl = document.getElementById("zeo-chat-messages");
  const inputEl = document.getElementById("zeo-chat-input");
  const sendBtn = document.getElementById("zeo-send-btn");
  const attachBtn = document.getElementById("zeo-attach-btn");
  const screenshotBtn = document.getElementById("zeo-screenshot-btn");
  const capturePageBtn = document.getElementById("zeo-capture-page-btn");
  const fileInput = document.getElementById("zeo-file-input");
  const attachPreview = document.getElementById("zeo-attachment-preview");
  const typingEl = document.getElementById("zeo-typing");
  const statusDot = document.getElementById("zeo-status-dot");
  const statusText = document.getElementById("zeo-status-text");

  // ---------- Toggle ----------
  toggleBtn.addEventListener("click", () => {
    isOpen = !isOpen;
    chatWindow.classList.toggle("zeo-open", isOpen);
    if (isOpen) {
      inputEl.focus();
      if (!isConnected) connectWS();
    }
  });

  minimizeBtn.addEventListener("click", () => {
    isOpen = false;
    chatWindow.classList.remove("zeo-open");
  });

  // ---------- Connection ----------
  function connectWS() {
    chrome.runtime.sendMessage({ type: "connect" }, () => {});
  }

  function updateConnectionStatus(connected) {
    isConnected = connected;
    statusDot.classList.toggle("offline", !connected);
    statusText.textContent = connected ? "Connected" : "Disconnected";
  }

  // Listen for background messages
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "ws_connected") {
      updateConnectionStatus(true);
    } else if (msg.type === "ws_disconnected") {
      updateConnectionStatus(false);
    } else if (msg.type === "ws_message") {
      handleWSMessage(msg.data);
    }
  });

  function handleWSMessage(data) {
    if (data.type === "assistant_message") {
      hideTyping();
      addMessage("assistant", data.content);
    } else if (data.type === "typing_start") {
      showTyping();
    } else if (data.type === "typing_end") {
      hideTyping();
    } else if (data.type === "error") {
      hideTyping();
      addMessage("system", "Error: " + (data.message || "Unknown error"));
    }
  }

  // ---------- Messages ----------
  function addMessage(role, content, imageUrl) {
    const msgEl = document.createElement("div");
    msgEl.className = `zeo-message ${role}`;

    if (typeof content === "string") {
      msgEl.textContent = content;
    }

    if (imageUrl) {
      const img = document.createElement("img");
      img.src = imageUrl;
      img.alt = "Attached image";
      msgEl.appendChild(img);
    }

    messagesEl.appendChild(msgEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function showTyping() { typingEl.classList.add("active"); }
  function hideTyping() { typingEl.classList.remove("active"); }

  // ---------- Send ----------
  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text && attachments.length === 0) return;

    // Show user message
    if (text) addMessage("user", text);
    for (const a of attachments) {
      if (a.type.startsWith("image/")) {
        addMessage("user", a.name, a.dataUrl);
      } else {
        addMessage("user", `[File: ${a.name}]`);
      }
    }

    const currentAttachments = [...attachments];
    clearAttachments();
    inputEl.value = "";
    inputEl.style.height = "36px";

    showTyping();

    // If we have a screenshot attachment, use REST API for analysis
    const imageAttachment = currentAttachments.find((a) => a.type.startsWith("image/"));

    if (imageAttachment) {
      // Use REST API with screenshot
      const base64 = imageAttachment.dataUrl.replace(/^data:[^;]+;base64,/, "");
      chrome.runtime.sendMessage(
        {
          type: "capture_and_analyze",
          question: text || "Please analyze this image",
          userId,
          language,
          url: window.location.href,
          action: "analyze_screen",
        },
        (response) => {
          hideTyping();
          if (response && response.status === "ok" && response.data) {
            addMessage("assistant", response.data.explanation || "Analysis complete.");
          } else {
            // Fallback: send via WS
            sendViaWS(text, currentAttachments);
          }
        }
      );
    } else {
      sendViaWS(text, currentAttachments);
    }
  }

  function sendViaWS(text, files) {
    const payload = {
      type: "browser_assist_chat",
      content: text,
      url: window.location.href,
      title: document.title,
      user_id: userId,
      language,
      attachments: files.map((f) => ({
        name: f.name,
        type: f.type,
        data: f.dataUrl,
      })),
    };

    chrome.runtime.sendMessage({ type: "send_to_ws", data: payload }, (resp) => {
      if (!resp || resp.status !== "sent") {
        hideTyping();
        // Fallback to REST
        fetchRESTChat(text, files);
      }
    });
  }

  async function fetchRESTChat(text, files) {
    try {
      const apiBase =
        (await new Promise((r) =>
          chrome.storage.sync.get("apiBaseUrl", (i) => r(i.apiBaseUrl))
        )) || "http://localhost:18234/api/v1";

      const body = {
        user_id: userId,
        action: "analyze_screen",
        screenshot_base64: "",
        user_question: text,
        target_url: window.location.href,
        browser: "chrome",
        language,
      };

      // Attach first image if any
      const img = files.find((f) => f.type.startsWith("image/"));
      if (img) {
        body.screenshot_base64 = img.dataUrl.replace(/^data:[^;]+;base64,/, "");
      }

      const res = await fetch(`${apiBase}/browser-assist/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      hideTyping();
      addMessage("assistant", data.explanation || JSON.stringify(data));
    } catch (err) {
      hideTyping();
      addMessage("system", "Failed to connect to server: " + err.message);
    }
  }

  sendBtn.addEventListener("click", sendMessage);

  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Auto-resize input
  inputEl.addEventListener("input", () => {
    inputEl.style.height = "36px";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 80) + "px";
  });

  // ---------- Attachments ----------
  attachBtn.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", () => {
    for (const file of fileInput.files) {
      const reader = new FileReader();
      reader.onload = () => {
        attachments.push({ name: file.name, type: file.type, dataUrl: reader.result });
        renderAttachments();
      };
      reader.readAsDataURL(file);
    }
    fileInput.value = "";
  });

  function renderAttachments() {
    attachPreview.innerHTML = "";
    if (attachments.length === 0) {
      attachPreview.classList.remove("has-files");
      return;
    }
    attachPreview.classList.add("has-files");

    attachments.forEach((a, i) => {
      const item = document.createElement("div");
      item.className = "zeo-attachment-item";

      if (a.type.startsWith("image/")) {
        const img = document.createElement("img");
        img.src = a.dataUrl;
        item.appendChild(img);
      }

      const nameSpan = document.createElement("span");
      nameSpan.textContent = a.name.length > 15 ? a.name.slice(0, 12) + "..." : a.name;
      item.appendChild(nameSpan);

      const removeBtn = document.createElement("span");
      removeBtn.className = "zeo-attachment-remove";
      removeBtn.textContent = "\u00d7";
      removeBtn.addEventListener("click", () => {
        attachments.splice(i, 1);
        renderAttachments();
      });
      item.appendChild(removeBtn);

      attachPreview.appendChild(item);
    });
  }

  function clearAttachments() {
    attachments = [];
    renderAttachments();
  }

  // ---------- Screenshot ----------
  screenshotBtn.addEventListener("click", () => {
    screenshotBtn.classList.add("capturing");
    chrome.runtime.sendMessage(
      {
        type: "capture_and_analyze",
        question: inputEl.value.trim() || "What is on this page?",
        userId,
        language,
        url: window.location.href,
        action: "analyze_screen",
      },
      (response) => {
        screenshotBtn.classList.remove("capturing");
        if (response && response.status === "ok" && response.data) {
          addMessage("user", "[Screenshot captured]");
          addMessage("assistant", response.data.explanation || "Analysis complete.");
        } else {
          addMessage("system", "Screenshot capture failed: " + (response?.error || "Unknown"));
        }
      }
    );
  });

  capturePageBtn.addEventListener("click", () => {
    // Same as screenshot button
    screenshotBtn.click();
  });
})();
