/* ==========================================================
   MIET AI Assistant — script.js (vanilla JavaScript)
   Talks to the FastAPI backend at /api/chat.
   ========================================================== */

const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const input = document.getElementById("question-input");
const sendBtn = document.getElementById("send-btn");
const clearBtn = document.getElementById("clear-btn");
const suggestionsBox = document.getElementById("suggestions");
const statusBadge = document.getElementById("status-badge");

const WELCOME =
  "👋 Hi! I'm the <strong>MIET AI Assistant</strong>. Ask me anything: " +
  "coding, studies, career advice, general knowledge, or questions about " +
  "MIET Jammu (admissions, placements, facilities). For MIET facts I use " +
  "official website content and show my sources.";

/* conversation memory sent with every request so follow-ups make sense */
let history = [];

/* ---------- helpers ---------- */

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

/* tiny markdown: **bold** and _italic_ only (bot text is trusted-ish but
   we escape first, then re-apply the two patterns) */
function renderText(str) {
  const parts = String(str).split(/```[a-zA-Z0-9]*\n?/);
  return parts
    .map((part, i) => {
      const safe = escapeHtml(part);
      if (i % 2 === 1) {
        return "<pre><code>" + safe.replace(/\n$/, "") + "</code></pre>";
      }
      return safe
        .replace(/`([^`\n]+)`/g, "<code>$1</code>")
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/^- (.+)$/gm, "&bull; $1")
        .replace(/\n/g, "<br>");
    })
    .join("");
}

function addMessage(role, html, sources, mode) {
  const msg = document.createElement("div");
  msg.className = `msg ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "bot" ? "🎓" : "🧑";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = html;

  if (sources && sources.length) {
    const box = document.createElement("div");
    box.className = "sources";
    sources.forEach((s) => {
      const a = document.createElement("a");
      a.href = s.url;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = "🔗 " + s.title;
      box.appendChild(a);
    });
    bubble.appendChild(box);
  }

  if (mode) {
    const tag = document.createElement("div");
    tag.className = "mode-tag";
    const labels = {
      llm: "AI answer",
      local: "Limited mode: no AI key configured (website search only)",
      local_fallback: "Limited mode: AI service unavailable right now",
    };
    if (labels[mode]) {
      tag.textContent = labels[mode];
      bubble.appendChild(tag);
    }
  }

  msg.appendChild(avatar);
  msg.appendChild(bubble);
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return msg;
}

function addTyping() {
  const msg = addMessage(
    "bot",
    '<div class="typing"><span></span><span></span><span></span></div>'
  );
  msg.id = "typing-indicator";
  return msg;
}

function removeTyping() {
  const t = document.getElementById("typing-indicator");
  if (t) t.remove();
}

/* ---------- API calls ---------- */

async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (data.llm_configured) {
      statusBadge.className = "badge badge-ok";
      statusBadge.textContent = `● Online · ${data.model} · AI enabled`;
    } else {
      statusBadge.className = "badge badge-off";
      statusBadge.textContent = "● Limited mode · API key missing";
    }
  } catch {
    statusBadge.className = "badge badge-off";
    statusBadge.textContent = "● Server unreachable";
  }
}

async function loadSuggestions() {
  try {
    const res = await fetch("/api/suggestions");
    const data = await res.json();
    suggestionsBox.innerHTML = "";
    data.questions.forEach((q) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "chip";
      chip.textContent = q;
      chip.addEventListener("click", () => {
        input.value = q;
        chatForm.requestSubmit();
      });
      suggestionsBox.appendChild(chip);
    });
  } catch {
    /* suggestions are optional */
  }
}

async function askQuestion(question) {
  addMessage("user", renderText(question));
  input.value = "";
  sendBtn.disabled = true;
  addTyping();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, history: history.slice(-10) }),
    });
    removeTyping();

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      addMessage(
        "bot",
        renderText(
          err.detail ||
            "⚠️ The server returned an error. Please try again in a moment."
        )
      );
      return;
    }

    const data = await res.json();
    addMessage("bot", renderText(data.answer), data.sources, data.mode);
    history.push({ role: "user", content: question });
    history.push({ role: "assistant", content: data.answer });
    history = history.slice(-20);
  } catch {
    removeTyping();
    addMessage(
      "bot",
      "⚠️ I couldn't reach the chatbot server. Make sure FastAPI is running " +
        "(<strong>uvicorn app:app --reload</strong>) and refresh the page."
    );
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

/* ---------- events ---------- */

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if (q) askQuestion(q);
});

clearBtn.addEventListener("click", () => {
  chatWindow.innerHTML = "";
  history = [];
  addMessage("bot", WELCOME);
  input.focus();
});

/* ---------- init ---------- */
addMessage("bot", WELCOME);
checkHealth();
loadSuggestions();
input.focus();
