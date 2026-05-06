// --- UTILITIES ---
const $ = (selector) => document.querySelector(selector);

// --- THEME ---
const THEME_KEY = "roc-theme";
const themeToggle = $("#theme-toggle");

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  if (themeToggle) {
    const label = `Switch to ${theme === "dark" ? "light" : "dark"} mode`;
    themeToggle.setAttribute("aria-label", label);
    themeToggle.title = label;
  }
}

const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches;
applyTheme(localStorage.getItem(THEME_KEY) || (prefersDark ? "dark" : "light"));

themeToggle?.addEventListener("click", () => {
  const next =
    document.documentElement.getAttribute("data-theme") === "dark"
      ? "light"
      : "dark";
  applyTheme(next);
  localStorage.setItem(THEME_KEY, next);
});

// --- DOM ELEMENTS ---
const els = {
  connectForm: $("#connect-form"),
  messageForm: $("#message-form"),
  username: $("#username"),
  message: $("#message"),
  connectBtn: $("#connect-button"),
  disconnectBtn: $("#disconnect-button"),
  sendBtn: $("#send-button"),
  messages: $("#messages"),
  status: $("#connection-status"),
};

// --- CHAT STATE ---
let socket = null;
let activeUsername = "";

function setConnectionState(state) {
  const isConn = state === "connected";
  const isBusy = ["connecting", "disconnecting"].includes(state);

  // Control buttons and inputs
  els.username.disabled = els.connectBtn.disabled = isConn || isBusy;
  els.disconnectBtn.disabled = ["disconnected", "disconnecting"].includes(
    state,
  );
  els.message.disabled = els.sendBtn.disabled = !isConn;

  // Status lookup to avoid multiple if/else checks
  const statusMap = {
    connecting: { class: "connecting", text: "Connecting..." },
    disconnecting: { class: "connecting", text: "Disconnecting..." },
    connected: { class: "on", text: `Connected as ${activeUsername}` },
    disconnected: { class: "off", text: "Disconnected" },
  };

  const current = statusMap[state];
  els.status.innerHTML = `<span class="status-dot" data-state="${current.class}"></span>${current.text}`;
}

function addMessage({
  type = "message",
  username = "Anonymous",
  content = "",
  timestamp,
}) {
  els.messages.querySelector(".empty-state")?.remove();

  const isSelf = type === "message" && username === activeUsername;
  const article = document.createElement("article");
  article.className = `message ${type} ${isSelf ? "self" : ""}`.trim();

  if (type === "message" && !isSelf) {
    const author = document.createElement("strong");
    author.textContent = username;
    article.append(author);
  }

  const text = document.createElement("div");
  text.textContent = content;
  article.append(text);

  if (timestamp) {
    const time = document.createElement("time");
    time.dateTime = timestamp;
    time.textContent = new Date(timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    article.append(time);
  }

  els.messages.append(article);
  els.messages.scrollTop = els.messages.scrollHeight;
}

// --- WEBSOCKET CONNECTION ---
function connect(username) {
  if (
    socket?.readyState === WebSocket.CONNECTING ||
    socket?.readyState === WebSocket.OPEN
  )
    return;

  activeUsername = username;
  setConnectionState("connecting");

  const protocol = location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(
    `${protocol}://${location.host}/ws/${encodeURIComponent(username)}`,
  );

  // Use WebSocket .onX handlers for cleaner code
  socket.onopen = () => {
    setConnectionState("connected");
    els.message.focus();
  };

  socket.onmessage = (event) => {
    try {
      addMessage(JSON.parse(event.data));
    } catch {
      addMessage({
        type: "error",
        content: "Invalid message received from server",
      });
    }
  };

  socket.onclose = () => {
    socket = null;
    activeUsername = "";
    setConnectionState("disconnected");
    addMessage({ type: "system", content: "Disconnected" });
  };

  socket.onerror = () =>
    addMessage({ type: "error", content: "WebSocket connection error" });
}

function disconnect() {
  if (
    !socket ||
    [WebSocket.CLOSED, WebSocket.CLOSING].includes(socket.readyState)
  )
    return;

  setConnectionState("disconnecting");
  try {
    socket.close(1000, "client disconnect");
  } catch {
    socket.onclose(); // Force UI cleanup if close fails
    addMessage({ type: "error", content: "Could not close cleanly" });
  }
}

// --- EVENT LISTENERS ---
els.connectForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const user = els.username.value.trim();
  if (user) connect(user);
});

els.disconnectBtn.addEventListener("click", disconnect);

els.messageForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const content = els.message.value.trim();
  if (content && socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ content }));
    els.message.value = "";
    els.message.focus();
  }
});
